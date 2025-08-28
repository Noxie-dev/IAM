"""
Transcription Service
Phase 2: Backend Enhancement

Multi-provider transcription service with retry logic and error handling
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Azure Speech
try:
    import azure.cognitiveservices.speech as speechsdk
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

# Google Speech
try:
    from google.cloud import speech
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

from app.core.config import get_settings
from app.models.meeting import Meeting

logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Multi-provider transcription service with retry logic
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Initialize clients
        self.openai_client = None
        if HAS_OPENAI and self.settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        
        # Log available providers
        providers = []
        if self.openai_client:
            providers.append("OpenAI")
        if HAS_AZURE:
            providers.append("Azure")
        if HAS_GOOGLE:
            providers.append("Google")
        
        logger.info(f"Transcription service initialized with providers: {', '.join(providers) if providers else 'None'}")
    
    async def transcribe_audio(
        self,
        audio_path: str,
        meeting: Meeting,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using configured provider
        
        Args:
            audio_path: Path to audio file
            meeting: Meeting object with transcription settings
            max_retries: Maximum retry attempts
        
        Returns:
            Transcription result dictionary
        """
        settings = meeting.transcription_settings or {}
        provider = settings.get("provider", "openai")
        
        # Run transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._transcribe_with_retry,
            audio_path,
            provider,
            settings,
            max_retries
        )
        
        return result
    
    def _transcribe_with_retry(
        self,
        audio_path: str,
        provider: str,
        settings: Dict[str, Any],
        max_retries: int
    ) -> Dict[str, Any]:
        """
        Transcribe with retry logic
        
        Args:
            audio_path: Path to audio file
            provider: Transcription provider
            settings: Transcription settings
            max_retries: Maximum retry attempts
        
        Returns:
            Transcription result dictionary
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Transcription attempt {attempt + 1}/{max_retries} using {provider}")
                
                if provider == "openai":
                    return self._transcribe_openai(audio_path, settings)
                elif provider == "azure":
                    return self._transcribe_azure(audio_path, settings)
                elif provider == "google":
                    return self._transcribe_google(audio_path, settings)
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported provider: {provider}"
                    }
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Transcription attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = 2 ** attempt
                    logger.info(f"Retrying in {delay} seconds...")
                    asyncio.sleep(delay)
        
        return {
            "success": False,
            "error": f"Transcription failed after {max_retries} attempts: {last_error}"
        }
    
    def _transcribe_openai(self, audio_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper"""
        if not self.openai_client:
            return {
                "success": False,
                "error": "OpenAI client not configured"
            }
        
        try:
            model = settings.get("model", "whisper-1")
            language = settings.get("language", "auto")
            timestamps = settings.get("timestamps", True)
            
            with open(audio_path, 'rb') as audio_file:
                # Determine response format
                if timestamps:
                    response_format = "verbose_json"
                else:
                    response_format = "text"
                
                # Prepare transcription parameters
                transcription_params = {
                    "model": model,
                    "file": audio_file,
                    "response_format": response_format
                }
                
                # Add language if not auto-detect
                if language and language != "auto":
                    transcription_params["language"] = language
                
                # Call OpenAI API
                transcript = self.openai_client.audio.transcriptions.create(**transcription_params)
                
                if response_format == "verbose_json":
                    return {
                        "success": True,
                        "text": transcript.text,
                        "segments": transcript.segments if hasattr(transcript, 'segments') else None,
                        "language": transcript.language if hasattr(transcript, 'language') else None,
                        "duration": transcript.duration if hasattr(transcript, 'duration') else None
                    }
                else:
                    return {
                        "success": True,
                        "text": transcript
                    }
                    
        except Exception as e:
            error_msg = str(e)
            
            # Categorize errors
            if "rate limit" in error_msg.lower():
                error_type = "rate_limit"
            elif "authentication" in error_msg.lower():
                error_type = "authentication"
            elif "file size" in error_msg.lower():
                error_type = "file_size"
            else:
                error_type = "transcription_error"
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type
            }
    
    def _transcribe_azure(self, audio_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe using Azure Speech Services"""
        if not HAS_AZURE:
            return {
                "success": False,
                "error": "Azure Speech SDK not available"
            }
        
        try:
            # Azure implementation would go here
            # This is a placeholder for future implementation
            return {
                "success": False,
                "error": "Azure transcription not yet implemented"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Azure transcription failed: {str(e)}"
            }
    
    def _transcribe_google(self, audio_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe using Google Speech-to-Text"""
        if not HAS_GOOGLE:
            return {
                "success": False,
                "error": "Google Speech SDK not available"
            }
        
        try:
            # Google implementation would go here
            # This is a placeholder for future implementation
            return {
                "success": False,
                "error": "Google transcription not yet implemented"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Google transcription failed: {str(e)}"
            }
    
    def get_supported_providers(self) -> Dict[str, bool]:
        """Get list of supported transcription providers"""
        return {
            "openai": bool(self.openai_client),
            "azure": HAS_AZURE,
            "google": HAS_GOOGLE
        }
    
    def validate_settings(self, provider: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate transcription settings for a provider
        
        Args:
            provider: Transcription provider
            settings: Settings to validate
        
        Returns:
            Validation result with errors if any
        """
        errors = []
        
        if provider == "openai":
            if not self.openai_client:
                errors.append("OpenAI API key not configured")
            
            model = settings.get("model", "whisper-1")
            if model not in ["whisper-1"]:
                errors.append(f"Unsupported OpenAI model: {model}")
            
            language = settings.get("language")
            if language and language not in ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]:
                errors.append(f"Unsupported language: {language}")
        
        elif provider == "azure":
            if not HAS_AZURE:
                errors.append("Azure Speech SDK not available")
        
        elif provider == "google":
            if not HAS_GOOGLE:
                errors.append("Google Speech SDK not available")
        
        else:
            errors.append(f"Unsupported provider: {provider}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
