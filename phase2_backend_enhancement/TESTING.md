# Audio Enhancement Testing Guide

## Overview

This document provides comprehensive testing guidance for the audio enhancement features in the IAM transcription application. The test suite covers unit tests, integration tests, and performance benchmarks.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_audio_enhancement.py      # Audio enhancement service tests
├── test_transcription_service.py  # Transcription service tests
├── test_storage_service.py        # Storage service tests
└── test_transcription_endpoints.py # API endpoint tests
```

## Quick Start

### 1. Install Test Dependencies

```bash
# Install test requirements
pip install -r requirements-test.txt

# Verify installation
python run_tests.py --check-deps
```

### 2. Run Basic Tests

```bash
# Run unit tests (fast, no external dependencies)
python run_tests.py unit

# Run all tests with coverage
python run_tests.py all

# Generate comprehensive test report
python run_tests.py report
```

## Test Categories

### 🧪 Unit Tests
Fast tests with no external dependencies. Mock all external services.

```bash
# Run unit tests only
python run_tests.py unit

# Run specific service tests
python run_tests.py audio
python run_tests.py storage
python run_tests.py transcription
python run_tests.py endpoints
```

**Coverage:**
- Audio enhancement pipeline components
- Service initialization and configuration
- Error handling and edge cases
- Parameter validation
- Mock external API calls

### 🔗 Integration Tests
Tests that require external services (OpenAI API, S3/Wasabi storage).

```bash
# Set up environment variables
export OPENAI_API_KEY="your-openai-key"
export S3_ACCESS_KEY="your-s3-key"
export S3_SECRET_KEY="your-s3-secret"
export S3_BUCKET_NAME="your-test-bucket"

# Run integration tests
python run_tests.py integration
```

**Coverage:**
- Real OpenAI API transcription
- Actual S3/Wasabi file operations
- End-to-end audio processing workflow
- Network error handling

### ⚡ Performance Tests
Benchmarks for audio processing performance.

```bash
# Run performance tests
python run_tests.py performance
```

**Coverage:**
- Audio enhancement processing times
- Memory usage during processing
- File size vs processing time correlation
- Concurrent processing capabilities

## Test Features

### 🎵 Audio Test Data Generation

The test suite includes sophisticated audio data generators:

```python
# Generate clean audio
audio, sr = sample_audio_data(duration=2.0, sample_rate=16000)

# Generate speech-like audio
audio, sr = speech_like_audio(duration=3.0)

# Generate noisy audio with controlled SNR
audio, sr = noisy_audio(duration=2.0, snr_db=10.0)
```

### 🎛️ Enhancement Testing

Tests cover all enhancement features:

- **Noise Reduction**: RNNoise and spectral gating
- **VAD Attenuation**: Voice activity detection
- **Frequency Filtering**: High-pass filters
- **Dynamic Processing**: Compression and limiting
- **Loudness Normalization**: LUFS-based normalization
- **Speech Enhancement**: Frequency boost

### 📊 Coverage Reporting

```bash
# Generate HTML coverage report
python run_tests.py all

# View coverage report
open htmlcov/index.html
```

**Target Coverage:** 80%+ for all services

## Test Configuration

### Environment Variables

```bash
# Required for integration tests
OPENAI_API_KEY=your-openai-api-key
S3_ACCESS_KEY=your-s3-access-key
S3_SECRET_KEY=your-s3-secret-key
S3_BUCKET_NAME=your-test-bucket

# Optional test configuration
TESTING=true
TEST_DATABASE_URL=sqlite:///:memory:
MAX_TEST_DURATION=300
```

### Pytest Configuration

Key settings in `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires external services)
    slow: Slow tests (performance benchmarks)
    audio: Audio processing tests
    
addopts = 
    -v --tb=short --cov=app --cov-fail-under=80
```

## Running Specific Tests

### By Test File

```bash
# Audio enhancement tests only
pytest tests/test_audio_enhancement.py -v

# Storage service tests only
pytest tests/test_storage_service.py -v
```

### By Test Markers

```bash
# Run only audio-related tests
pytest -m audio -v

# Run only fast unit tests
pytest -m "unit and not slow" -v

