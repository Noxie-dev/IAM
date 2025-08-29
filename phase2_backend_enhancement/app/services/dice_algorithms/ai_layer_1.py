"""
DICE™ AI Layer 1: Draft Transcript Generation
Advanced AI-powered transcript generation using OpenAI Whisper and GPT-4o

Handles audio transcription, document-to-transcript conversion, and initial summarization
"""

import asyncio
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import io

# OpenAI
try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Audio processing
try:
    import librosa
    import soundfile as sf
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

import boto3
from botocore.exceptions import ClientError

from app.schemas.dice_schemas import (
    FileInfo, PreScanJSON, DraftTranscriptJSON, TranscriptSegment
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AILayer1:
    """
    AI Layer 1: Draft Transcript Generation
    
    Uses advanced AI models to generate initial transcript drafts from:
    - Audio files (via Whisper)
    - Document text (via GPT-4o conversion to meeting format)
    - Multi-modal content (combining audio and document context)
    """
    
    def __init__(self):
        """Initialize AI Layer 1 with OpenAI client"""
        self.openai_client = None
        if HAS_OPENAI and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
    
    async def generate_draft_transcript(
        self, 
        files: List[FileInfo], 
        prescan_result: PreScanJSON
    ) -> DraftTranscriptJSON:
        """
        Generate draft transcript from files and pre-scan results
        
        Args:
            files: List of input files
            prescan_result: Results from pre-scan algorithm
            
        Returns:
            DraftTranscriptJSON with initial transcript
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        # Determine primary content type
        audio_files = [f for f in files if f.mime_type.startswith('audio/')]
        document_files = [f for f in files if not f.mime_type.startswith('audio/')]
        
        if audio_files:
            # Audio-first processing
            return await self._process_audio_primary(audio_files, document_files, prescan_result)
        elif document_files:
            # Document-only processing
            return await self._process_document_only(document_files, prescan_result)
        else:
            raise ValueError("No processable files found")
    
    async def _process_audio_primary(
        self, 
        audio_files: List[FileInfo], 
        document_files: List[FileInfo],
        prescan_result: PreScanJSON
    ) -> DraftTranscriptJSON:
        """Process with audio as primary source"""
        
        segments = []
        total_confidence = 0.0
        
        for audio_file in audio_files:
            try:
                # Transcribe audio with Whisper
                audio_segments = await self._transcribe_audio_file(audio_file, prescan_result)
                segments.extend(audio_segments)
                
            except Exception as e:
                logger.error(f"Error transcribing audio file {audio_file.original_filename}: {e}")
                continue
        
        if not segments:
            raise ValueError("No audio could be transcribed")
        
        # Calculate confidence
        total_confidence = sum(seg.confidence for seg in segments) / len(segments) if segments else 0.0
        
        # Enhance with document context if available
        if document_files and prescan_result.pages:
            segments = await self._enhance_with_document_context(segments, prescan_result)
        
        # Generate summary and action items
        summary, action_items, key_topics = await self._generate_initial_analysis(segments)
        
        return DraftTranscriptJSON(
            language="en",  # TODO: Detect language
            segments=segments,
            summary=summary,
            action_items=action_items,
            key_topics=key_topics,
            model_used="whisper-1",
            ai_provider="openai",
            confidence=total_confidence
        )
    
    async def _process_document_only(
        self, 
        document_files: List[FileInfo], 
        prescan_result: PreScanJSON
    ) -> DraftTranscriptJSON:
        """Process document-only content by converting to meeting transcript format"""
        
        if not prescan_result.pages:
            raise ValueError("No text content found in documents")
        
        # Combine all document text
        combined_text = ""
        for page in prescan_result.pages:
            combined_text += page.text + "\n\n"
        
        # Convert document to transcript format using GPT-4o
        segments = await self._convert_document_to_transcript(combined_text)
        
        # Generate analysis
        summary, action_items, key_topics = await self._generate_initial_analysis(segments)
        
        return DraftTranscriptJSON(
            language="en",
            segments=segments,
            summary=summary,
            action_items=action_items,
            key_topics=key_topics,
            model_used="gpt-4o",
            ai_provider="openai",
            confidence=0.85  # Lower confidence for document conversion
        )
    
    async def _transcribe_audio_file(
        self, 
        audio_file: FileInfo, 
        prescan_result: PreScanJSON
    ) -> List[TranscriptSegment]:
        """Transcribe audio file using OpenAI Whisper"""
        
        try:
            # Download audio file
            audio_data = await self._download_file_from_s3(audio_file.s3_uri)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Transcribe with Whisper
                with open(temp_path, 'rb') as audio_fp:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_fp,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                
                # Convert to TranscriptSegment objects
                segments = []
                for i, segment in enumerate(transcript.segments):
                    # Use pre-scan speaker hints if available
                    speaker = self._assign_speaker(segment, prescan_result, i)
                    
                    ts = TranscriptSegment(
                        speaker=speaker,
                        start_time=segment['start'],
                        end_time=segment['end'],
                        text=segment['text'].strip(),
                        confidence=getattr(segment, 'avg_logprob', 0.8)
                    )
                    segments.append(ts)
                
                logger.info(f"Transcribed audio: {len(segments)} segments")
                return segments
                
            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)
        
        except Exception as e:
            logger.error(f"Error in audio transcription: {e}")
            raise
    
    def _assign_speaker(
        self, 
        segment: Dict[str, Any], 
        prescan_result: PreScanJSON, 
        segment_index: int
    ) -> str:
        """Assign speaker to segment using pre-scan diarization hints"""
        
        # Use pre-scan audio segments if available
        if prescan_result.audio_segments:
            segment_time = segment['start']
            
            # Find matching audio segment
            for audio_seg in prescan_result.audio_segments:
                if audio_seg.start_time <= segment_time <= audio_seg.end_time:
                    return audio_seg.speaker_hint or f"Speaker_{(segment_index % 3) + 1}"
        
        # Default speaker assignment
        return f"Speaker_{(segment_index % 3) + 1}"
    
    async def _enhance_with_document_context(
        self, 
        segments: List[TranscriptSegment], 
        prescan_result: PreScanJSON
    ) -> List[TranscriptSegment]:
        """Enhance transcript segments with document context"""
        
        if not prescan_result.pages:
            return segments
        
        # Extract document context
        document_text = ""
        for page in prescan_result.pages:
            document_text += page.text + "\n"
        
        if not document_text.strip():
            return segments
        
        try:
            # Use GPT-4o to enhance transcript with document context
            prompt = self._build_enhancement_prompt(segments, document_text)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert transcript enhancer. Use the provided document context to improve transcript accuracy, especially for names, technical terms, and specific details."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse enhanced transcript
            enhanced_segments = self._parse_enhanced_transcript(
                response.choices[0].message.content, 
                segments
            )
            
            return enhanced_segments
            
        except Exception as e:
            logger.error(f"Error enhancing transcript with document context: {e}")
            return segments  # Return original on error
    
    def _build_enhancement_prompt(
        self, 
        segments: List[TranscriptSegment], 
        document_text: str
    ) -> str:
        """Build prompt for transcript enhancement"""
        
        # Convert segments to text
        transcript_text = ""
        for seg in segments:
            transcript_text += f"[{seg.speaker}] {seg.text}\n"
        
        prompt = f"""
Please enhance this meeting transcript using the provided document context. 
Focus on correcting names, technical terms, and specific details that might have been misheard.

DOCUMENT CONTEXT:
{document_text[:2000]}...

ORIGINAL TRANSCRIPT:
{transcript_text[:2000]}...

Please provide the enhanced transcript in the same format, maintaining the speaker labels and timing structure.
Only make corrections where you're confident the document provides better context.
"""
        
        return prompt
    
    def _parse_enhanced_transcript(
        self, 
        enhanced_text: str, 
        original_segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        """Parse enhanced transcript back to segments"""
        
        # Simple parsing - in production, this would be more sophisticated
        lines = enhanced_text.strip().split('\n')
        enhanced_segments = []
        
        for i, line in enumerate(lines):
            if line.strip() and '[' in line and ']' in line:
                try:
                    # Extract speaker and text
                    speaker_end = line.find(']')
                    speaker = line[1:speaker_end]
                    text = line[speaker_end + 1:].strip()
                    
                    # Use original timing if available
                    if i < len(original_segments):
                        original = original_segments[i]
                        enhanced_seg = TranscriptSegment(
                            speaker=speaker,
                            start_time=original.start_time,
                            end_time=original.end_time,
                            text=text,
                            confidence=original.confidence
                        )
                        enhanced_segments.append(enhanced_seg)
                        
                except Exception:
                    continue
        
        # Return original if parsing failed
        if len(enhanced_segments) < len(original_segments) * 0.8:
            logger.warning("Enhancement parsing failed, returning original transcript")
            return original_segments
        
        return enhanced_segments
    
    async def _convert_document_to_transcript(self, document_text: str) -> List[TranscriptSegment]:
        """Convert document text to meeting transcript format"""
        
        try:
            prompt = f"""
Convert this meeting document/notes into a realistic meeting transcript format with speakers.
Create natural dialogue that represents how this content would have been discussed in a meeting.

DOCUMENT CONTENT:
{document_text[:3000]}...

Please format as:
[Speaker_1] Opening statement or introduction...
[Speaker_2] Response or questions...
[Speaker_1] Further discussion...

Make it natural and conversational while preserving all key information.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at converting meeting documents into realistic transcript format. Create natural dialogue that preserves all important information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            # Parse the generated transcript
            transcript_text = response.choices[0].message.content
            segments = self._parse_generated_transcript(transcript_text)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error converting document to transcript: {e}")
            raise
    
    def _parse_generated_transcript(self, transcript_text: str) -> List[TranscriptSegment]:
        """Parse generated transcript into segments"""
        
        lines = transcript_text.strip().split('\n')
        segments = []
        current_time = 0.0
        
        for line in lines:
            if line.strip() and '[' in line and ']' in line:
                try:
                    # Extract speaker and text
                    speaker_end = line.find(']')
                    speaker = line[1:speaker_end]
                    text = line[speaker_end + 1:].strip()
                    
                    if text:
                        # Estimate duration based on text length (rough: ~150 words per minute)
                        word_count = len(text.split())
                        duration = max(2.0, word_count * 0.4)  # Minimum 2 seconds
                        
                        segment = TranscriptSegment(
                            speaker=speaker,
                            start_time=current_time,
                            end_time=current_time + duration,
                            text=text,
                            confidence=0.8  # Moderate confidence for generated content
                        )
                        
                        segments.append(segment)
                        current_time += duration + 0.5  # Small pause between speakers
                        
                except Exception:
                    continue
        
        return segments
    
    async def _generate_initial_analysis(
        self, 
        segments: List[TranscriptSegment]
    ) -> tuple[str, List[str], List[str]]:
        """Generate summary, action items, and key topics"""
        
        # Combine all transcript text
        full_text = " ".join(seg.text for seg in segments)
        
        if not full_text.strip():
            return "", [], []
        
        try:
            prompt = f"""
Analyze this meeting transcript and provide:
1. A concise summary (2-3 sentences)
2. Action items (specific tasks with owners if mentioned)
3. Key topics discussed

TRANSCRIPT:
{full_text[:4000]}...

Format your response as JSON:
{{
    "summary": "Brief meeting summary...",
    "action_items": ["Action 1", "Action 2", ...],
    "key_topics": ["Topic 1", "Topic 2", ...]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting analyst. Provide accurate, concise analysis in the requested JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse JSON response
            analysis = json.loads(response.choices[0].message.content)
            
            return (
                analysis.get("summary", ""),
                analysis.get("action_items", []),
                analysis.get("key_topics", [])
            )
            
        except Exception as e:
            logger.error(f"Error generating initial analysis: {e}")
            return "", [], []
    
    async def _download_file_from_s3(self, s3_uri: str) -> bytes:
        """Download file content from S3"""
        try:
            # Parse S3 URI
            s3_parts = s3_uri.replace('s3://', '').split('/', 1)
            bucket = s3_parts[0]
            key = s3_parts[1]
            
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            raise



