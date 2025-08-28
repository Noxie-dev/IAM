#!/usr/bin/env python3
"""
S3-Compatible Storage Configuration (Wasabi)
Phase 1: Infrastructure - File Storage Setup

This module provides S3-compatible storage functionality using Wasabi for cost-effective file storage.
"""

import boto3
import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class S3StorageManager:
    """
    S3-compatible storage manager for Wasabi cloud storage
    Provides secure file upload, download, and management capabilities
    """
    
    def __init__(self, 
                 endpoint_url: str = None,
                 access_key: str = None,
                 secret_key: str = None,
                 bucket_name: str = None,
                 region: str = 'us-east-1'):
        """
        Initialize S3 storage manager
        
        Args:
            endpoint_url: S3-compatible endpoint (e.g., Wasabi endpoint)
            access_key: Access key ID
            secret_key: Secret access key
            bucket_name: S3 bucket name
            region: AWS region (default for Wasabi)
        """
        
        # Load from environment if not provided
        self.endpoint_url = endpoint_url or os.getenv('S3_ENDPOINT_URL', 'https://s3.wasabisys.com')
        self.access_key = access_key or os.getenv('S3_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('S3_SECRET_KEY')
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME', 'iam-transcription-files')
        self.region = region or os.getenv('S3_REGION', 'us-east-1')
        
        # Validate configuration
        if not all([self.access_key, self.secret_key, self.bucket_name]):
            raise ValueError("S3 credentials and bucket name are required")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        
        # Test connection and create bucket if needed
        self._initialize_bucket()
    
    def _initialize_bucket(self):
        """Initialize S3 bucket with proper configuration"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' is accessible")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                # Bucket doesn't exist, create it
                logger.info(f"Creating S3 bucket: {self.bucket_name}")
                self._create_bucket()
            else:
                logger.error(f"S3 bucket access error: {e}")
                raise
        
        except NoCredentialsError:
            logger.error("S3 credentials not found or invalid")
            raise
    
    def _create_bucket(self):
        """Create S3 bucket with proper configuration"""
        try:
            # Create bucket
            if self.region == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Set bucket CORS configuration for web uploads
            cors_configuration = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                        'AllowedOrigins': ['*'],  # Restrict this in production
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_configuration
            )
            
            # Set bucket lifecycle policy for cost optimization
            lifecycle_configuration = {
                'Rules': [
                    {
                        'ID': 'DeleteIncompleteMultipartUploads',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': ''},
                        'AbortIncompleteMultipartUpload': {
                            'DaysAfterInitiation': 1
                        }
                    },
                    {
                        'ID': 'TransitionToIA',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'audio/'},
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            }
                        ]
                    }
                ]
            }
            
            try:
                self.s3_client.put_bucket_lifecycle_configuration(
                    Bucket=self.bucket_name,
                    LifecycleConfiguration=lifecycle_configuration
                )
            except ClientError as e:
                # Some S3-compatible services don't support lifecycle policies
                logger.warning(f"Could not set lifecycle policy: {e}")
            
            logger.info(f"S3 bucket '{self.bucket_name}' created successfully")
            
        except ClientError as e:
            logger.error(f"Failed to create S3 bucket: {e}")
            raise
    
    def upload_file(self, 
                   file_obj: BinaryIO, 
                   file_key: str,
                   content_type: str = None,
                   metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload file to S3 storage
        
        Args:
            file_obj: File object to upload
            file_key: S3 object key (file path in bucket)
            content_type: MIME type of the file
            metadata: Additional metadata to store with file
            
        Returns:
            Dict containing upload result information
        """
        
        try:
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_key)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare metadata
            upload_metadata = metadata or {}
            upload_metadata.update({
                'uploaded_at': datetime.utcnow().isoformat(),
                'original_filename': os.path.basename(file_key)
            })
            
            # Upload file
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': upload_metadata,
                    'ServerSideEncryption': 'AES256'  # Enable encryption at rest
                }
            )
            
            # Get file URL
            file_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
            
            # Get file size
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            
            logger.info(f"File uploaded successfully: {file_key}")
            
            return {
                'success': True,
                'file_key': file_key,
                'file_url': file_url,
                'file_size': file_size,
                'content_type': content_type,
                'metadata': upload_metadata
            }
            
        except ClientError as e:
            logger.error(f"File upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_key': file_key
            }
    
    def generate_presigned_url(self, 
                              file_key: str, 
                              expiration: int = 3600,
                              http_method: str = 'GET') -> Optional[str]:
        """
        Generate presigned URL for secure file access
        
        Args:
            file_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method (GET, PUT, POST)
            
        Returns:
            Presigned URL string or None if failed
        """
        
        try:
            method_mapping = {
                'GET': 'get_object',
                'PUT': 'put_object',
                'POST': 'post_object'
            }
            
            presigned_url = self.s3_client.generate_presigned_url(
                method_mapping.get(http_method, 'get_object'),
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3 storage
        
        Args:
            file_key: S3 object key to delete
            
        Returns:
            True if successful, False otherwise
        """
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted successfully: {file_key}")
            return True
            
        except ClientError as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from S3
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dict containing file information or None if not found
        """
        
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            
            return {
                'file_key': file_key,
                'file_size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"File not found: {file_key}")
            else:
                logger.error(f"Failed to get file info: {e}")
            return None
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> list[Dict[str, Any]]:
        """
        List files in S3 bucket
        
        Args:
            prefix: Filter files by prefix
            max_keys: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'file_key': obj['Key'],
                    'file_size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []

class AudioFileManager:
    """
    Specialized file manager for audio files with transcription-specific features
    """
    
    def __init__(self, storage_manager: S3StorageManager):
        self.storage = storage_manager
        self.audio_formats = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.mp4': 'video/mp4',
            '.mpeg': 'audio/mpeg',
            '.mpga': 'audio/mpeg',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm',
            '.flac': 'audio/flac'
        }
    
    def upload_audio_file(self, 
                         file_obj: BinaryIO,
                         user_id: str,
                         meeting_id: str,
                         original_filename: str) -> Dict[str, Any]:
        """
        Upload audio file with proper organization and metadata
        
        Args:
            file_obj: Audio file object
            user_id: User UUID
            meeting_id: Meeting UUID
            original_filename: Original filename
            
        Returns:
            Upload result dictionary
        """
        
        # Generate organized file key
        file_extension = os.path.splitext(original_filename)[1].lower()
        timestamp = datetime.utcnow().strftime('%Y/%m/%d')
        file_key = f"audio/{user_id}/{timestamp}/{meeting_id}{file_extension}"
        
        # Validate audio format
        if file_extension not in self.audio_formats:
            return {
                'success': False,
                'error': f'Unsupported audio format: {file_extension}',
                'supported_formats': list(self.audio_formats.keys())
            }
        
        # Prepare metadata
        metadata = {
            'user_id': user_id,
            'meeting_id': meeting_id,
            'original_filename': original_filename,
            'file_type': 'audio',
            'format': file_extension[1:]  # Remove the dot
        }
        
        # Upload file
        result = self.storage.upload_file(
            file_obj=file_obj,
            file_key=file_key,
            content_type=self.audio_formats[file_extension],
            metadata=metadata
        )
        
        return result
    
    def get_audio_download_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Get secure download URL for audio file
        
        Args:
            file_key: S3 object key
            expiration: URL expiration in seconds
            
        Returns:
            Presigned download URL
        """
        return self.storage.generate_presigned_url(file_key, expiration, 'GET')

# Configuration and initialization
def create_storage_manager() -> S3StorageManager:
    """Create and configure S3 storage manager"""
    
    # Wasabi configuration
    config = {
        'endpoint_url': os.getenv('S3_ENDPOINT_URL', 'https://s3.wasabisys.com'),
        'access_key': os.getenv('S3_ACCESS_KEY'),
        'secret_key': os.getenv('S3_SECRET_KEY'),
        'bucket_name': os.getenv('S3_BUCKET_NAME', 'iam-transcription-files'),
        'region': os.getenv('S3_REGION', 'us-east-1')
    }
    
    return S3StorageManager(**config)

def create_audio_manager() -> AudioFileManager:
    """Create audio file manager with S3 storage"""
    storage_manager = create_storage_manager()
    return AudioFileManager(storage_manager)

# Example usage and testing
if __name__ == "__main__":
    # Test S3 storage setup
    try:
        storage = create_storage_manager()
        audio_manager = create_audio_manager()
        
        print("✅ S3 storage configuration successful")
        print(f"📦 Bucket: {storage.bucket_name}")
        print(f"🌐 Endpoint: {storage.endpoint_url}")
        
        # List existing files
        files = storage.list_files(max_keys=10)
        print(f"📁 Found {len(files)} files in bucket")
        
    except Exception as e:
        print(f"❌ S3 storage configuration failed: {e}")
        print("Please check your environment variables:")
        print("- S3_ACCESS_KEY")
        print("- S3_SECRET_KEY") 
        print("- S3_BUCKET_NAME (optional)")
        print("- S3_ENDPOINT_URL (optional)")
