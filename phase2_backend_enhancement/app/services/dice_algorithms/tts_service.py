"""
DICE™ TTS Service
Text-to-Speech generation for meeting summaries and full transcripts

Supports multiple TTS providers with high-quality voice synthesis
"""

import asyncio
import logging
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

# OpenAI TTS
try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ElevenLabs TTS
try:
    import elevenlabs
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False

# AWS Polly
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_AWS_POLLY = True
except ImportError:
    HAS_AWS_POLLY = False

# Audio processing
try:
    import pydub
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

from app.schemas.dice_schemas import FinalMinutes, TranscriptSegment
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TTSService:
    """
    Text-to-Speech service for DICE™
    
    Generates high-quality audio narration for:
    - Executive summaries
    - Full meeting transcripts
    - Key decisions and action items
    """
    
    def __init__(self):
        """Initialize TTS service with available providers"""
        
        # OpenAI TTS
        self.openai_client = None
        if HAS_OPENAI and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # ElevenLabs
        self.elevenlabs_api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
        if self.elevenlabs_api_key and HAS_ELEVENLABS:
            elevenlabs.set_api_key(self.elevenlabs_api_key)
        
        # AWS Polly
        self.polly_client = None
        if HAS_AWS_POLLY:
            try:
                self.polly_client = boto3.client(
                    'polly',
                    aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                    aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
            except Exception as e:
                logger.warning(f"Could not initialize AWS Polly: {e}")
        
        # S3 for storing audio files
        self.s3_client = None
        if HAS_AWS_POLLY:  # Reuse AWS setup
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                    aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
            except Exception as e:
                logger.warning(f"Could not initialize S3 client: {e}")
        
        # Voice configurations
        self.voice_configs = {
            "openai": {
                "alloy": {"provider": "openai", "voice": "alloy", "quality": "hd"},
                "echo": {"provider": "openai", "voice": "echo", "quality": "hd"},
                "fable": {"provider": "openai", "voice": "fable", "quality": "hd"},
                "onyx": {"provider": "openai", "voice": "onyx", "quality": "hd"},
                "nova": {"provider": "openai", "voice": "nova", "quality": "hd"},
                "shimmer": {"provider": "openai", "voice": "shimmer", "quality": "hd"}
            },
            "elevenlabs": {
                "rachel": {"provider": "elevenlabs", "voice_id": "21m00Tcm4TlvDq8ikWAM"},
                "drew": {"provider": "elevenlabs", "voice_id": "29vD33N1CtxCmqQRPOHJ"},
                "bella": {"provider": "elevenlabs", "voice_id": "EXAVITQu4vr4xnSDxMaL"},
                "antoni": {"provider": "elevenlabs", "voice_id": "ErXwobaYiN019PkySvjV"}
            },
            "polly": {
                "joanna": {"provider": "polly", "voice_id": "Joanna", "engine": "neural"},
                "matthew": {"provider": "polly", "voice_id": "Matthew", "engine": "neural"},
                "amy": {"provider": "polly", "voice_id": "Amy", "engine": "neural"},
                "brian": {"provider": "polly", "voice_id": "Brian", "engine": "neural"}
            }
        }
    
    async def generate_audio(
        self, 
        final_minutes: FinalMinutes,
        voice_config: str = "alloy",
        include_full_transcript: bool = False
    ) -> Dict[str, str]:
        """
        Generate TTS audio for meeting minutes
        
        Args:
            final_minutes: Final meeting minutes
            voice_config: Voice configuration to use
            include_full_transcript: Whether to generate full transcript audio
            
        Returns:
            Dictionary with URLs to generated audio files
        """
        results = {}
        
        try:
            # Generate summary audio
            summary_audio_url = await self._generate_summary_audio(
                final_minutes, voice_config
            )
            if summary_audio_url:
                results["summary_audio_url"] = summary_audio_url
            
            # Generate key points audio
            key_points_audio_url = await self._generate_key_points_audio(
                final_minutes, voice_config
            )
            if key_points_audio_url:
                results["key_points_audio_url"] = key_points_audio_url
            
            # Generate full transcript audio if requested
            if include_full_transcript:
                transcript_audio_url = await self._generate_transcript_audio(
                    final_minutes, voice_config
                )
                if transcript_audio_url:
                    results["transcript_audio_url"] = transcript_audio_url
            
            logger.info(f"Generated {len(results)} audio files for meeting minutes")
            return results
            
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            raise
    
    async def _generate_summary_audio(
        self, 
        final_minutes: FinalMinutes, 
        voice_config: str
    ) -> Optional[str]:
        """Generate audio for executive summary"""
        
        # Create narration script
        script = self._create_summary_script(final_minutes)
        
        if not script.strip():
            return None
        
        try:
            # Generate audio
            audio_data = await self._synthesize_speech(script, voice_config)
            
            if not audio_data:
                return None
            
            # Upload to S3 and return URL
            file_key = f"dice-audio/{final_minutes.title.replace(' ', '_')}_summary_{uuid.uuid4().hex[:8]}.mp3"
            audio_url = await self._upload_audio_to_s3(audio_data, file_key)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Error generating summary audio: {e}")
            return None
    
    async def _generate_key_points_audio(
        self, 
        final_minutes: FinalMinutes, 
        voice_config: str
    ) -> Optional[str]:
        """Generate audio for key decisions and action items"""
        
        # Create key points script
        script = self._create_key_points_script(final_minutes)
        
        if not script.strip():
            return None
        
        try:
            # Generate audio
            audio_data = await self._synthesize_speech(script, voice_config)
            
            if not audio_data:
                return None
            
            # Upload to S3 and return URL
            file_key = f"dice-audio/{final_minutes.title.replace(' ', '_')}_keypoints_{uuid.uuid4().hex[:8]}.mp3"
            audio_url = await self._upload_audio_to_s3(audio_data, file_key)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Error generating key points audio: {e}")
            return None
    
    async def _generate_transcript_audio(
        self, 
        final_minutes: FinalMinutes, 
        voice_config: str
    ) -> Optional[str]:
        """Generate audio for full transcript"""
        
        # Create transcript script
        script = self._create_transcript_script(final_minutes)
        
        if not script.strip():
            return None
        
        # For long transcripts, we might need to split into chunks
        max_chunk_length = 4000  # characters
        if len(script) > max_chunk_length:
            return await self._generate_chunked_transcript_audio(
                final_minutes, voice_config, max_chunk_length
            )
        
        try:
            # Generate audio
            audio_data = await self._synthesize_speech(script, voice_config)
            
            if not audio_data:
                return None
            
            # Upload to S3 and return URL
            file_key = f"dice-audio/{final_minutes.title.replace(' ', '_')}_transcript_{uuid.uuid4().hex[:8]}.mp3"
            audio_url = await self._upload_audio_to_s3(audio_data, file_key)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Error generating transcript audio: {e}")
            return None
    
    async def _generate_chunked_transcript_audio(
        self, 
        final_minutes: FinalMinutes, 
        voice_config: str,
        max_chunk_length: int
    ) -> Optional[str]:
        """Generate audio for long transcript by chunking"""
        
        if not HAS_PYDUB:
            logger.warning("pydub not available for audio concatenation")
            return None
        
        script = self._create_transcript_script(final_minutes)
        
        # Split script into chunks at sentence boundaries
        chunks = self._split_script_into_chunks(script, max_chunk_length)
        
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Generate audio for chunk
                audio_data = await self._synthesize_speech(chunk, voice_config)
                
                if audio_data:
                    # Convert to AudioSegment
                    with tempfile.NamedTemporaryFile(suffix='.mp3') as temp_file:
                        temp_file.write(audio_data)
                        temp_file.flush()
                        
                        audio_segment = AudioSegment.from_mp3(temp_file.name)
                        audio_segments.append(audio_segment)
                        
                        # Add short pause between chunks
                        if i < len(chunks) - 1:
                            pause = AudioSegment.silent(duration=500)  # 500ms pause
                            audio_segments.append(pause)
                
            except Exception as e:
                logger.error(f"Error generating chunk {i}: {e}")
                continue
        
        if not audio_segments:
            return None
        
        try:
            # Concatenate all segments
            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio += segment
            
            # Export to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                final_audio.export(temp_file.name, format="mp3")
                
                # Read back the audio data
                with open(temp_file.name, 'rb') as f:
                    combined_audio_data = f.read()
                
                # Clean up
                Path(temp_file.name).unlink(missing_ok=True)
            
            # Upload combined audio
            file_key = f"dice-audio/{final_minutes.title.replace(' ', '_')}_transcript_{uuid.uuid4().hex[:8]}.mp3"
            audio_url = await self._upload_audio_to_s3(combined_audio_data, file_key)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Error combining audio chunks: {e}")
            return None
    
    def _split_script_into_chunks(self, script: str, max_length: int) -> List[str]:
        """Split script into chunks at sentence boundaries"""
        
        # Split into sentences
        sentences = [s.strip() + "." for s in script.split('.') if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed limit
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split it
                    chunks.append(sentence[:max_length])
                    current_chunk = sentence[max_length:]
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _synthesize_speech(self, text: str, voice_config: str) -> Optional[bytes]:
        """Synthesize speech using the best available provider"""
        
        # Determine provider and voice settings
        voice_settings = self._get_voice_settings(voice_config)
        
        if voice_settings["provider"] == "openai" and self.openai_client:
            return await self._synthesize_openai(text, voice_settings)
        elif voice_settings["provider"] == "elevenlabs" and self.elevenlabs_api_key:
            return await self._synthesize_elevenlabs(text, voice_settings)
        elif voice_settings["provider"] == "polly" and self.polly_client:
            return await self._synthesize_polly(text, voice_settings)
        else:
            # Fallback to any available provider
            if self.openai_client:
                return await self._synthesize_openai(text, {"voice": "alloy", "quality": "hd"})
            elif self.polly_client:
                return await self._synthesize_polly(text, {"voice_id": "Joanna", "engine": "neural"})
            else:
                logger.error("No TTS providers available")
                return None
    
    def _get_voice_settings(self, voice_config: str) -> Dict[str, Any]:
        """Get voice settings for the specified configuration"""
        
        # Check each provider for the voice config
        for provider, voices in self.voice_configs.items():
            if voice_config in voices:
                return voices[voice_config]
        
        # Default to OpenAI alloy
        return {"provider": "openai", "voice": "alloy", "quality": "hd"}
    
    async def _synthesize_openai(self, text: str, voice_settings: Dict[str, Any]) -> Optional[bytes]:
        """Synthesize speech using OpenAI TTS"""
        
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd" if voice_settings.get("quality") == "hd" else "tts-1",
                voice=voice_settings.get("voice", "alloy"),
                input=text,
                response_format="mp3"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return None
    
    async def _synthesize_elevenlabs(self, text: str, voice_settings: Dict[str, Any]) -> Optional[bytes]:
        """Synthesize speech using ElevenLabs"""
        
        if not HAS_ELEVENLABS:
            return None
        
        try:
            audio = elevenlabs.generate(
                text=text,
                voice=voice_settings.get("voice_id", "21m00Tcm4TlvDq8ikWAM"),
                model="eleven_monolingual_v1"
            )
            
            return audio
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None
    
    async def _synthesize_polly(self, text: str, voice_settings: Dict[str, Any]) -> Optional[bytes]:
        """Synthesize speech using AWS Polly"""
        
        try:
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_settings.get("voice_id", "Joanna"),
                Engine=voice_settings.get("engine", "neural")
            )
            
            return response['AudioStream'].read()
            
        except Exception as e:
            logger.error(f"AWS Polly TTS error: {e}")
            return None
    
    async def _upload_audio_to_s3(self, audio_data: bytes, file_key: str) -> Optional[str]:
        """Upload audio file to S3 and return public URL"""
        
        if not self.s3_client:
            logger.warning("S3 client not available for audio upload")
            return None
        
        try:
            bucket_name = getattr(settings, 'AWS_S3_BUCKET', 'iam-dice-audio')
            
            # Upload file
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=audio_data,
                ContentType='audio/mpeg',
                ACL='public-read'
            )
            
            # Generate public URL
            url = f"https://{bucket_name}.s3.{getattr(settings, 'AWS_REGION', 'us-east-1')}.amazonaws.com/{file_key}"
            
            logger.info(f"Uploaded audio file to S3: {file_key}")
            return url
            
        except Exception as e:
            logger.error(f"Error uploading audio to S3: {e}")
            return None
    
    def _create_summary_script(self, final_minutes: FinalMinutes) -> str:
        """Create narration script for executive summary"""
        
        script_parts = [
            f"Meeting Summary: {final_minutes.title}",
            "",
            final_minutes.executive_summary
        ]
        
        return " ".join(script_parts)
    
    def _create_key_points_script(self, final_minutes: FinalMinutes) -> str:
        """Create narration script for key decisions and action items"""
        
        script_parts = [
            f"Key Points from {final_minutes.title}",
            ""
        ]
        
        # Add decisions
        if final_minutes.decisions:
            script_parts.append("Decisions made:")
            for i, decision in enumerate(final_minutes.decisions, 1):
                script_parts.append(f"{i}. {decision.decision}")
        
        # Add action items
        if final_minutes.action_items:
            script_parts.append("Action items:")
            for i, action in enumerate(final_minutes.action_items, 1):
                owner_text = f" assigned to {action.owner}" if action.owner != "TBD" else ""
                due_text = f" due {action.due_date}" if action.due_date else ""
                script_parts.append(f"{i}. {action.item}{owner_text}{due_text}")
        
        return " ".join(script_parts)
    
    def _create_transcript_script(self, final_minutes: FinalMinutes) -> str:
        """Create narration script for full transcript"""
        
        script_parts = [
            f"Full transcript of {final_minutes.title}",
            ""
        ]
        
        # Add transcript segments
        current_speaker = None
        for segment in final_minutes.full_transcript:
            if segment.speaker != current_speaker:
                script_parts.append(f"{segment.speaker} says:")
                current_speaker = segment.speaker
            
            script_parts.append(segment.text)
        
        return " ".join(script_parts)




