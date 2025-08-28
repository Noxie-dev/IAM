"""
Storage Service
Phase 2: Backend Enhancement

S3/Wasabi storage service for audio files and transcription data
"""

import os
import logging
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional, BinaryIO
from io import BytesIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class StorageService:
    """
    S3/Wasabi storage service for file management
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = None
        self.bucket_name = self.settings.S3_BUCKET_NAME
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.settings.S3_ENDPOINT_URL,
                aws_access_key_id=self.settings.S3_ACCESS_KEY,
                aws_secret_access_key=self.settings.S3_SECRET_KEY,
                region_name=getattr(self.settings, 'S3_REGION', 'us-east-1')
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Storage service initialized with bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("S3 credentials not configured")
            self.s3_client = None
        except ClientError as e:
            logger.error(f"S3 connection failed: {e}")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Storage service initialization failed: {e}")
            self.s3_client = None
    
    async def upload_file(
        self,
        file_content: bytes,
        file_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3/Wasabi storage
        
        Args:
            file_content: File content as bytes
            file_key: S3 object key
            content_type: MIME content type
            metadata: Additional metadata
        
        Returns:
            Upload result dictionary
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "Storage service not configured"
            }
        
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
            
            # Create file-like object from bytes
            file_obj = BytesIO(file_content)
            
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
            file_url = f"{self.settings.S3_ENDPOINT_URL}/{self.bucket_name}/{file_key}"
            
            logger.info(f"File uploaded successfully: {file_key}")
            
            return {
                'success': True,
                'file_key': file_key,
                'file_url': file_url,
                'file_size': len(file_content),
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
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}",
                'file_key': file_key
            }
    
    def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600,
        method: str = 'GET'
    ) -> Optional[str]:
        """
        Generate presigned URL for file access
        
        Args:
            file_key: S3 object key
            expiration: URL expiration in seconds
            method: HTTP method (GET, PUT, etc.)
        
        Returns:
            Presigned URL or None if failed
        """
        if not self.s3_client:
            return None
        
        try:
            if method == 'GET':
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_key},
                    ExpiresIn=expiration
                )
            elif method == 'PUT':
                url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_key},
                    ExpiresIn=expiration
                )
            else:
                logger.error(f"Unsupported method for presigned URL: {method}")
                return None
            
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, file_key: str) -> Dict[str, Any]:
        """
        Delete file from storage
        
        Args:
            file_key: S3 object key
        
        Returns:
            Deletion result dictionary
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "Storage service not configured"
            }
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted successfully: {file_key}")
            
            return {
                'success': True,
                'file_key': file_key
            }
            
        except ClientError as e:
            logger.error(f"File deletion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_key': file_key
            }
    
    def file_exists(self, file_key: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            file_key: S3 object key
        
        Returns:
            True if file exists, False otherwise
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False
    
    def get_file_metadata(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from storage
        
        Args:
            file_key: S3 object key
        
        Returns:
            File metadata dictionary or None if not found
        """
        if not self.s3_client:
            return None
        
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            
            return {
                'file_key': file_key,
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> Dict[str, Any]:
        """
        List files in storage with optional prefix filter
        
        Args:
            prefix: Key prefix to filter by
            max_keys: Maximum number of keys to return
        
        Returns:
            List of files with metadata
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "Storage service not configured"
            }
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return {
                'success': True,
                'files': files,
                'count': len(files),
                'truncated': response.get('IsTruncated', False)
            }
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics
        
        Returns:
            Storage statistics dictionary
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "Storage service not configured"
            }
        
        try:
            # List all objects to calculate stats
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            total_size = 0
            file_count = 0
            
            for obj in response.get('Contents', []):
                total_size += obj['Size']
                file_count += 1
            
            return {
                'success': True,
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name
            }
            
        except ClientError as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
