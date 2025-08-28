"""
Unit Tests for Transcription Service
Phase 2: Backend Enhancement

Tests for multi-provider transcription service with retry logic
"""

import os
import tempfile
import pytest
import soundfile as sf
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from app.services.transcription_service import TranscriptionService
from app.models.meeting import Meeting


class TestTranscriptionService:
    """Test suite for TranscriptionService"""
    
    @pytest.fixture
    def transcription_service(self):
        """Create TranscriptionService instance for testing"""
        with patch('app.services.transcription_service.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test-api-key"
            return TranscriptionService()
    
    @pytest.fixture
    def mock_meeting(self):
        """Create mock meeting object"""
        meeting = Mock(spec=Meeting)
        meeting.transcription_settings = {
            "provider": "openai",
            "model": "whisper-1",
            "language": "en",
            "timestamps": True
        }
        return meeting
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create temporary audio file for testing"""
        # Generate 1 second of test audio
        duration = 1.0
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration), False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio, sr)
            yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_service_initialization(self, transcription_service):
        """Test service initializes correctly"""
        assert transcription_service is not None
        assert hasattr(transcription_service, 'executor')
        assert hasattr(transcription_service, 'openai_client')
    
    def test_get_supported_providers(self, transcription_service):
        """Test getting supported providers"""
        providers = transcription_service.get_supported_providers()
        
        assert isinstance(providers, dict)
        assert 'openai' in providers
        assert 'azure' in providers
        assert 'google' in providers
        assert providers['openai'] is True  # Should be True with mock API key
    
    def test_validate_settings_openai_valid(self, transcription_service):
        """Test validation of valid OpenAI settings"""
        settings = {
            "model": "whisper-1",
            "language": "en"
        }
        
        result = transcription_service.validate_settings("openai", settings)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_settings_openai_invalid_model(self, transcription_service):
        """Test validation of invalid OpenAI model"""
        settings = {
            "model": "invalid-model",
            "language": "en"
        }
        
        result = transcription_service.validate_settings("openai", settings)
        
        assert result['valid'] is False
        assert any("Unsupported OpenAI model" in error for error in result['errors'])
    
    def test_validate_settings_unsupported_provider(self, transcription_service):
        """Test validation of unsupported provider"""
        result = transcription_service.validate_settings("unsupported", {})
        
        assert result['valid'] is False
        assert any("Unsupported provider" in error for error in result['errors'])
    
    @patch('app.services.transcription_service.OpenAI')
    def test_transcribe_openai_success(self, mock_openai_class, transcription_service, sample_audio_file):
        """Test successful OpenAI transcription"""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_transcript = Mock()
        mock_transcript.text = "This is a test transcription."
        mock_transcript.language = "en"
        mock_transcript.duration = 1.0
        mock_transcript.segments = [
            {"start": 0.0, "end": 1.0, "text": "This is a test transcription."}
        ]
        
        mock_client.audio.transcriptions.create.return_value = mock_transcript
        
        # Reinitialize service with mocked client
        transcription_service.openai_client = mock_client
        
        settings = {
            "model": "whisper-1",
            "language": "en",
            "timestamps": True
        }
        
        result = transcription_service._transcribe_openai(sample_audio_file, settings)
        
        assert result['success'] is True
        assert result['text'] == "This is a test transcription."
        assert result['language'] == "en"
        assert result['duration'] == 1.0
        assert 'segments' in result
    
    @patch('app.services.transcription_service.OpenAI')
    def test_transcribe_openai_text_only(self, mock_openai_class, transcription_service, sample_audio_file):
        """Test OpenAI transcription with text-only response"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_client.audio.transcriptions.create.return_value = "Simple text response."
        transcription_service.openai_client = mock_client
        
        settings = {
            "model": "whisper-1",
            "timestamps": False
        }
        
        result = transcription_service._transcribe_openai(sample_audio_file, settings)
        
        assert result['success'] is True
        assert result['text'] == "Simple text response."
        assert 'segments' not in result
    
    @patch('app.services.transcription_service.OpenAI')
    def test_transcribe_openai_rate_limit_error(self, mock_openai_class, transcription_service, sample_audio_file):
        """Test OpenAI transcription with rate limit error"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_client.audio.transcriptions.create.side_effect = Exception("Rate limit exceeded")
        transcription_service.openai_client = mock_client
        
        settings = {"model": "whisper-1"}
        
        result = transcription_service._transcribe_openai(sample_audio_file, settings)
        
        assert result['success'] is False
        assert "Rate limit exceeded" in result['error']
        assert result['error_type'] == 'rate_limit'
    
    @patch('app.services.transcription_service.OpenAI')
    def test_transcribe_openai_authentication_error(self, mock_openai_class, transcription_service, sample_audio_file):
        """Test OpenAI transcription with authentication error"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_client.audio.transcriptions.create.side_effect = Exception("Authentication failed")
        transcription_service.openai_client = mock_client
        
        settings = {"model": "whisper-1"}
        
        result = transcription_service._transcribe_openai(sample_audio_file, settings)
        
        assert result['success'] is False
        assert "Authentication failed" in result['error']
        assert result['error_type'] == 'authentication'
    
    def test_transcribe_openai_no_client(self, sample_audio_file):
        """Test OpenAI transcription without configured client"""
        service = TranscriptionService()
        service.openai_client = None
        
        result = service._transcribe_openai(sample_audio_file, {})
        
        assert result['success'] is False
        assert "OpenAI client not configured" in result['error']
    
    def test_transcribe_azure_not_implemented(self, transcription_service, sample_audio_file):
        """Test Azure transcription (not yet implemented)"""
        result = transcription_service._transcribe_azure(sample_audio_file, {})
        
        assert result['success'] is False
        assert "not yet implemented" in result['error']
    
    def test_transcribe_google_not_implemented(self, transcription_service, sample_audio_file):
        """Test Google transcription (not yet implemented)"""
        result = transcription_service._transcribe_google(sample_audio_file, {})
        
        assert result['success'] is False
        assert "not yet implemented" in result['error']
    
    def test_transcribe_with_retry_success_first_attempt(self, transcription_service, sample_audio_file):
        """Test transcription with retry - success on first attempt"""
        with patch.object(transcription_service, '_transcribe_openai') as mock_transcribe:
            mock_transcribe.return_value = {
                'success': True,
                'text': 'Test transcription'
            }
            
            result = transcription_service._transcribe_with_retry(
                sample_audio_file, "openai", {}, 3
            )
            
            assert result['success'] is True
            assert result['text'] == 'Test transcription'
            assert mock_transcribe.call_count == 1
    
    def test_transcribe_with_retry_success_after_failures(self, transcription_service, sample_audio_file):
        """Test transcription with retry - success after initial failures"""
        with patch.object(transcription_service, '_transcribe_openai') as mock_transcribe:
            # First two calls fail, third succeeds
            mock_transcribe.side_effect = [
                Exception("Temporary error"),
                Exception("Another error"),
                {'success': True, 'text': 'Success after retries'}
            ]
            
            with patch('asyncio.sleep'):  # Mock sleep to speed up test
                result = transcription_service._transcribe_with_retry(
                    sample_audio_file, "openai", {}, 3
                )
            
            assert result['success'] is True
            assert result['text'] == 'Success after retries'
            assert mock_transcribe.call_count == 3
    
    def test_transcribe_with_retry_all_attempts_fail(self, transcription_service, sample_audio_file):
        """Test transcription with retry - all attempts fail"""
        with patch.object(transcription_service, '_transcribe_openai') as mock_transcribe:
            mock_transcribe.side_effect = Exception("Persistent error")
            
            with patch('asyncio.sleep'):  # Mock sleep to speed up test
                result = transcription_service._transcribe_with_retry(
                    sample_audio_file, "openai", {}, 3
                )
            
            assert result['success'] is False
            assert "failed after 3 attempts" in result['error']
            assert "Persistent error" in result['error']
            assert mock_transcribe.call_count == 3
    
    def test_transcribe_with_retry_unsupported_provider(self, transcription_service, sample_audio_file):
        """Test transcription with unsupported provider"""
        result = transcription_service._transcribe_with_retry(
            sample_audio_file, "unsupported", {}, 3
        )
        
        assert result['success'] is False
        assert "Unsupported provider" in result['error']
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_async(self, transcription_service, mock_meeting, sample_audio_file):
        """Test asynchronous transcription"""
        with patch.object(transcription_service, '_transcribe_with_retry') as mock_transcribe:
            mock_transcribe.return_value = {
                'success': True,
                'text': 'Async transcription result'
            }
            
            result = await transcription_service.transcribe_audio(
                sample_audio_file, mock_meeting, max_retries=3
            )
            
            assert result['success'] is True
            assert result['text'] == 'Async transcription result'
            mock_transcribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_custom_settings(self, transcription_service, sample_audio_file):
        """Test transcription with custom meeting settings"""
        meeting = Mock(spec=Meeting)
        meeting.transcription_settings = {
            "provider": "openai",
            "model": "whisper-1",
            "language": "es",
            "timestamps": False
        }
        
        with patch.object(transcription_service, '_transcribe_with_retry') as mock_transcribe:
            mock_transcribe.return_value = {'success': True, 'text': 'Spanish text'}
            
            await transcription_service.transcribe_audio(sample_audio_file, meeting)
            
            # Verify correct settings were passed
            call_args = mock_transcribe.call_args
            assert call_args[0][1] == "openai"  # provider
            assert call_args[0][2]["language"] == "es"  # settings
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_settings(self, transcription_service, sample_audio_file):
        """Test transcription with no meeting settings (use defaults)"""
        meeting = Mock(spec=Meeting)
        meeting.transcription_settings = None
        
        with patch.object(transcription_service, '_transcribe_with_retry') as mock_transcribe:
            mock_transcribe.return_value = {'success': True, 'text': 'Default settings'}
            
            await transcription_service.transcribe_audio(sample_audio_file, meeting)
            
            # Should use default provider
            call_args = mock_transcribe.call_args
            assert call_args[0][1] == "openai"  # default provider


class TestTranscriptionIntegration:
    """Integration tests for transcription service"""
    
    @pytest.fixture
    def real_audio_file(self):
        """Create a more realistic audio file for integration testing"""
        # Generate 3 seconds of more complex audio
        duration = 3.0
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration), False)
        
        # Mix of frequencies to simulate speech
        audio = (
            0.3 * np.sin(2 * np.pi * 300 * t) +  # Low frequency
            0.4 * np.sin(2 * np.pi * 1000 * t) +  # Mid frequency
            0.2 * np.sin(2 * np.pi * 2000 * t) +  # High frequency
            0.1 * np.random.normal(0, 0.02, len(t))  # Background noise
        )
        
        # Add some amplitude variation
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)
        audio = audio * envelope
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio, sr)
            yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not available")
    async def test_real_openai_transcription(self, real_audio_file):
        """Integration test with real OpenAI API (requires API key)"""
        service = TranscriptionService()
        
        meeting = Mock(spec=Meeting)
        meeting.transcription_settings = {
            "provider": "openai",
            "model": "whisper-1",
            "language": "en",
            "timestamps": True
        }
        
        result = await service.transcribe_audio(real_audio_file, meeting)
        
        # Note: This will likely return empty or nonsensical text since we're using synthetic audio
        # But it tests the actual API integration
        assert 'success' in result
        assert 'text' in result or 'error' in result
    
    def test_file_handling_edge_cases(self, transcription_service):
        """Test transcription service with various file edge cases"""
        # Test with non-existent file
        result = transcription_service._transcribe_openai("nonexistent.wav", {})
        assert result['success'] is False
        
        # Test with empty settings
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            # Create minimal valid WAV file
            sf.write(temp_file.name, np.array([0.0]), 16000)
            
            # Should handle empty settings gracefully
            result = transcription_service._transcribe_openai(temp_file.name, {})
            # Will fail due to no OpenAI client, but shouldn't crash
            assert 'success' in result