# Skip integration tests
pytest -m "not integration" -v
```

### By Test Name Pattern

```bash
# Run tests matching pattern
pytest -k "test_enhancement" -v

# Run specific test method
pytest tests/test_audio_enhancement.py::TestAudioEnhancementService::test_noise_reduction -v
```

## Test Data and Fixtures

### Shared Fixtures

Available in all tests via `conftest.py`:

- `sample_audio_data()`: Generate synthetic audio
- `speech_like_audio()`: Generate speech-like audio
- `noisy_audio()`: Generate noisy audio with controlled SNR
- `audio_file_factory()`: Create temporary audio files
- `mock_openai_client()`: Mock OpenAI API client
- `mock_s3_client()`: Mock S3 client
- `enhancement_options()`: Standard enhancement settings
- `transcription_settings()`: Standard transcription settings

### Example Usage

```python
def test_audio_processing(sample_audio_data, enhancement_options):
    """Test audio processing with generated data"""
    audio, sr = sample_audio_data(duration=2.0, noise_level=0.1)
    
    service = AudioEnhancementService()
    enhanced = service._apply_enhancement_pipeline(audio, sr, enhancement_options)
    
    assert len(enhanced) == len(audio)
    assert not np.array_equal(audio, enhanced)
```

## Debugging Tests

### Verbose Output

```bash
# Maximum verbosity
pytest -vvv --tb=long

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Test Debugging

```python
import pytest

def test_with_debugging():
    # Set breakpoint for debugging
    pytest.set_trace()
    
    # Your test code here
    assert True
```

### Log Output

```bash
# Show log output during tests
pytest --log-cli-level=DEBUG
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Audio Enhancement Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg libsndfile1
    
    - name: Install Python dependencies
      run: |
        pip install -r requirements-test.txt
        pip install -r requirements-audio.txt
    
    - name: Run unit tests
      run: python run_tests.py unit
    
    - name: Run integration tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        S3_ACCESS_KEY: ${{ secrets.S3_ACCESS_KEY }}
        S3_SECRET_KEY: ${{ secrets.S3_SECRET_KEY }}
        S3_BUCKET_NAME: ${{ secrets.S3_BUCKET_NAME }}
      run: python run_tests.py integration
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
```

## Performance Benchmarks

### Expected Performance

| File Size | Duration | Enhancement Time | Memory Usage |
|-----------|----------|------------------|--------------|
| 1MB       | 30s      | 5-15s           | 50-100MB     |
| 10MB      | 5min     | 30-60s          | 100-200MB    |
| 50MB      | 25min    | 2-5min          | 200-500MB    |

### Benchmark Tests

```bash
# Run performance benchmarks
pytest tests/ -m slow --benchmark-only

# Generate benchmark report
pytest tests/ -m slow --benchmark-json=benchmark.json
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Install audio libraries
   sudo apt-get install ffmpeg libsndfile1
   pip install soundfile librosa
   ```

2. **Memory Issues**
   ```bash
   # Reduce test file sizes
   export TEST_AUDIO_DURATION=1.0
   ```

3. **Timeout Issues**
   ```bash
   # Increase timeout
   pytest --timeout=600
   ```

### Test Failures

1. **Check test logs**: `pytest --log-cli-level=DEBUG`
2. **Run single test**: `pytest tests/test_file.py::test_function -v`
3. **Check environment**: `python run_tests.py --check-deps`

## Contributing

### Adding New Tests

1. **Follow naming convention**: `test_*.py`
2. **Use appropriate markers**: `@pytest.mark.unit`
3. **Add docstrings**: Describe what the test validates
4. **Use fixtures**: Leverage shared test data
5. **Mock external services**: Keep unit tests fast

### Test Quality Guidelines

- **Arrange-Act-Assert**: Clear test structure
- **Single responsibility**: One concept per test
- **Descriptive names**: `test_enhancement_reduces_noise_level`
- **Edge cases**: Test boundary conditions
- **Error cases**: Test failure scenarios

---

**Happy Testing!** 🧪✨

For questions or issues, check the test logs and ensure all dependencies are installed correctly.
