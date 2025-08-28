"""
Unit Tests for Storage Service
Phase 2: Backend Enhancement

Tests for S3/Wasabi storage service
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime

from app.services.storage_service import StorageService


class TestStorageService:
    """Test suite for StorageService"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for storage service"""
        settings = Mock()
        settings.S3_ENDPOINT_URL = "https://s3.wasabisys.com"
        settings.S3_ACCESS_KEY = "test-access-key"
        settings.S3_SECRET_KEY = "test-secret-key"
        settings.S3_BUCKET_NAME = "test-bucket"
        settings.S3_REGION = "us-east-1"
        return settings
    
    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client"""
        client = Mock()
        client.head_bucket.return_value = {}  # Successful bucket access
        return client
    
    @pytest.fixture
    def storage_service(self, mock_settings, mock_s3_client):
        """Create StorageService with mocked dependencies"""
        with patch('app.services.storage_service.get_settings', return_value=mock_settings):
            with patch('app.services.storage_service.boto3.client', return_value=mock_s3_client):
                service = StorageService()
                service.s3_client = mock_s3_client
                return service
    
    def test_service_initialization_success(self, mock_settings, mock_s3_client):
        """Test successful service initialization"""
        with patch('app.services.storage_service.get_settings', return_value=mock_settings):
            with patch('app.services.storage_service.boto3.client', return_value=mock_s3_client):
                service = StorageService()
                
                assert service.s3_client is not None
                assert service.bucket_name == "test-bucket"
    
    def test_service_initialization_no_credentials(self, mock_settings):
        """Test service initialization with no credentials"""
        with patch('app.services.storage_service.get_settings', return_value=mock_settings):
            with patch('app.services.storage_service.boto3.client', side_effect=NoCredentialsError()):
                service = StorageService()
                
                assert service.s3_client is None
    
    def test_service_initialization_client_error(self, mock_settings):
        """Test service initialization with client error"""
        with patch('app.services.storage_service.get_settings', return_value=mock_settings):
            with patch('app.services.storage_service.boto3.client') as mock_boto:
                mock_client = Mock()
                mock_client.head_bucket.side_effect = ClientError(
                    {'Error': {'Code': 'NoSuchBucket'}}, 'HeadBucket'
                )
                mock_boto.return_value = mock_client
                
                service = StorageService()
                
                assert service.s3_client is None
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_service):
        """Test successful file upload"""
        file_content = b"test file content"
        file_key = "test/file.txt"
        
        # Mock successful upload
        storage_service.s3_client.upload_fileobj.return_value = None
        
        result = await storage_service.upload_file(
            file_content=file_content,
            file_key=file_key,
            content_type="text/plain",
            metadata={"test": "metadata"}
        )
        
        assert result['success'] is True
        assert result['file_key'] == file_key
        assert result['file_size'] == len(file_content)
        assert result['content_type'] == "text/plain"
        assert 'file_url' in result
        assert 'metadata' in result
        
        # Verify upload was called correctly
        storage_service.s3_client.upload_fileobj.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_auto_detect_content_type(self, storage_service):
        """Test file upload with auto-detected content type"""
        file_content = b"test content"
        file_key = "test/audio.wav"
        
        storage_service.s3_client.upload_fileobj.return_value = None
        
        result = await storage_service.upload_file(
            file_content=file_content,
            file_key=file_key
        )
        
        assert result['success'] is True
        # Should auto-detect WAV content type
        assert result['content_type'] in ['audio/wav', 'audio/x-wav', 'application/octet-stream']
    
    @pytest.mark.asyncio
    async def test_upload_file_client_error(self, storage_service):
        """Test file upload with S3 client error"""
        file_content = b"test content"
        file_key = "test/file.txt"
        
        # Mock client error
        storage_service.s3_client.upload_fileobj.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}, 'PutObject'
        )
        
        result = await storage_service.upload_file(
            file_content=file_content,
            file_key=file_key
        )
        
        assert result['success'] is False
        assert 'Access denied' in result['error']
        assert result['file_key'] == file_key
    
    @pytest.mark.asyncio
    async def test_upload_file_no_client(self):
        """Test file upload without configured client"""
        service = StorageService()
        service.s3_client = None
        
        result = await service.upload_file(
            file_content=b"test",
            file_key="test.txt"
        )
        
        assert result['success'] is False
        assert "not configured" in result['error']
    
    def test_generate_presigned_url_get(self, storage_service):
        """Test generating presigned URL for GET"""
        file_key = "test/file.txt"
        expected_url = "https://presigned-url.com"
        
        storage_service.s3_client.generate_presigned_url.return_value = expected_url
        
        url = storage_service.generate_presigned_url(file_key, expiration=3600, method='GET')
        
        assert url == expected_url
        storage_service.s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': file_key},
            ExpiresIn=3600
        )
    
    def test_generate_presigned_url_put(self, storage_service):
        """Test generating presigned URL for PUT"""
        file_key = "test/file.txt"
        expected_url = "https://presigned-upload-url.com"
        
        storage_service.s3_client.generate_presigned_url.return_value = expected_url
        
        url = storage_service.generate_presigned_url(file_key, expiration=1800, method='PUT')
        
        assert url == expected_url
        storage_service.s3_client.generate_presigned_url.assert_called_once_with(
            'put_object',
            Params={'Bucket': 'test-bucket', 'Key': file_key},
            ExpiresIn=1800
        )
    
    def test_generate_presigned_url_unsupported_method(self, storage_service):
        """Test generating presigned URL with unsupported method"""
        url = storage_service.generate_presigned_url("test.txt", method='DELETE')
        
        assert url is None
    
    def test_generate_presigned_url_client_error(self, storage_service):
        """Test generating presigned URL with client error"""
        storage_service.s3_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        url = storage_service.generate_presigned_url("nonexistent.txt")
        
        assert url is None
    
    def test_generate_presigned_url_no_client(self):
        """Test generating presigned URL without client"""
        service = StorageService()
        service.s3_client = None
        
        url = service.generate_presigned_url("test.txt")
        
        assert url is None
    
    def test_delete_file_success(self, storage_service):
        """Test successful file deletion"""
        file_key = "test/file.txt"
        
        storage_service.s3_client.delete_object.return_value = {}
        
        result = storage_service.delete_file(file_key)
        
        assert result['success'] is True
        assert result['file_key'] == file_key
        storage_service.s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket', Key=file_key
        )
    
    def test_delete_file_client_error(self, storage_service):
        """Test file deletion with client error"""
        file_key = "test/file.txt"
        
        storage_service.s3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'DeleteObject'
        )
        
        result = storage_service.delete_file(file_key)
        
        assert result['success'] is False
        assert result['file_key'] == file_key
    
    def test_file_exists_true(self, storage_service):
        """Test file exists check - file exists"""
        file_key = "test/existing-file.txt"
        
        storage_service.s3_client.head_object.return_value = {}
        
        exists = storage_service.file_exists(file_key)
        
        assert exists is True
        storage_service.s3_client.head_object.assert_called_once_with(
            Bucket='test-bucket', Key=file_key
        )
    
    def test_file_exists_false(self, storage_service):
        """Test file exists check - file doesn't exist"""
        file_key = "test/nonexistent-file.txt"
        
        storage_service.s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'HeadObject'
        )
        
        exists = storage_service.file_exists(file_key)
        
        assert exists is False
    
    def test_file_exists_no_client(self):
        """Test file exists check without client"""
        service = StorageService()
        service.s3_client = None
        
        exists = service.file_exists("test.txt")
        
        assert exists is False
    
    def test_get_file_metadata_success(self, storage_service):
        """Test getting file metadata successfully"""
        file_key = "test/file.txt"
        mock_response = {
            'ContentLength': 1024,
            'ContentType': 'text/plain',
            'LastModified': datetime(2023, 1, 1),
            'ETag': '"abc123"',
            'Metadata': {'custom': 'value'}
        }
        
        storage_service.s3_client.head_object.return_value = mock_response
        
        metadata = storage_service.get_file_metadata(file_key)
        
        assert metadata is not None
        assert metadata['file_key'] == file_key
        assert metadata['size'] == 1024
        assert metadata['content_type'] == 'text/plain'
        assert metadata['metadata']['custom'] == 'value'
    
    def test_get_file_metadata_not_found(self, storage_service):
        """Test getting metadata for non-existent file"""
        file_key = "test/nonexistent.txt"
        
        storage_service.s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'HeadObject'
        )
        
        metadata = storage_service.get_file_metadata(file_key)
        
        assert metadata is None
    
    def test_list_files_success(self, storage_service):
        """Test listing files successfully"""
        mock_response = {
            'Contents': [
                {
                    'Key': 'test/file1.txt',
                    'Size': 100,
                    'LastModified': datetime(2023, 1, 1),
                    'ETag': '"abc123"'
                },
                {
                    'Key': 'test/file2.txt',
                    'Size': 200,
                    'LastModified': datetime(2023, 1, 2),
                    'ETag': '"def456"'
                }
            ],
            'IsTruncated': False
        }
        
        storage_service.s3_client.list_objects_v2.return_value = mock_response
        
        result = storage_service.list_files(prefix="test/", max_keys=100)
        
        assert result['success'] is True
        assert result['count'] == 2
        assert result['truncated'] is False
        assert len(result['files']) == 2
        assert result['files'][0]['key'] == 'test/file1.txt'
        assert result['files'][0]['size'] == 100
    
    def test_list_files_empty(self, storage_service):
        """Test listing files with empty result"""
        mock_response = {
            'Contents': [],
            'IsTruncated': False
        }
        
        storage_service.s3_client.list_objects_v2.return_value = mock_response
        
        result = storage_service.list_files()
        
        assert result['success'] is True
        assert result['count'] == 0
        assert len(result['files']) == 0
    
    def test_list_files_client_error(self, storage_service):
        """Test listing files with client error"""
        storage_service.s3_client.list_objects_v2.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'ListObjectsV2'
        )
        
        result = storage_service.list_files()
        
        assert result['success'] is False
        assert 'AccessDenied' in result['error']
    
    def test_get_storage_stats_success(self, storage_service):
        """Test getting storage statistics successfully"""
        mock_response = {
            'Contents': [
                {'Key': 'file1.txt', 'Size': 1000},
                {'Key': 'file2.txt', 'Size': 2000},
                {'Key': 'file3.txt', 'Size': 500}
            ]
        }
        
        storage_service.s3_client.list_objects_v2.return_value = mock_response
        
        stats = storage_service.get_storage_stats()
        
        assert stats['success'] is True
        assert stats['total_files'] == 3
        assert stats['total_size_bytes'] == 3500
        assert stats['total_size_mb'] == 3.5
        assert stats['bucket_name'] == 'test-bucket'
    
    def test_get_storage_stats_empty_bucket(self, storage_service):
        """Test getting storage statistics for empty bucket"""
        mock_response = {'Contents': []}
        
        storage_service.s3_client.list_objects_v2.return_value = mock_response
        
        stats = storage_service.get_storage_stats()
        
        assert stats['success'] is True
        assert stats['total_files'] == 0
        assert stats['total_size_bytes'] == 0
        assert stats['total_size_mb'] == 0.0
    
    def test_get_storage_stats_client_error(self, storage_service):
        """Test getting storage statistics with client error"""
        storage_service.s3_client.list_objects_v2.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'ListObjectsV2'
        )
        
        stats = storage_service.get_storage_stats()
        
        assert stats['success'] is False
        assert 'AccessDenied' in stats['error']


