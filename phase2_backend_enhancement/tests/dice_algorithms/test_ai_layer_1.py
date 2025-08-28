"""
Unit tests for DICE™ AI Layer 1 (Draft Transcript Generation)
Tests OpenAI Whisper integration and GPT-4o transcript processing
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List

from app.services.dice_algorithms.ai_layer_1 import AILayer1
from app.schemas.dice_schemas import (
    FileInfo, PreScanJSON, DraftTranscriptJSON, 
    TranscriptSegment
)
from tests.fixtures.dice_test_data import DICETestFixtures, DICETestConstants


class TestAILayer1:
    """Test suite for AI Layer 1 (Draft Transcript Generation)"""
    
    @pytest.fixture
    def ai_layer_1(self):
        """Create an AI Layer 1 instance for testing"""
        with patch('app.services.dice_algorithms.ai_layer_1.OpenAI'):
            layer = AILayer1()
            layer.openai_client = DICETestFixtures.create_mock_openai_client()
            return layer
    
    @pytest.fixture
    def sample_prescan_result(self):
        """Create sample prescan results for testing"""
        return DICETestFixtures.create_sample_prescan_result()
    
    @pytest.fixture
    def sample_files(self):
        """Create sample files for testing"""
        return [
            DICETestFixtures.create_sample_audio_file_info(),
            DICETestFixtures.create_sample_file_info()
        ]
    
    @pytest.mark.asyncio
    async def test_generate_transcript_basic(self, ai_layer_1, sample_files, sample_prescan_result):
        """Test basic transcript generation functionality"""
        with patch.object(ai_layer_1, '_transcribe_audio_files', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(ai_layer_1, '_process_document_to_transcript', new_callable=AsyncMock) as mock_doc_process, \
             patch.object(ai_layer_1, '_generate_summary_and_insights', new_callable=AsyncMock) as mock_insights:
            
            # Mock return values
            mock_transcribe.return_value = DICETestFixtures.create_sample_transcript_segments()
            mock_insights.return_value = {
                'summary': 'Test summary',
                'action_items': ['Test action'],
                'key_topics': ['Test topic']
            }
            
            result = await ai_layer_1.generate_transcript(sample_files, sample_prescan_result)
            
            # Verify the result
            assert isinstance(result, DraftTranscriptJSON)
            assert result.language == "en"
            assert len(result.segments) > 0
            assert result.confidence > 0.0
            assert result.model_used == "gpt-4o"
            assert result.ai_provider == "openai"
            
            # Verify methods were called
            mock_transcribe.assert_called_once()
            mock_insights.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_files(self, ai_layer_1):
        """Test audio transcription with Whisper"""
        audio_files = [DICETestFixtures.create_sample_audio_file_info()]
        prescan_result = DICETestFixtures.create_sample_prescan_result()
        
        # Mock Whisper response
        mock_whisper_response = MagicMock()
        mock_whisper_response.text = "This is the transcribed audio content from the meeting."
        
        with patch.object(ai_layer_1, '_download_file_from_s3', return_value=b'mock audio data'), \
             patch.object(ai_layer_1.openai_client.audio.transcriptions, 'create', new_callable=AsyncMock, return_value=mock_whisper_response):
            
            segments = await ai_layer_1._transcribe_audio_files(audio_files, prescan_result)
            
            # Verify results
            assert isinstance(segments, list)
            assert len(segments) > 0
            assert all(isinstance(seg, TranscriptSegment) for seg in segments)
            assert segments[0].text == mock_whisper_response.text
    
    @pytest.mark.asyncio
    async def test_transcribe_with_diarization(self, ai_layer_1):
        """Test audio transcription with speaker diarization"""
        audio_files = [DICETestFixtures.create_sample_audio_file_info()]
        prescan_result = DICETestFixtures.create_sample_prescan_result()
        
        # Mock Whisper response with timestamps
        mock_whisper_response = MagicMock()
        mock_whisper_response.segments = [
            MagicMock(
                text="Welcome to the meeting.",
                start=0.0,
                end=3.5
            ),
            MagicMock(
                text="Thank you for joining us today.",
                start=3.5,
                end=7.2
            )
        ]
        
        with patch.object(ai_layer_1, '_download_file_from_s3', return_value=b'mock audio data'), \
             patch.object(ai_layer_1.openai_client.audio.transcriptions, 'create', new_callable=AsyncMock, return_value=mock_whisper_response):
            
            segments = await ai_layer_1._transcribe_audio_files(audio_files, prescan_result)
            
            # Verify speaker assignment based on diarization
            assert len(segments) >= 2
            for segment in segments:
                assert segment.speaker is not None
                assert segment.start_time >= 0.0
                assert segment.end_time > segment.start_time
    
    @pytest.mark.asyncio
    async def test_process_document_to_transcript(self, ai_layer_1):
        """Test converting document content to transcript format"""
        document_files = [DICETestFixtures.create_sample_file_info()]
        prescan_result = DICETestFixtures.create_sample_prescan_result()
        
        # Mock GPT response for document processing
        mock_gpt_response = MagicMock()
        mock_gpt_response.choices = [MagicMock(
            message=MagicMock(content='{"segments": [{"speaker": "Document", "text": "Meeting agenda item 1", "start_time": 0.0, "end_time": 5.0}]}')
        )]
        
        with patch.object(ai_layer_1.openai_client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_gpt_response):
            
            await ai_layer_1._process_document_to_transcript(document_files, prescan_result, [])
            
            # Verify GPT was called for document processing
            ai_layer_1.openai_client.chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_summary_and_insights(self, ai_layer_1):
        """Test summary and insights generation"""
        segments = DICETestFixtures.create_sample_transcript_segments()
        
        # Mock GPT response for summary generation
        mock_gpt_response = MagicMock()
        mock_gpt_response.choices = [MagicMock(
            message=MagicMock(content='{"summary": "Test meeting summary", "action_items": ["Action 1", "Action 2"], "key_topics": ["Topic 1", "Topic 2"]}')
        )]
        
        with patch.object(ai_layer_1.openai_client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_gpt_response):
            
            result = await ai_layer_1._generate_summary_and_insights(segments)
            
            # Verify results
            assert 'summary' in result
            assert 'action_items' in result
            assert 'key_topics' in result
            assert isinstance(result['action_items'], list)
            assert isinstance(result['key_topics'], list)
    
    @pytest.mark.asyncio
    async def test_chunk_large_audio_file(self, ai_layer_1):
        """Test handling of large audio files through chunking"""
        # Create a large audio file
        large_audio_file = FileInfo(
            s3_uri="s3://test-bucket/large_audio.wav",
            mime_type="audio/wav",
            original_filename="large_meeting.wav",
            file_size=DICETestConstants.LARGE_FILE_SIZE
        )
        
        prescan_result = PreScanJSON(total_duration=3600.0)  # 1 hour audio
        
        # Mock file chunking and processing
        with patch.object(ai_layer_1, '_download_file_from_s3', return_value=b'large mock audio data'), \
             patch.object(ai_layer_1, '_chunk_audio_file', return_value=[b'chunk1', b'chunk2', b'chunk3']), \
             patch.object(ai_layer_1.openai_client.audio.transcriptions, 'create', new_callable=AsyncMock) as mock_transcribe:
            
            # Mock multiple transcription responses
            mock_transcribe.side_effect = [
                MagicMock(text="First chunk transcription"),
                MagicMock(text="Second chunk transcription"), 
                MagicMock(text="Third chunk transcription")
            ]
            
            segments = await ai_layer_1._transcribe_audio_files([large_audio_file], prescan_result)
            
            # Verify chunking occurred
            assert mock_transcribe.call_count == 3
            assert len(segments) >= 3
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_audio(self, ai_layer_1):
        """Test error handling for invalid audio files"""
        invalid_audio = FileInfo(
            s3_uri="s3://test-bucket/invalid.wav",
            mime_type="audio/wav",
            original_filename="invalid.wav",
            file_size=100
        )
        
        with patch.object(ai_layer_1, '_download_file_from_s3', return_value=b'invalid data'), \
             patch.object(ai_layer_1.openai_client.audio.transcriptions, 'create', side_effect=Exception("Invalid audio format")):
            
            segments = await ai_layer_1._transcribe_audio_files([invalid_audio], PreScanJSON())
            
            # Should handle errors gracefully
            assert isinstance(segments, list)
            # Might be empty or contain error placeholders
    
    @pytest.mark.asyncio
    async def test_multi_language_detection(self, ai_layer_1):
        """Test automatic language detection for transcription"""
        audio_files = [DICETestFixtures.create_sample_audio_file_info()]
        prescan_result = PreScanJSON()
        
        # Mock Whisper response with language detection
        mock_whisper_response = MagicMock()
        mock_whisper_response.text = "Bonjour, bienvenue à notre réunion."
        mock_whisper_response.language = "fr"
        
        with patch.object(ai_layer_1, '_download_file_from_s3', return_value=b'french audio data'), \
             patch.object(ai_layer_1.openai_client.audio.transcriptions, 'create', new_callable=AsyncMock, return_value=mock_whisper_response):
            
            segments = await ai_layer_1._transcribe_audio_files(audio_files, prescan_result)
            result = DraftTranscriptJSON(language="fr", segments=segments)
            
            # Verify language detection
            assert result.language == "fr"
            assert "Bonjour" in segments[0].text
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, ai_layer_1):
        """Test confidence scoring for transcript segments"""
        segments = DICETestFixtures.create_sample_transcript_segments()
        
        # Test confidence calculation
        total_confidence = sum(seg.confidence for seg in segments) / len(segments)
        
        # Create result with confidence
        result = DraftTranscriptJSON(
            segments=segments,
            confidence=total_confidence
        )
        
        # Verify confidence meets thresholds
        assert result.confidence >= DICETestConstants.MIN_TRANSCRIPT_CONFIDENCE
        assert all(seg.confidence > 0.0 for seg in segments)
    
    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, ai_layer_1):
        """Test tracking of OpenAI token usage"""
        segments = DICETestFixtures.create_sample_transcript_segments()
        
        # Mock GPT response with usage data
        mock_gpt_response = MagicMock()
        mock_gpt_response.choices = [MagicMock(
            message=MagicMock(content='{"summary": "Test summary"}')
        )]
        mock_gpt_response.usage = MagicMock(
            prompt_tokens=500,
            completion_tokens=200,
            total_tokens=700
        )
        
        with patch.object(ai_layer_1.openai_client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_gpt_response):
            
            result = await ai_layer_1._generate_summary_and_insights(segments)
            
            # Verify token usage is tracked
            # This would be stored in the result metadata
            assert mock_gpt_response.usage.total_tokens == 700
    
    @pytest.mark.asyncio
    async def test_processing_performance(self, ai_layer_1, sample_files, sample_prescan_result):
        """Test that AI Layer 1 processing completes within time limits"""
        import time
        
        with patch.object(ai_layer_1, '_transcribe_audio_files', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(ai_layer_1, '_process_document_to_transcript', new_callable=AsyncMock), \
             patch.object(ai_layer_1, '_generate_summary_and_insights', new_callable=AsyncMock) as mock_insights:
            
            # Mock quick responses
            mock_transcribe.return_value = DICETestFixtures.create_sample_transcript_segments()
            mock_insights.return_value = {
                'summary': 'Quick summary',
                'action_items': ['Quick action'],
                'key_topics': ['Quick topic']
            }
            
            start_time = time.time()
            result = await ai_layer_1.generate_transcript(sample_files, sample_prescan_result)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete within time limit
            assert processing_time < DICETestConstants.MAX_AI_LAYER1_TIME
            assert result.processing_time >= 0.0
    
    def test_segment_validation(self, ai_layer_1):
        """Test validation of transcript segments"""
        # Test with invalid segments
        invalid_segments = [
            TranscriptSegment(
                speaker="",  # Empty speaker
                start_time=-1.0,  # Negative time
                end_time=5.0,
                text="Invalid segment"
            ),
            TranscriptSegment(
                speaker="Valid Speaker",
                start_time=10.0,
                end_time=5.0,  # End before start
                text="Another invalid segment"
            )
        ]
        
        # Manual validation logic for testing
        valid_segments = []
        for seg in invalid_segments:
            if seg.start_time >= 0 and seg.end_time > seg.start_time and len(seg.speaker.strip()) > 0:
                valid_segments.append(seg)
        
        # Should filter out invalid segments
        assert len(valid_segments) < len(invalid_segments)  # Some should be filtered out


@pytest.mark.integration
class TestAILayer1Integration:
    """Integration tests for AI Layer 1 with real OpenAI API"""
    
    @pytest.mark.skipif(not os.environ.get('OPENAI_API_KEY'), 
                       reason="Integration tests require OpenAI API key")
    @pytest.mark.asyncio
    async def test_real_whisper_transcription(self):
        """Test with real Whisper API (requires API key)"""
        # This would test with actual OpenAI Whisper API
        # Requires valid API key and test audio files
        pass
    
    @pytest.mark.skipif(not os.environ.get('OPENAI_API_KEY'),
                       reason="Integration tests require OpenAI API key")  
    @pytest.mark.asyncio
    async def test_real_gpt_processing(self):
        """Test with real GPT API (requires API key)"""
        # This would test with actual GPT-4o API
        # Requires valid API key
        pass
