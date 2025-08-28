"""
Unit tests for DICE™ PreScan Algorithm (Algorithm 1: Extractor)
Tests OCR, document parsing, audio diarization, and entity detection
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List

from app.services.dice_algorithms.prescan_algorithm import PreScanAlgorithm
from app.schemas.dice_schemas import FileInfo, PreScanJSON, PreScanBlock, PreScanAudioSegment
from tests.fixtures.dice_test_data import DICETestFixtures, DICETestConstants


class TestPreScanAlgorithm:
    """Test suite for PreScan Algorithm"""
    
    @pytest.fixture
    def prescan_algorithm(self):
        """Create a PreScanAlgorithm instance for testing"""
        with patch('app.services.dice_algorithms.prescan_algorithm.boto3.client'):
            algorithm = PreScanAlgorithm()
            return algorithm
    
    @pytest.fixture
    def sample_files(self):
        """Create sample files for testing"""
        return [
            DICETestFixtures.create_sample_file_info(),
            DICETestFixtures.create_sample_audio_file_info()
        ]
    
    @pytest.mark.asyncio
    async def test_process_files_basic(self, prescan_algorithm, sample_files):
        """Test basic file processing functionality"""
        # Mock the individual processing methods
        with patch.object(prescan_algorithm, '_process_pdf_file', new_callable=AsyncMock) as mock_pdf, \
             patch.object(prescan_algorithm, '_process_audio_file', new_callable=AsyncMock) as mock_audio, \
             patch.object(prescan_algorithm, '_detect_entities', new_callable=AsyncMock) as mock_entities, \
             patch.object(prescan_algorithm, '_calculate_overall_confidence', return_value=0.85) as mock_confidence:
            
            result = await prescan_algorithm.process_files(sample_files)
            
            # Verify the result structure
            assert isinstance(result, PreScanJSON)
            assert result.ocr_confidence == 0.85
            assert result.algorithm_version == "1.0.0"
            
            # Verify methods were called
            mock_pdf.assert_called_once()
            mock_audio.assert_called_once()
            mock_entities.assert_called_once()
            mock_confidence.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_pdf_file(self, prescan_algorithm):
        """Test PDF file processing"""
        pdf_file = DICETestFixtures.create_sample_file_info()
        result = PreScanJSON()
        
        # Mock PDF processing dependencies
        mock_pdf_content = b"Mock PDF content"
        
        with patch.object(prescan_algorithm, '_download_file_from_s3', return_value=mock_pdf_content), \
             patch('app.services.dice_algorithms.prescan_algorithm.HAS_PDF', True), \
             patch('pdfplumber.open') as mock_pdfplumber:
            
            # Mock PDF pages
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test PDF content with important information"
            mock_page.bbox = [0, 0, 612, 792]  # Standard page size
            
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
            
            await prescan_algorithm._process_pdf_file(pdf_file, result)
            
            # Verify results
            assert result.pages is not None
            assert len(result.pages) > 0
            assert result.total_pages == 1
            assert result.pages[0].type == "text"
            assert "important information" in result.pages[0].text
    
    @pytest.mark.asyncio
    async def test_process_audio_file(self, prescan_algorithm):
        """Test audio file processing"""
        audio_file = DICETestFixtures.create_sample_audio_file_info()
        result = PreScanJSON()
        
        mock_audio_data = b"Mock audio data"
        mock_sample_rate = 16000
        mock_duration = 120.5
        
        with patch.object(prescan_algorithm, '_download_file_from_s3', return_value=mock_audio_data), \
             patch('app.services.dice_algorithms.prescan_algorithm.HAS_AUDIO', True), \
             patch('librosa.load') as mock_librosa, \
             patch('librosa.get_duration') as mock_duration_func:
            
            # Mock librosa functions
            mock_librosa.return_value = (None, mock_sample_rate)
            mock_duration_func.return_value = mock_duration
            
            await prescan_algorithm._process_audio_file(audio_file, result)
            
            # Verify results
            assert result.total_duration == mock_duration
            # Note: Audio segments would be added by diarization if available
    
    @pytest.mark.asyncio
    async def test_process_image_file(self, prescan_algorithm):
        """Test image file processing with OCR"""
        image_file = FileInfo(
            s3_uri="s3://test-bucket/test-image.jpg",
            mime_type="image/jpeg",
            original_filename="test_image.jpg",
            file_size=512000
        )
        result = PreScanJSON()
        
        mock_image_data = b"Mock image data"
        mock_ocr_text = "This is text extracted from an image"
        
        with patch.object(prescan_algorithm, '_download_file_from_s3', return_value=mock_image_data), \
             patch('app.services.dice_algorithms.prescan_algorithm.HAS_TESSERACT', True), \
             patch('pytesseract.image_to_string', return_value=mock_ocr_text) as mock_ocr, \
             patch('pytesseract.image_to_data') as mock_ocr_data, \
             patch('PIL.Image.open') as mock_image:
            
            # Mock OCR data
            mock_ocr_data.return_value = {
                'text': ['This', 'is', 'text', 'extracted', 'from', 'an', 'image'],
                'conf': [95, 90, 88, 92, 85, 90, 87],
                'left': [10, 50, 90, 130, 200, 250, 290],
                'top': [10, 10, 10, 10, 10, 10, 10],
                'width': [30, 25, 30, 50, 35, 30, 40],
                'height': [15, 15, 15, 15, 15, 15, 15]
            }
            
            await prescan_algorithm._process_image_file(image_file, result)
            
            # Verify results
            assert result.pages is not None
            assert len(result.pages) > 0
            assert any("extracted from an image" in block.text for block in result.pages)
    
    @pytest.mark.asyncio
    async def test_detect_entities(self, prescan_algorithm):
        """Test entity detection functionality"""
        result = PreScanJSON(
            pages=[
                PreScanBlock(
                    type="text",
                    bbox=[0, 0, 100, 20],
                    text="John Smith met with Microsoft Corporation in New York",
                    confidence=0.9
                )
            ]
        )
        
        # Mock spaCy NLP
        mock_nlp = DICETestFixtures.create_mock_spacy_nlp()
        
        with patch('app.services.dice_algorithms.prescan_algorithm.HAS_SPACY', True):
            prescan_algorithm.nlp = mock_nlp
            
            await prescan_algorithm._detect_entities(result)
            
            # Verify entities were detected
            assert len(result.entities_detected) > 0
            assert "PERSON" in result.entities_detected
            assert "ORG" in result.entities_detected
    
    def test_calculate_overall_confidence(self, prescan_algorithm):
        """Test overall confidence calculation"""
        result = PreScanJSON(
            pages=[
                PreScanBlock(type="text", bbox=[0, 0, 100, 20], text="High confidence text", confidence=0.95),
                PreScanBlock(type="text", bbox=[0, 20, 100, 40], text="Medium confidence text", confidence=0.80),
                PreScanBlock(type="text", bbox=[0, 40, 100, 60], text="Low confidence text", confidence=0.60),
            ]
        )
        
        confidence = prescan_algorithm._calculate_overall_confidence(result)
        
        # Should be weighted average of confidences
        assert 0.6 <= confidence <= 0.95
        assert isinstance(confidence, float)
    
    @pytest.mark.asyncio
    async def test_download_file_from_s3(self, prescan_algorithm):
        """Test S3 file download functionality"""
        test_uri = "s3://test-bucket/test-file.pdf"
        mock_content = b"Mock file content"
        
        # Mock S3 client
        prescan_algorithm.s3_client.get_object.return_value = {
            'Body': MagicMock(read=MagicMock(return_value=mock_content))
        }
        
        result = await prescan_algorithm._download_file_from_s3(test_uri)
        
        assert result == mock_content
        prescan_algorithm.s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-file.pdf"
        )
    
    @pytest.mark.asyncio
    async def test_error_handling_unsupported_file(self, prescan_algorithm):
        """Test handling of unsupported file types"""
        unsupported_file = FileInfo(
            s3_uri="s3://test-bucket/test.xyz",
            mime_type="application/unknown",
            original_filename="test.xyz",
            file_size=1000
        )
        
        result = await prescan_algorithm.process_files([unsupported_file])
        
        # Should complete without errors but with minimal processing
        assert isinstance(result, PreScanJSON)
        assert result.ocr_confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_processing_performance(self, prescan_algorithm, sample_files):
        """Test that processing completes within expected time limits"""
        import time
        
        with patch.object(prescan_algorithm, '_process_pdf_file', new_callable=AsyncMock), \
             patch.object(prescan_algorithm, '_process_audio_file', new_callable=AsyncMock), \
             patch.object(prescan_algorithm, '_detect_entities', new_callable=AsyncMock), \
             patch.object(prescan_algorithm, '_calculate_overall_confidence', return_value=0.85):
            
            start_time = time.time()
            result = await prescan_algorithm.process_files(sample_files)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete within reasonable time
            assert processing_time < DICETestConstants.MAX_PRESCAN_TIME
            assert result.processing_time >= 0.0
    
    def test_initialization_with_missing_dependencies(self):
        """Test algorithm initialization when optional dependencies are missing"""
        with patch('app.services.dice_algorithms.prescan_algorithm.HAS_TESSERACT', False), \
             patch('app.services.dice_algorithms.prescan_algorithm.HAS_PDF', False), \
             patch('app.services.dice_algorithms.prescan_algorithm.HAS_AUDIO', False), \
             patch('app.services.dice_algorithms.prescan_algorithm.HAS_SPACY', False), \
             patch('app.services.dice_algorithms.prescan_algorithm.boto3.client'):
            
            # Should initialize without errors even with missing dependencies
            algorithm = PreScanAlgorithm()
            assert algorithm is not None
            assert algorithm.nlp is None
            assert algorithm.diarization_pipeline is None
    
    @pytest.mark.asyncio
    async def test_concurrent_file_processing(self, prescan_algorithm):
        """Test processing multiple files concurrently"""
        files = [
            DICETestFixtures.create_sample_file_info(),
            DICETestFixtures.create_sample_audio_file_info(),
            FileInfo(
                s3_uri="s3://test-bucket/test2.pdf",
                mime_type="application/pdf",
                original_filename="test2.pdf",
                file_size=2048000
            )
        ]
        
        with patch.object(prescan_algorithm, '_process_pdf_file', new_callable=AsyncMock) as mock_pdf, \
             patch.object(prescan_algorithm, '_process_audio_file', new_callable=AsyncMock) as mock_audio, \
             patch.object(prescan_algorithm, '_detect_entities', new_callable=AsyncMock), \
             patch.object(prescan_algorithm, '_calculate_overall_confidence', return_value=0.85):
            
            result = await prescan_algorithm.process_files(files)
            
            # Should process all PDF files
            assert mock_pdf.call_count == 2
            assert mock_audio.call_count == 1
            assert isinstance(result, PreScanJSON)
    
    @pytest.mark.asyncio
    async def test_confidence_thresholds(self, prescan_algorithm):
        """Test that confidence scores meet minimum thresholds"""
        files = [DICETestFixtures.create_sample_file_info()]
        
        with patch.object(prescan_algorithm, '_process_pdf_file', new_callable=AsyncMock), \
             patch.object(prescan_algorithm, '_detect_entities', new_callable=AsyncMock), \
             patch.object(prescan_algorithm, '_calculate_overall_confidence', return_value=0.75):
            
            result = await prescan_algorithm.process_files(files)
            
            # Confidence should meet minimum threshold
            assert result.ocr_confidence >= DICETestConstants.MIN_OCR_CONFIDENCE


@pytest.mark.integration
class TestPreScanAlgorithmIntegration:
    """Integration tests for PreScan Algorithm with real dependencies"""
    
    @pytest.mark.skipif(not os.environ.get('RUN_INTEGRATION_TESTS'), 
                       reason="Integration tests require environment setup")
    @pytest.mark.asyncio
    async def test_real_pdf_processing(self):
        """Test with a real PDF file (requires test environment)"""
        # This would test with actual PDF processing
        # Requires test files and proper environment setup
        pass
    
    @pytest.mark.skipif(not os.environ.get('RUN_INTEGRATION_TESTS'),
                       reason="Integration tests require environment setup")
    @pytest.mark.asyncio
    async def test_real_audio_processing(self):
        """Test with a real audio file (requires test environment)"""
        # This would test with actual audio processing
        # Requires test files and proper environment setup
        pass
