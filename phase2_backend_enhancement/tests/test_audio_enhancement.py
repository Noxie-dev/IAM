"""
Unit Tests for Audio Enhancement Service
Phase 2: Backend Enhancement

Tests for the production-ready audio enhancement pipeline
"""

import os
import json
import tempfile
import pytest
import numpy as np
import soundfile as sf
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the service to test
from app.services.audio_enhancement import AudioEnhancementService


class TestAudioEnhancementService:
    """Test suite for AudioEnhancementService"""
    
    @pytest.fixture
    def enhancement_service(self):
        """Create AudioEnhancementService instance for testing"""
        return AudioEnhancementService()
    
    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio data for testing"""
        # Generate 2 seconds of sample audio at 16kHz
        duration = 2.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create a mix of sine waves (simulating speech frequencies)
        audio = (
            0.3 * np.sin(2 * np.pi * 440 * t) +  # A4 note
            0.2 * np.sin(2 * np.pi * 880 * t) +  # A5 note
            0.1 * np.random.normal(0, 0.05, len(t))  # Add some noise
        )
        
        return audio, sample_rate
    
    @pytest.fixture
    def temp_audio_file(self, sample_audio):
        """Create temporary audio file for testing"""
        audio, sr = sample_audio
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio, sr)
            yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_service_initialization(self, enhancement_service):
        """Test service initializes correctly"""
        assert enhancement_service is not None
        assert hasattr(enhancement_service, 'executor')
        assert hasattr(enhancement_service, 'supported_formats')
        assert '.wav' in enhancement_service.supported_formats
        assert '.mp3' in enhancement_service.supported_formats
    
    def test_parse_options_default(self, enhancement_service):
        """Test parsing of default enhancement options"""
        options = enhancement_service._parse_options(None)
        
        assert options['sample_rate'] == 16000
        assert options['noise_reduction'] is True
        assert options['vad_attenuation_db'] == 12
        assert options['high_pass_freq'] == 80
        assert options['lufs_target'] == -23.0
        assert options['speaker_boost_db'] == 3.0
        assert options['normalize_loudness'] is True
    
    def test_parse_options_custom(self, enhancement_service):
        """Test parsing of custom enhancement options"""
        custom_options = {
            "sample_rate": 22050,
            "noise_reduction": False,
            "vad_attenuation_db": 15,
            "high_pass_freq": 100
        }
        
        options = enhancement_service._parse_options(json.dumps(custom_options))
        
        assert options['sample_rate'] == 22050
        assert options['noise_reduction'] is False
        assert options['vad_attenuation_db'] == 15
        assert options['high_pass_freq'] == 100
        # Default values should still be present
        assert options['lufs_target'] == -23.0
    
    def test_parse_options_invalid_json(self, enhancement_service):
        """Test parsing of invalid JSON options"""
        options = enhancement_service._parse_options("invalid json")
        
        # Should return default options
        assert options['sample_rate'] == 16000
        assert options['noise_reduction'] is True
    
    def test_high_pass_filter(self, enhancement_service, sample_audio):
        """Test high-pass filter functionality"""
        audio, sr = sample_audio
        
        # Apply high-pass filter
        filtered = enhancement_service._apply_high_pass_filter(audio, sr, 100)
        
        assert len(filtered) == len(audio)
        assert isinstance(filtered, np.ndarray)
        # Filtered audio should be different from original
        assert not np.array_equal(audio, filtered)
    
    def test_compression(self, enhancement_service, sample_audio):
        """Test dynamic range compression"""
        audio, sr = sample_audio
        
        # Apply compression
        compressed = enhancement_service._apply_compression(audio, 3.0)
        
        assert len(compressed) == len(audio)
        assert isinstance(compressed, np.ndarray)
        # Peak levels should be reduced
        assert np.max(np.abs(compressed)) <= np.max(np.abs(audio))
    
    def test_limiter(self, enhancement_service, sample_audio):
        """Test limiter functionality"""
        audio, sr = sample_audio
        
        # Apply limiter with -6dB threshold
        limited = enhancement_service._apply_limiter(audio, -6.0)
        
        assert len(limited) == len(audio)
        assert isinstance(limited, np.ndarray)
        
        # Check that peaks are limited to threshold
        threshold = 10 ** (-6.0 / 20)
        assert np.max(np.abs(limited)) <= threshold + 1e-6  # Small tolerance for floating point
    
    @patch('app.services.audio_enhancement.HAS_NOISEREDUCE', True)
    @patch('app.services.audio_enhancement.nr')
    def test_noise_reduction_with_noisereduce(self, mock_nr, enhancement_service, sample_audio):
        """Test noise reduction using noisereduce library"""
        audio, sr = sample_audio
        mock_nr.reduce_noise.return_value = audio * 0.8  # Simulate noise reduction
        
        result = enhancement_service._apply_noise_reduction(audio, sr)
        
        mock_nr.reduce_noise.assert_called_once()
        assert len(result) == len(audio)
    
    @patch('app.services.audio_enhancement.HAS_NOISEREDUCE', False)
    def test_noise_reduction_fallback(self, enhancement_service, sample_audio):
        """Test noise reduction fallback when noisereduce is not available"""
        audio, sr = sample_audio
        
        result = enhancement_service._apply_noise_reduction(audio, sr)
        
        assert len(result) == len(audio)
        assert isinstance(result, np.ndarray)
    
    @patch('app.services.audio_enhancement.HAS_WEBRTCVAD', True)
    @patch('app.services.audio_enhancement.webrtcvad')
    def test_vad_attenuation(self, mock_webrtcvad, enhancement_service, sample_audio):
        """Test VAD-based attenuation"""
        audio, sr = sample_audio
        
        # Mock VAD
        mock_vad = Mock()
        mock_vad.is_speech.return_value = False  # Simulate non-speech
        mock_webrtcvad.Vad.return_value = mock_vad
        
        result = enhancement_service._apply_vad_attenuation(audio, sr, 12.0)
        
        assert len(result) == len(audio)
        # Non-speech should be attenuated
        assert np.mean(np.abs(result)) < np.mean(np.abs(audio))
    
    @patch('app.services.audio_enhancement.HAS_PYLOUDNORM', True)
    @patch('app.services.audio_enhancement.pyln')
    def test_lufs_normalization(self, mock_pyln, enhancement_service, sample_audio):
        """Test LUFS loudness normalization"""
        audio, sr = sample_audio
        
        # Mock pyloudnorm
        mock_meter = Mock()
        mock_meter.integrated_loudness.return_value = -30.0  # Simulate current loudness
        mock_pyln.Meter.return_value = mock_meter
        mock_pyln.normalize.loudness.return_value = audio * 1.5  # Simulate normalization
        
        result = enhancement_service._apply_lufs_normalization(audio, sr, -23.0)
        
        mock_pyln.Meter.assert_called_once_with(sr)
        mock_pyln.normalize.loudness.assert_called_once()
        assert len(result) == len(audio)
    
    def test_speaker_boost(self, enhancement_service, sample_audio):
        """Test primary speaker boost"""
        audio, sr = sample_audio
        
        result = enhancement_service._apply_speaker_boost(audio, sr, 3.0)
        
        assert len(result) == len(audio)
        assert isinstance(result, np.ndarray)
        # Should enhance speech frequencies
        assert not np.array_equal(audio, result)
    
    def test_enhancement_pipeline(self, enhancement_service, sample_audio):
        """Test complete enhancement pipeline"""
        audio, sr = sample_audio
        
        options = {
            "noise_reduction": True,
            "vad_attenuation_db": 10,
            "high_pass_freq": 80,
            "compression_ratio": 2.0,
            "limiter_threshold": -3.0,
            "normalize_loudness": False,  # Skip LUFS to avoid mocking
            "speaker_boost_db": 2.0
        }
        
        result = enhancement_service._apply_enhancement_pipeline(audio, sr, options)
        
        assert len(result) == len(audio)
        assert isinstance(result, np.ndarray)
        # Enhanced audio should be different from original
        assert not np.array_equal(audio, result)
    
    def test_enhance_audio_sync_success(self, enhancement_service, temp_audio_file):
        """Test synchronous audio enhancement success case"""
        output_dir = tempfile.gettempdir()
        options = {"sample_rate": 16000, "noise_reduction": True}
        
        result_path = enhancement_service._enhance_audio_sync(
            temp_audio_file, output_dir, options
        )
        
        assert os.path.exists(result_path)
        assert result_path.endswith('_enhanced.wav')
        
        # Verify enhanced file is valid
        audio, sr = sf.read(result_path)
        assert len(audio) > 0
        assert sr == 16000
        
        # Cleanup
        if os.path.exists(result_path):
            os.unlink(result_path)
    
    def test_enhance_audio_sync_file_not_found(self, enhancement_service):
        """Test enhancement with non-existent input file"""
        output_dir = tempfile.gettempdir()
        options = {"sample_rate": 16000}
        
        result_path = enhancement_service._enhance_audio_sync(
            "nonexistent.wav", output_dir, options
        )
        
        # Should return original path on error
        assert result_path == "nonexistent.wav"
    
    @pytest.mark.asyncio
    async def test_enhance_audio_async(self, enhancement_service, temp_audio_file):
        """Test asynchronous audio enhancement"""
        output_dir = tempfile.gettempdir()
        options = json.dumps({"sample_rate": 16000, "noise_reduction": True})
        
        result_path = await enhancement_service.enhance_audio(
            temp_audio_file, output_dir, options
        )
        
        assert os.path.exists(result_path)
        assert result_path.endswith('_enhanced.wav')
        
        # Cleanup
        if os.path.exists(result_path):
            os.unlink(result_path)
    
    def test_enhancement_preserves_audio_length(self, enhancement_service, sample_audio):
        """Test that enhancement preserves audio length"""
        audio, sr = sample_audio
        original_length = len(audio)
        
        options = {
            "noise_reduction": True,
            "vad_attenuation_db": 12,
            "high_pass_freq": 80,
            "normalize_loudness": False
        }
        
        enhanced = enhancement_service._apply_enhancement_pipeline(audio, sr, options)
        
        assert len(enhanced) == original_length
    
    def test_enhancement_handles_empty_audio(self, enhancement_service):
        """Test enhancement with empty audio array"""
        empty_audio = np.array([])
        sr = 16000
        options = {"noise_reduction": True}
        
        # Should handle gracefully without crashing
        result = enhancement_service._apply_enhancement_pipeline(empty_audio, sr, options)
        assert len(result) == 0
    
    def test_enhancement_handles_mono_audio(self, enhancement_service):
        """Test enhancement with mono audio"""
        # Generate mono audio
        duration = 1.0
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration), False)
        mono_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        options = {"noise_reduction": True, "normalize_loudness": False}
        
        result = enhancement_service._apply_enhancement_pipeline(mono_audio, sr, options)
        
        assert result.ndim == 1  # Should remain mono
        assert len(result) == len(mono_audio)
    
    @patch('app.services.audio_enhancement.logger')
    def test_enhancement_logs_errors(self, mock_logger, enhancement_service, sample_audio):
        """Test that enhancement errors are properly logged"""
        audio, sr = sample_audio
        
        # Force an error by passing invalid parameters
        with patch.object(enhancement_service, '_apply_noise_reduction', side_effect=Exception("Test error")):
            result = enhancement_service._apply_enhancement_pipeline(audio, sr, {"noise_reduction": True})
            
            # Should return original audio on error
            assert np.array_equal(result, audio)
            # Should log the error
            mock_logger.warning.assert_called()


class TestAudioEnhancementIntegration:
    """Integration tests for audio enhancement with file I/O"""
    
    @pytest.fixture
    def sample_files(self):
        """Create sample audio files in different formats"""
        files = {}
        
        # Generate test audio
        duration = 1.0
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration), False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Create WAV file
        wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(wav_file.name, audio, sr)
        files['wav'] = wav_file.name
        
        yield files
        
        # Cleanup
        for file_path in files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_end_to_end_enhancement(self, sample_files):
        """Test complete end-to-end enhancement process"""
        service = AudioEnhancementService()
        input_file = sample_files['wav']
        output_dir = tempfile.gettempdir()
        
        # Test with realistic options
        options = {
            "sample_rate": 16000,
            "noise_reduction": True,
            "vad_attenuation_db": 12,
            "high_pass_freq": 80,
            "compression_ratio": 3.0,
            "limiter_threshold": -1.0,
            "normalize_loudness": False,  # Skip to avoid dependency issues
            "speaker_boost_db": 3.0
        }
        
        result_path = service._enhance_audio_sync(input_file, output_dir, options)
        
        # Verify output
        assert os.path.exists(result_path)
        assert result_path != input_file
        
        # Load and verify enhanced audio
        enhanced_audio, enhanced_sr = sf.read(result_path)
        original_audio, original_sr = sf.read(input_file)
        
        assert enhanced_sr == options["sample_rate"]
        assert len(enhanced_audio) > 0
        
        # Enhanced audio should be different from original
        # (unless all enhancements are no-ops, which is unlikely)
        if len(enhanced_audio) == len(original_audio):
            # Allow for small differences due to processing
            assert not np.allclose(enhanced_audio, original_audio, atol=1e-6)
        
        # Cleanup
        if os.path.exists(result_path):
            os.unlink(result_path)
    
    def test_performance_benchmark(self, sample_files):
        """Basic performance test for enhancement pipeline"""
        import time
        
        service = AudioEnhancementService()
        input_file = sample_files['wav']
        output_dir = tempfile.gettempdir()
        
        options = {
            "sample_rate": 16000,
            "noise_reduction": True,
            "normalize_loudness": False
        }
        
        start_time = time.time()
        result_path = service._enhance_audio_sync(input_file, output_dir, options)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on your requirements)
        assert processing_time < 10.0  # 10 seconds for 1 second of audio
        assert os.path.exists(result_path)
        
        # Cleanup
        if os.path.exists(result_path):
            os.unlink(result_path)
