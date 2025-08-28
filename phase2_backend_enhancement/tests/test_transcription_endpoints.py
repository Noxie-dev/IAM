"""
Unit Tests for Transcription Endpoints
Phase 2: Backend Enhancement

Tests for the enhanced transcription upload endpoint with audio enhancement
"""

import os
import json
import tempfile
import pytest
import numpy as np
import soundfile as sf
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO

# Import the endpoint functions
from app.api.v2.endpoints.transcription import upload_audio, process_audio_file


class TestTranscriptionUploadEndpoint:
    """Test suite for transcription upload endpoint"""
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock authenticated user"""
        user = Mock()
        user.id = "test-user-123"
        return user
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create sample audio file for testing"""
        # Generate 1 second of test audio
        duration = 1.0
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration), False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Create file-like object
        audio_bytes = BytesIO()
        sf.write(audio_bytes, audio, sr, format='WAV')
        audio_bytes.seek(0)
        
        # Create UploadFile
        upload_file = UploadFile(
            filename="test_audio.wav",
            file=audio_bytes,
            content_type="audio/wav"
        )
        
        return upload_file
    
    @pytest.fixture
    def valid_form_data(self):
        """Valid form data for upload"""
        return {
            "title": "Test Meeting",
            "description": "Test description",
            "language": "en",
            "provider": "openai",
            "model": "whisper-1",
            "speaker_detection": False,
            "timestamps": True,
            "word_timestamps": False,
            "enhance_audio": True,
            "enhancement_options": json.dumps({
                "noise_reduction": True,
                "vad_attenuation_db": 12,
                "high_pass_freq": 80,
                "lufs_target": -23,
                "speaker_boost_db": 3
            })
        }
    
    @pytest.mark.asyncio
    async def test_upload_audio_success(self, sample_audio_file, valid_form_data, mock_current_user, mock_db_session):
        """Test successful audio upload with enhancement"""
        with patch('app.api.v2.endpoints.transcription.Meeting') as mock_meeting_class:
            with patch('app.api.v2.endpoints.transcription.websocket_manager') as mock_ws:
                # Mock meeting creation
                mock_meeting = Mock()
                mock_meeting.id = "meeting-123"
                mock_meeting.created_at.isoformat.return_value = "2023-01-01T00:00:00"
                mock_meeting_class.return_value = mock_meeting
                
                # Mock WebSocket manager
                mock_ws.send_transcription_update = AsyncMock()
                
                # Call endpoint
                result = await upload_audio(
                    background_tasks=Mock(),
                    file=sample_audio_file,
                    current_user=mock_current_user,
                    db=mock_db_session,
                    **valid_form_data
                )
                
                # Verify response
                assert result["success"] is True
                assert result["id"] == "meeting-123"
                assert result["title"] == "Test Meeting"
                assert result["processing_status"] == "processing"
                
                # Verify database operations
                mock_db_session.add.assert_called_once()
                mock_db_session.commit.assert_called_once()
                
                # Verify WebSocket notification
                mock_ws.send_transcription_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_audio_no_file(self, valid_form_data, mock_current_user, mock_db_session):
        """Test upload with no file provided"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                background_tasks=Mock(),
                file=Mock(filename=None),  # No filename
                current_user=mock_current_user,
                db=mock_db_session,
                **valid_form_data
            )
        
        assert exc_info.value.status_code == 400
        assert "No file provided" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_audio_file_too_large(self, valid_form_data, mock_current_user, mock_db_session):
        """Test upload with file too large"""
        from fastapi import HTTPException
        
        # Create mock file that's too large
        large_file = Mock()
        large_file.filename = "large_file.wav"
        large_file.read = AsyncMock(return_value=b"x" * (251 * 1024 * 1024))  # 251MB
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                background_tasks=Mock(),
                file=large_file,
                current_user=mock_current_user,
                db=mock_db_session,
                **valid_form_data
            )
        
        assert exc_info.value.status_code == 400
        assert "exceeds 250MB limit" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_audio_empty_file(self, valid_form_data, mock_current_user, mock_db_session):
        """Test upload with empty file"""
        from fastapi import HTTPException
        
        empty_file = Mock()
        empty_file.filename = "empty.wav"
        empty_file.read = AsyncMock(return_value=b"")  # Empty file
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                background_tasks=Mock(),
                file=empty_file,
                current_user=mock_current_user,
                db=mock_db_session,
                **valid_form_data
            )
        
        assert exc_info.value.status_code == 400
        assert "Empty file provided" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_audio_unsupported_format(self, valid_form_data, mock_current_user, mock_db_session):
        """Test upload with unsupported file format"""
        from fastapi import HTTPException
        
        unsupported_file = Mock()
        unsupported_file.filename = "document.pdf"
        unsupported_file.read = AsyncMock(return_value=b"PDF content")
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                background_tasks=Mock(),
                file=unsupported_file,
                current_user=mock_current_user,
                db=mock_db_session,
                **valid_form_data
            )
        
        assert exc_info.value.status_code == 400
        assert "Unsupported file format" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_audio_without_enhancement(self, sample_audio_file, mock_current_user, mock_db_session):
        """Test upload without audio enhancement"""
        form_data = {
            "title": "Test Meeting",
            "language": "en",
            "provider": "openai",
            "model": "whisper-1",
            "enhance_audio": False,  # No enhancement
            "speaker_detection": False,
            "timestamps": True,
            "word_timestamps": False
        }
        
        with patch('app.api.v2.endpoints.transcription.Meeting') as mock_meeting_class:
            with patch('app.api.v2.endpoints.transcription.websocket_manager') as mock_ws:
                mock_meeting = Mock()
                mock_meeting.id = "meeting-123"
                mock_meeting.created_at.isoformat.return_value = "2023-01-01T00:00:00"
                mock_meeting_class.return_value = mock_meeting
                mock_ws.send_transcription_update = AsyncMock()
                
                result = await upload_audio(
                    background_tasks=Mock(),
                    file=sample_audio_file,
                    current_user=mock_current_user,
                    db=mock_db_session,
                    **form_data
                )
                
                assert result["success"] is True
                # Verify enhancement is disabled in settings
                call_args = mock_meeting_class.call_args
                transcription_settings = call_args.kwargs['transcription_settings']
                assert transcription_settings['enhance_audio'] is False


class TestProcessAudioFileTask:
    """Test suite for background audio processing task"""
    
    @pytest.fixture
    def mock_meeting(self):
        """Mock meeting object"""
        meeting = Mock()
        meeting.id = "meeting-123"
        meeting.processing_status = "uploading"
        meeting.add_metadata = Mock()
        meeting.transcription_metadata = {}
        return meeting
    
    @pytest.fixture
    def mock_db_session(self, mock_meeting):
        """Mock database session with meeting"""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_meeting
        db.commit = Mock()
        db.close = Mock()
        return db
    
    @pytest.fixture
    def sample_file_content(self):
        """Sample audio file content"""
        # Generate minimal WAV content
        duration = 0.5
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration), False)
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)
        
        audio_bytes = BytesIO()
        sf.write(audio_bytes, audio, sr, format='WAV')
        return audio_bytes.getvalue()
    
    @pytest.mark.asyncio
    async def test_process_audio_file_success_with_enhancement(self, mock_db_session, sample_file_content):
        """Test successful audio processing with enhancement"""
        with patch('app.api.v2.endpoints.transcription.get_db', return_value=iter([mock_db_session])):
            with patch('app.api.v2.endpoints.transcription.storage_service') as mock_storage:
                with patch('app.api.v2.endpoints.transcription.audio_enhancer') as mock_enhancer:
                    with patch('app.api.v2.endpoints.transcription.transcription_service') as mock_transcription:
                        with patch('app.api.v2.endpoints.transcription.websocket_manager') as mock_ws:
                            # Mock successful operations
                            mock_storage.upload_file = AsyncMock(return_value={
                                "success": True,
                                "file_url": "https://s3.example.com/original.wav"
                            })
                            
                            mock_enhancer.enhance_audio = AsyncMock(return_value="/tmp/enhanced.wav")
                            
                            mock_transcription.transcribe_audio = AsyncMock(return_value={
                                "success": True,
                                "text": "Test transcription result",
                                "segments": [{"start": 0, "end": 1, "text": "Test"}]
                            })
                            
                            mock_ws.send_transcription_update = AsyncMock()
                            
                            # Create temporary files for mocking
                            with tempfile.NamedTemporaryFile() as temp_original:
                                with tempfile.NamedTemporaryFile() as temp_enhanced:
                                    temp_enhanced.write(sample_file_content)
                                    temp_enhanced.flush()
                                    
                                    mock_enhancer.enhance_audio.return_value = temp_enhanced.name
                                    
                                    # Call the background task
                                    await process_audio_file(
                                        meeting_id="meeting-123",
                                        file_content=sample_file_content,
                                        filename="test.wav",
                                        user_id="user-123",
                                        enhance_audio=True,
                                        enhancement_options='{"noise_reduction": true}'
                                    )
                            
                            # Verify operations were called
                            mock_storage.upload_file.assert_called()
                            mock_enhancer.enhance_audio.assert_called_once()
                            mock_transcription.transcribe_audio.assert_called_once()
                            
                            # Verify WebSocket updates
                            assert mock_ws.send_transcription_update.call_count >= 3  # Multiple progress updates
    
    @pytest.mark.asyncio
    async def test_process_audio_file_enhancement_failure(self, mock_db_session, sample_file_content):
        """Test audio processing when enhancement fails"""
        with patch('app.api.v2.endpoints.transcription.get_db', return_value=iter([mock_db_session])):
            with patch('app.api.v2.endpoints.transcription.storage_service') as mock_storage:
                with patch('app.api.v2.endpoints.transcription.audio_enhancer') as mock_enhancer:
                    with patch('app.api.v2.endpoints.transcription.transcription_service') as mock_transcription:
                        with patch('app.api.v2.endpoints.transcription.websocket_manager') as mock_ws:
                            # Mock storage success
                            mock_storage.upload_file = AsyncMock(return_value={
                                "success": True,
                                "file_url": "https://s3.example.com/original.wav"
                            })
                            
                            # Mock enhancement failure
                            mock_enhancer.enhance_audio = AsyncMock(side_effect=Exception("Enhancement failed"))
                            
                            # Mock successful transcription (should use original)
                            mock_transcription.transcribe_audio = AsyncMock(return_value={
                                "success": True,
                                "text": "Transcription from original audio"
                            })
                            
                            mock_ws.send_transcription_update = AsyncMock()
                            
                            # Call the background task
                            await process_audio_file(
                                meeting_id="meeting-123",
                                file_content=sample_file_content,
                                filename="test.wav",
                                user_id="user-123",
                                enhance_audio=True,
                                enhancement_options=None
                            )
                            
                            # Verify enhancement was attempted but failed gracefully
                            mock_enhancer.enhance_audio.assert_called_once()
                            mock_transcription.transcribe_audio.assert_called_once()
                            
                            # Should still complete successfully
                            final_update_call = mock_ws.send_transcription_update.call_args_list[-1]
                            assert final_update_call[1]['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_process_audio_file_transcription_failure(self, mock_db_session, sample_file_content):
        """Test audio processing when transcription fails"""
        with patch('app.api.v2.endpoints.transcription.get_db', return_value=iter([mock_db_session])):
            with patch('app.api.v2.endpoints.transcription.storage_service') as mock_storage:
                with patch('app.api.v2.endpoints.transcription.audio_enhancer') as mock_enhancer:
                    with patch('app.api.v2.endpoints.transcription.transcription_service') as mock_transcription:
                        with patch('app.api.v2.endpoints.transcription.websocket_manager') as mock_ws:
                            # Mock successful storage and enhancement
                            mock_storage.upload_file = AsyncMock(return_value={
                                "success": True,
                                "file_url": "https://s3.example.com/original.wav"
                            })
                            
                            mock_enhancer.enhance_audio = AsyncMock(return_value="/tmp/enhanced.wav")
                            
                            # Mock transcription failure
                            mock_transcription.transcribe_audio = AsyncMock(return_value={
                                "success": False,
                                "error": "Transcription service unavailable"
                            })
                            
                            mock_ws.send_transcription_update = AsyncMock()
                            
                            # Call the background task
                            await process_audio_file(
                                meeting_id="meeting-123",
                                file_content=sample_file_content,
                                filename="test.wav",
                                user_id="user-123",
                                enhance_audio=True,
                                enhancement_options=None
                            )
                            
                            # Verify failure was handled
                            final_update_call = mock_ws.send_transcription_update.call_args_list[-1]
                            assert final_update_call[1]['status'] == 'failed'
                            assert 'error' in final_update_call[1]
    
    @pytest.mark.asyncio
    async def test_process_audio_file_storage_failure(self, mock_db_session, sample_file_content):
        """Test audio processing when storage upload fails"""
        with patch('app.api.v2.endpoints.transcription.get_db', return_value=iter([mock_db_session])):
            with patch('app.api.v2.endpoints.transcription.storage_service') as mock_storage:
                with patch('app.api.v2.endpoints.transcription.websocket_manager') as mock_ws:
                    # Mock storage failure
                    mock_storage.upload_file = AsyncMock(return_value={
                        "success": False,
                        "error": "Storage service unavailable"
                    })
                    
                    mock_ws.send_transcription_update = AsyncMock()
                    
                    # Call the background task
                    await process_audio_file(
                        meeting_id="meeting-123",
                        file_content=sample_file_content,
                        filename="test.wav",
                        user_id="user-123",
                        enhance_audio=False,
                        enhancement_options=None
                    )
                    
                    # Verify failure was handled
                    final_update_call = mock_ws.send_transcription_update.call_args_list[-1]
                    assert final_update_call[1]['status'] == 'failed'
                    assert 'Storage service unavailable' in final_update_call[1]['error']
    
    @pytest.mark.asyncio
    async def test_process_audio_file_meeting_not_found(self, sample_file_content):
        """Test audio processing when meeting is not found"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No meeting found
        mock_db.close = Mock()
        
        with patch('app.api.v2.endpoints.transcription.get_db', return_value=iter([mock_db])):
            # Should handle gracefully and not crash
            await process_audio_file(
                meeting_id="nonexistent-meeting",
                file_content=sample_file_content,
                filename="test.wav",
                user_id="user-123",
                enhance_audio=False,
                enhancement_options=None
            )
            
            # Should close database connection
            mock_db.close.assert_called_once()
