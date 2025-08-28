"""
Pytest Configuration and Fixtures
Phase 2: Backend Enhancement

Shared fixtures and configuration for audio enhancement tests
"""

import os
import tempfile
import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, Any, Generator


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing"""
    def _generate_audio(
        duration: float = 2.0,
        sample_rate: int = 16000,
        frequency: float = 440.0,
        noise_level: float = 0.1
    ) -> tuple[np.ndarray, int]:
        """Generate synthetic audio with optional noise"""
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Generate base signal (sine wave)
        audio = 0.5 * np.sin(2 * np.pi * frequency * t)
        
        # Add harmonics for more realistic sound
        audio += 0.2 * np.sin(2 * np.pi * frequency * 2 * t)
        audio += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)
        
        # Add noise if requested
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, len(audio))
            audio += noise
        
        # Normalize to prevent clipping
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        return audio, sample_rate
    
    return _generate_audio


@pytest.fixture
def speech_like_audio():
    """Generate more speech-like audio for testing"""
    def _generate_speech_audio(
        duration: float = 3.0,
        sample_rate: int = 16000
    ) -> tuple[np.ndarray, int]:
        """Generate synthetic speech-like audio"""
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Mix of frequencies common in speech
        formants = [300, 800, 2200, 3500]  # Typical formant frequencies
        audio = np.zeros_like(t)
        
        for i, freq in enumerate(formants):
            amplitude = 0.3 / (i + 1)  # Decreasing amplitude
            audio += amplitude * np.sin(2 * np.pi * freq * t)
        
        # Add amplitude modulation to simulate speech patterns
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)  # 2 Hz modulation
        audio *= envelope
        
        # Add some background noise
        noise = np.random.normal(0, 0.05, len(audio))
        audio += noise
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.7
        
        return audio, sample_rate
    
    return _generate_speech_audio


@pytest.fixture
def noisy_audio():
    """Generate noisy audio for enhancement testing"""
    def _generate_noisy_audio(
        duration: float = 2.0,
        sample_rate: int = 16000,
        snr_db: float = 10.0
    ) -> tuple[np.ndarray, int]:
        """Generate audio with controlled signal-to-noise ratio"""
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Clean signal
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Generate noise
        noise = np.random.normal(0, 1, len(signal))
        
        # Calculate noise power for desired SNR
        signal_power = np.mean(signal ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = noise * np.sqrt(noise_power / np.mean(noise ** 2))
        
        # Combine signal and noise
        noisy_audio = signal + noise
        
        # Normalize to prevent clipping
        noisy_audio = noisy_audio / np.max(np.abs(noisy_audio)) * 0.8
        
        return noisy_audio, sample_rate
    
    return _generate_noisy_audio


@pytest.fixture
def audio_file_factory(test_data_dir, sample_audio_data):
    """Factory for creating temporary audio files"""
    created_files = []
    
    def _create_audio_file(
        filename: str = "test_audio.wav",
        duration: float = 2.0,
        sample_rate: int = 16000,
        audio_format: str = "WAV"
    ) -> Path:
        """Create temporary audio file"""
        audio, sr = sample_audio_data(duration=duration, sample_rate=sample_rate)
        file_path = test_data_dir / filename
        
        sf.write(str(file_path), audio, sr, format=audio_format)
        created_files.append(file_path)
        
        return file_path
    
    yield _create_audio_file
    
    # Cleanup
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for transcription testing"""
    client = Mock()
    
    # Mock successful transcription response
    mock_response = Mock()
    mock_response.text = "This is a test transcription."
    mock_response.language = "en"
    mock_response.duration = 2.0
    mock_response.segments = [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "This is a test"
        },
        {
            "start": 1.0,
            "end": 2.0,
            "text": "transcription."
        }
    ]
    
    client.audio.transcriptions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for storage testing"""
    client = Mock()
    
    # Mock successful operations
    client.head_bucket.return_value = {}
    client.upload_fileobj.return_value = None
    client.delete_object.return_value = {}
    client.head_object.return_value = {
        'ContentLength': 1024,
        'ContentType': 'audio/wav',
        'LastModified': '2023-01-01T00:00:00Z',
        'ETag': '"abc123"',
        'Metadata': {}
    }
    client.list_objects_v2.return_value = {
        'Contents': [],
        'IsTruncated': False
    }
    client.generate_presigned_url.return_value = "https://presigned-url.example.com"
    
    return client


@pytest.fixture
def enhancement_options():
    """Standard enhancement options for testing"""
    return {
        "sample_rate": 16000,
        "noise_reduction": True,
        "vad_attenuation_db": 12,
        "high_pass_freq": 80,
        "dereverb": False,
        "compression_ratio": 3.0,
        "limiter_threshold": -1.0,
        "lufs_target": -23.0,
        "speaker_boost_db": 3.0,
        "normalize_loudness": True
    }


@pytest.fixture
def transcription_settings():
    """Standard transcription settings for testing"""
    return {
        "provider": "openai",
        "model": "whisper-1",
        "language": "en",
        "timestamps": True,
        "word_timestamps": False,
        "speaker_detection": False
    }


@pytest.fixture
def mock_meeting():
    """Mock meeting object for testing"""
    meeting = Mock()
    meeting.id = "test-meeting-123"
    meeting.title = "Test Meeting"
    meeting.description = "Test description"
    meeting.user_id = "test-user-123"
    meeting.processing_status = "pending"
    meeting.transcription_text = None
    meeting.transcription_metadata = {}
    meeting.transcription_settings = {
        "provider": "openai",
        "model": "whisper-1",
        "language": "en",
        "timestamps": True
    }
    
    # Mock methods
    meeting.add_metadata = Mock()
    meeting.set_audio_file = Mock()
    
    return meeting


@pytest.fixture
def mock_user():
    """Mock user object for testing"""
    user = Mock()
    user.id = "test-user-123"
    user.email = "test@example.com"
    user.subscription_tier = "premium"
    user.remaining_minutes = 100
    
    return user


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "S3_BUCKET_NAME": "test-bucket",
        "S3_ENDPOINT_URL": "https://test-s3.example.com",
        "OPENAI_API_KEY": "test-api-key"
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def performance_audio_files(test_data_dir, sample_audio_data):
    """Generate audio files of different sizes for performance testing"""
    files = {}
    
    # Small file (1 second)
    audio_small, sr = sample_audio_data(duration=1.0)
    small_path = test_data_dir / "small.wav"
    sf.write(str(small_path), audio_small, sr)
    files['small'] = small_path
    
    # Medium file (30 seconds)
    audio_medium, sr = sample_audio_data(duration=30.0)
    medium_path = test_data_dir / "medium.wav"
    sf.write(str(medium_path), audio_medium, sr)
    files['medium'] = medium_path
    
    # Large file (2 minutes)
    audio_large, sr = sample_audio_data(duration=120.0)
    large_path = test_data_dir / "large.wav"
    sf.write(str(large_path), audio_large, sr)
    files['large'] = large_path
    
    yield files
    
    # Cleanup
    for file_path in files.values():
        if file_path.exists():
            file_path.unlink()


# Pytest markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.audio = pytest.mark.audio
pytest.mark.storage = pytest.mark.storage
pytest.mark.transcription = pytest.mark.transcription
pytest.mark.endpoints = pytest.mark.endpoints
