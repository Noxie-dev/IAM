"""
Audio Enhancement Service
Phase 2: Backend Enhancement

Production-ready audio enhancement pipeline for improving transcription quality
"""

import os
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import soundfile as sf
import librosa
from scipy import signal

# Optional dependencies (auto-detected)
try:
    import webrtcvad
    HAS_WEBRTCVAD = True
except ImportError:
    HAS_WEBRTCVAD = False

try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
except ImportError:
    HAS_NOISEREDUCE = False

try:
    import pyloudnorm as pyln
    HAS_PYLOUDNORM = True
except ImportError:
    HAS_PYLOUDNORM = False

try:
    import rnnoise
    HAS_RNNOISE = True
except ImportError:
    HAS_RNNOISE = False

try:
    from nara_wpe import wpe
    HAS_WPE = True
except ImportError:
    HAS_WPE = False

logger = logging.getLogger(__name__)

class AudioEnhancementService:
    """
    Production-ready audio enhancement service for improving transcription quality
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.supported_formats = {'.wav', '.mp3', '.m4a', '.mp4', '.mpeg', '.mpga', '.ogg', '.webm', '.flac'}
        
        # Log available enhancement features
        features = []
        if HAS_WEBRTCVAD:
            features.append("WebRTC VAD")
        if HAS_NOISEREDUCE:
            features.append("Spectral Noise Reduction")
        if HAS_PYLOUDNORM:
            features.append("LUFS Normalization")
        if HAS_RNNOISE:
            features.append("RNNoise")
        if HAS_WPE:
            features.append("WPE Dereverb")
        
        logger.info(f"Audio enhancement initialized with features: {', '.join(features) if features else 'Basic only'}")
    
    async def enhance_audio(
        self,
        input_path: str,
        output_dir: str,
        options: Optional[str] = None
    ) -> str:
        """
        Enhance audio file asynchronously
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            options: JSON string with enhancement options
        
        Returns:
            Path to enhanced audio file
        """
        # Parse enhancement options
        enhancement_options = self._parse_options(options)
        
        # Run enhancement in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        enhanced_path = await loop.run_in_executor(
            self.executor,
            self._enhance_audio_sync,
            input_path,
            output_dir,
            enhancement_options
        )
        
        return enhanced_path
    
    def _parse_options(self, options: Optional[str]) -> Dict[str, Any]:
        """Parse enhancement options from JSON string"""
        default_options = {
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
        
        if options:
            try:
                user_options = json.loads(options)
                default_options.update(user_options)
            except json.JSONDecodeError:
                logger.warning(f"Invalid enhancement options JSON: {options}")
        
        return default_options
    
    def _enhance_audio_sync(
        self,
        input_path: str,
        output_dir: str,
        options: Dict[str, Any]
    ) -> str:
        """
        Synchronous audio enhancement pipeline
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            options: Enhancement options
        
        Returns:
            Path to enhanced audio file
        """
        try:
            # Generate output filename
            input_name = Path(input_path).stem
            output_path = os.path.join(output_dir, f"{input_name}_enhanced.wav")
            
            logger.info(f"Starting audio enhancement: {input_path} -> {output_path}")
            
            # Load audio
            audio, sr = librosa.load(input_path, sr=None)
            target_sr = options.get("sample_rate", 16000)
            
            # Resample if needed
            if sr != target_sr:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
            
            logger.info(f"Loaded audio: {len(audio)/sr:.2f}s at {sr}Hz")
            
            # Enhancement pipeline
            enhanced_audio = self._apply_enhancement_pipeline(audio, sr, options)
            
            # Save enhanced audio
            sf.write(output_path, enhanced_audio, sr, format='WAV', subtype='PCM_16')
            
            # Verify output file
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception("Enhanced audio file was not created or is empty")
            
            logger.info(f"Audio enhancement completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {str(e)}")
            # Return original path if enhancement fails
            return input_path
    
    def _apply_enhancement_pipeline(
        self,
        audio: np.ndarray,
        sr: int,
        options: Dict[str, Any]
    ) -> np.ndarray:
        """
        Apply the complete audio enhancement pipeline
        
        Args:
            audio: Input audio signal
            sr: Sample rate
            options: Enhancement options
        
        Returns:
            Enhanced audio signal
        """
        enhanced = audio.copy()
        
        # 1. Noise Reduction
        if options.get("noise_reduction", True):
            enhanced = self._apply_noise_reduction(enhanced, sr)
        
        # 2. Voice Activity Detection and Non-speech Attenuation
        if options.get("vad_attenuation_db", 0) > 0:
            enhanced = self._apply_vad_attenuation(enhanced, sr, options["vad_attenuation_db"])
        
        # 3. Dereverberation (optional)
        if options.get("dereverb", False) and HAS_WPE:
            enhanced = self._apply_dereverb(enhanced, sr)
        
        # 4. High-pass filter
        if options.get("high_pass_freq", 0) > 0:
            enhanced = self._apply_high_pass_filter(enhanced, sr, options["high_pass_freq"])
        
        # 5. Dynamic Range Compression
        if options.get("compression_ratio", 0) > 1:
            enhanced = self._apply_compression(enhanced, options["compression_ratio"])
        
        # 6. Limiter
        if options.get("limiter_threshold", 0) < 0:
            enhanced = self._apply_limiter(enhanced, options["limiter_threshold"])
        
        # 7. LUFS Loudness Normalization
        if options.get("normalize_loudness", True) and HAS_PYLOUDNORM:
            enhanced = self._apply_lufs_normalization(enhanced, sr, options.get("lufs_target", -23.0))
        
        # 8. Primary Speaker Boost (lightweight)
        if options.get("speaker_boost_db", 0) > 0:
            enhanced = self._apply_speaker_boost(enhanced, sr, options["speaker_boost_db"])
        
        return enhanced
    
    def _apply_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply noise reduction using available methods"""
        try:
            if HAS_RNNOISE and sr == 48000:
                # RNNoise works best at 48kHz
                return self._apply_rnnoise(audio, sr)
            elif HAS_NOISEREDUCE:
                # Spectral gating fallback
                return nr.reduce_noise(y=audio, sr=sr, stationary=False, prop_decrease=0.8)
            else:
                # Simple spectral subtraction fallback
                return self._apply_spectral_subtraction(audio, sr)
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio
    
    def _apply_rnnoise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply RNNoise if available"""
        try:
            # Convert to int16 for RNNoise
            audio_int16 = (audio * 32767).astype(np.int16)
            denoised_int16 = rnnoise.denoise(audio_int16)
            return denoised_int16.astype(np.float32) / 32767.0
        except Exception as e:
            logger.warning(f"RNNoise failed: {e}")
            return audio
    
    def _apply_spectral_subtraction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Simple spectral subtraction for noise reduction"""
        try:
            # Estimate noise from first 0.5 seconds
            noise_duration = min(int(0.5 * sr), len(audio) // 4)
            noise_sample = audio[:noise_duration]
            
            # Simple spectral subtraction
            stft = librosa.stft(audio)
            noise_stft = librosa.stft(noise_sample)
            noise_power = np.mean(np.abs(noise_stft) ** 2, axis=1, keepdims=True)
            
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Subtract noise estimate
            clean_magnitude = magnitude - 0.5 * np.sqrt(noise_power)
            clean_magnitude = np.maximum(clean_magnitude, 0.1 * magnitude)
            
            clean_stft = clean_magnitude * np.exp(1j * phase)
            return librosa.istft(clean_stft)
        except Exception as e:
            logger.warning(f"Spectral subtraction failed: {e}")
            return audio
    
    def _apply_vad_attenuation(self, audio: np.ndarray, sr: int, attenuation_db: float) -> np.ndarray:
        """Apply VAD-based non-speech attenuation"""
        if not HAS_WEBRTCVAD or sr not in [8000, 16000, 32000, 48000]:
            return audio
        
        try:
            vad = webrtcvad.Vad(2)  # Aggressiveness level 2
            frame_duration = 30  # ms
            frame_length = int(sr * frame_duration / 1000)
            
            # Convert to int16 for VAD
            audio_int16 = (audio * 32767).astype(np.int16)
            
            enhanced = audio.copy()
            attenuation_factor = 10 ** (-attenuation_db / 20)
            
            for i in range(0, len(audio_int16) - frame_length, frame_length):
                frame = audio_int16[i:i + frame_length]
                
                if len(frame) == frame_length:
                    frame_bytes = frame.tobytes()
                    is_speech = vad.is_speech(frame_bytes, sr)
                    
                    if not is_speech:
                        enhanced[i:i + frame_length] *= attenuation_factor
            
            return enhanced
        except Exception as e:
            logger.warning(f"VAD attenuation failed: {e}")
            return audio
    
    def _apply_dereverb(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply WPE dereverberation if available"""
        try:
            if not HAS_WPE:
                return audio
            
            # WPE expects multi-channel input, so we duplicate mono to stereo
            if audio.ndim == 1:
                audio_stereo = np.stack([audio, audio])
            else:
                audio_stereo = audio
            
            # Apply WPE
            enhanced_stereo = wpe(audio_stereo, taps=10, delay=3, iterations=3)
            
            # Return to mono
            return enhanced_stereo[0] if enhanced_stereo.ndim > 1 else enhanced_stereo
        except Exception as e:
            logger.warning(f"Dereverberation failed: {e}")
            return audio
    
    def _apply_high_pass_filter(self, audio: np.ndarray, sr: int, cutoff_freq: float) -> np.ndarray:
        """Apply high-pass filter"""
        try:
            nyquist = sr / 2
            normalized_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='high')
            return signal.filtfilt(b, a, audio)
        except Exception as e:
            logger.warning(f"High-pass filter failed: {e}")
            return audio
    
    def _apply_compression(self, audio: np.ndarray, ratio: float) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            threshold = 0.1
            compressed = audio.copy()
            
            # Simple compression
            mask = np.abs(compressed) > threshold
            compressed[mask] = np.sign(compressed[mask]) * (
                threshold + (np.abs(compressed[mask]) - threshold) / ratio
            )
            
            return compressed
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return audio
    
    def _apply_limiter(self, audio: np.ndarray, threshold_db: float) -> np.ndarray:
        """Apply limiter"""
        try:
            threshold = 10 ** (threshold_db / 20)
            return np.clip(audio, -threshold, threshold)
        except Exception as e:
            logger.warning(f"Limiter failed: {e}")
            return audio
    
    def _apply_lufs_normalization(self, audio: np.ndarray, sr: int, target_lufs: float) -> np.ndarray:
        """Apply LUFS loudness normalization"""
        try:
            if not HAS_PYLOUDNORM:
                return audio
            
            meter = pyln.Meter(sr)
            loudness = meter.integrated_loudness(audio)
            
            if np.isfinite(loudness):
                normalized = pyln.normalize.loudness(audio, loudness, target_lufs)
                return normalized
            else:
                return audio
        except Exception as e:
            logger.warning(f"LUFS normalization failed: {e}")
            return audio
    
    def _apply_speaker_boost(self, audio: np.ndarray, sr: int, boost_db: float) -> np.ndarray:
        """Apply lightweight primary speaker boost"""
        try:
            # Simple spectral emphasis in speech frequency range (300-3400 Hz)
            stft = librosa.stft(audio)
            freqs = librosa.fft_frequencies(sr=sr)
            
            # Create boost mask for speech frequencies
            speech_mask = (freqs >= 300) & (freqs <= 3400)
            boost_factor = 10 ** (boost_db / 20)
            
            # Apply boost
            stft[speech_mask] *= boost_factor
            
            return librosa.istft(stft)
        except Exception as e:
            logger.warning(f"Speaker boost failed: {e}")
            return audio