class TestStorageServiceIntegration:
    """Integration tests for storage service"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not all([
            os.getenv('S3_ACCESS_KEY'),
            os.getenv('S3_SECRET_KEY'),
            os.getenv('S3_BUCKET_NAME')
        ]),
        reason="S3 credentials not available"
    )
    async def test_real_s3_operations(self):
        """Integration test with real S3/Wasabi (requires credentials)"""
        service = StorageService()
        
        if service.s3_client is None:
            pytest.skip("S3 client not configured")
        
        test_content = b"Integration test content"
        test_key = f"test/integration-{datetime.now().isoformat()}.txt"
        
        try:
            # Test upload
            upload_result = await service.upload_file(
                file_content=test_content,
                file_key=test_key,
                content_type="text/plain"
            )
            
            assert upload_result['success'] is True
            
            # Test file exists
            exists = service.file_exists(test_key)
            assert exists is True
            
            # Test get metadata
            metadata = service.get_file_metadata(test_key)
            assert metadata is not None
            assert metadata['size'] == len(test_content)
            
            # Test generate presigned URL
            url = service.generate_presigned_url(test_key)
            assert url is not None
            assert test_key in url
            
        finally:
            # Cleanup - delete test file
            service.delete_file(test_key)
    
    def test_error_handling_edge_cases(self, storage_service):
        """Test various error handling edge cases"""
        # Test with very large file key
        large_key = "a" * 1000 + ".txt"
        
        # Should handle gracefully
        exists = storage_service.file_exists(large_key)
        assert isinstance(exists, bool)
        
        # Test with special characters in key
        special_key = "test/file with spaces & symbols!@#.txt"
        
        # Should handle gracefully
        exists = storage_service.file_exists(special_key)
        assert isinstance(exists, bool)
