#!/usr/bin/env python3
"""
Audio Enhancement Demo
Phase 2: Backend Enhancement

Demonstrates the audio enhancement pipeline with real audio processing
"""

import os
import tempfile
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from pathlib import Path

from app.services.audio_enhancement import AudioEnhancementService


def generate_demo_audio():
    """Generate demo audio with noise for enhancement testing"""
    print("🎵 Generating demo audio...")
    
    # Parameters
    duration = 3.0  # seconds
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create speech-like signal with multiple frequencies
    speech_freqs = [300, 800, 1200, 2200]  # Typical speech formants
    clean_signal = np.zeros_like(t)
    
    for i, freq in enumerate(speech_freqs):
        amplitude = 0.3 / (i + 1)  # Decreasing amplitude
        clean_signal += amplitude * np.sin(2 * np.pi * freq * t)
    
    # Add amplitude modulation to simulate speech patterns
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)  # 2 Hz modulation
    clean_signal *= envelope
    
    # Add various types of noise
    # 1. White noise
    white_noise = np.random.normal(0, 0.1, len(t))
    
    # 2. Low-frequency rumble (AC hum, traffic)
    rumble = 0.15 * np.sin(2 * np.pi * 60 * t) + 0.1 * np.sin(2 * np.pi * 120 * t)
    
    # 3. High-frequency hiss
    hiss = np.random.normal(0, 0.05, len(t))
    hiss = np.convolve(hiss, np.ones(10)/10, mode='same')  # Smooth the hiss
    
    # Combine signal and noise
    noisy_signal = clean_signal + white_noise + rumble + hiss
    
    # Normalize to prevent clipping
    noisy_signal = noisy_signal / np.max(np.abs(noisy_signal)) * 0.8
    
    print(f"✅ Generated {duration}s of noisy audio at {sample_rate}Hz")
    return noisy_signal, sample_rate


def save_audio(audio, sample_rate, filename):
    """Save audio to file"""
    sf.write(filename, audio, sample_rate)
    print(f"💾 Saved audio: {filename}")


def analyze_audio(audio, sample_rate, title="Audio"):
    """Analyze audio characteristics"""
    print(f"\n📊 {title} Analysis:")
    print(f"   Duration: {len(audio)/sample_rate:.2f}s")
    print(f"   Sample Rate: {sample_rate}Hz")
    print(f"   RMS Level: {np.sqrt(np.mean(audio**2)):.4f}")
    print(f"   Peak Level: {np.max(np.abs(audio)):.4f}")
    print(f"   Dynamic Range: {20*np.log10(np.max(np.abs(audio))/np.sqrt(np.mean(audio**2))):.1f} dB")


def plot_audio_comparison(original, enhanced, sample_rate):
    """Create comparison plots of original vs enhanced audio"""
    try:
        import matplotlib.pyplot as plt
        
        # Time axis
        t = np.linspace(0, len(original)/sample_rate, len(original))
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Audio Enhancement Comparison', fontsize=16)
        
        # Time domain plots
        axes[0, 0].plot(t[:1000], original[:1000])
        axes[0, 0].set_title('Original Audio (Time Domain)')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Amplitude')
        
        axes[0, 1].plot(t[:1000], enhanced[:1000])
        axes[0, 1].set_title('Enhanced Audio (Time Domain)')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Amplitude')
        
        # Frequency domain plots
        freqs_orig = np.fft.fftfreq(len(original), 1/sample_rate)
        fft_orig = np.abs(np.fft.fft(original))
        
        freqs_enh = np.fft.fftfreq(len(enhanced), 1/sample_rate)
        fft_enh = np.abs(np.fft.fft(enhanced))
        
        # Plot only positive frequencies up to 4kHz
        mask_orig = (freqs_orig >= 0) & (freqs_orig <= 4000)
        mask_enh = (freqs_enh >= 0) & (freqs_enh <= 4000)
        
        axes[1, 0].semilogy(freqs_orig[mask_orig], fft_orig[mask_orig])
        axes[1, 0].set_title('Original Audio (Frequency Domain)')
        axes[1, 0].set_xlabel('Frequency (Hz)')
        axes[1, 0].set_ylabel('Magnitude')
        
        axes[1, 1].semilogy(freqs_enh[mask_enh], fft_enh[mask_enh])
        axes[1, 1].set_title('Enhanced Audio (Frequency Domain)')
        axes[1, 1].set_xlabel('Frequency (Hz)')
        axes[1, 1].set_ylabel('Magnitude')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = "audio_enhancement_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"📈 Saved comparison plot: {plot_path}")
        
        return plot_path
        
    except ImportError:
        print("⚠️  Matplotlib not available - skipping plots")
        return None


def main():
    """Main demo function"""
    print("🎵 Audio Enhancement Demo")
    print("=" * 50)
    
    # Create temporary directory for demo files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate demo audio
        noisy_audio, sample_rate = generate_demo_audio()
        
        # Save original audio
        original_path = temp_path / "original_noisy.wav"
        save_audio(noisy_audio, sample_rate, str(original_path))
        
        # Analyze original audio
        analyze_audio(noisy_audio, sample_rate, "Original Noisy Audio")
        
        # Initialize enhancement service
        print("\n🔧 Initializing Audio Enhancement Service...")
        enhancer = AudioEnhancementService()
        
        # Enhancement options
        enhancement_options = {
            "sample_rate": sample_rate,
            "noise_reduction": True,
            "vad_attenuation_db": 15,  # Strong background noise reduction
            "high_pass_freq": 100,     # Remove low-frequency rumble
            "compression_ratio": 3.0,   # Moderate compression
            "limiter_threshold": -3.0,  # Prevent clipping
            "lufs_target": -20.0,      # Normalize loudness
            "speaker_boost_db": 4.0,   # Boost speech frequencies
            "normalize_loudness": False  # Skip LUFS for demo
        }
        
        print("\n🎛️  Enhancement Settings:")
        for key, value in enhancement_options.items():
            print(f"   {key}: {value}")
        
        # Apply enhancement
        print("\n⚡ Applying audio enhancement...")
        try:
            enhanced_path = enhancer._enhance_audio_sync(
                str(original_path),
                str(temp_path),
                enhancement_options
            )
            
            if enhanced_path != str(original_path):
                # Load enhanced audio for analysis
                enhanced_audio, _ = sf.read(enhanced_path)
                
                # Analyze enhanced audio
                analyze_audio(enhanced_audio, sample_rate, "Enhanced Audio")
                
                # Calculate improvement metrics
                print("\n📈 Enhancement Results:")
                
                # RMS improvement
                original_rms = np.sqrt(np.mean(noisy_audio**2))
                enhanced_rms = np.sqrt(np.mean(enhanced_audio**2))
                rms_change = 20 * np.log10(enhanced_rms / original_rms)
                print(f"   RMS Level Change: {rms_change:+.1f} dB")
                
                # Peak improvement
                original_peak = np.max(np.abs(noisy_audio))
                enhanced_peak = np.max(np.abs(enhanced_audio))
                peak_change = 20 * np.log10(enhanced_peak / original_peak)
                print(f"   Peak Level Change: {peak_change:+.1f} dB")
                
                # Dynamic range
                original_dr = 20*np.log10(np.max(np.abs(noisy_audio))/np.sqrt(np.mean(noisy_audio**2)))
                enhanced_dr = 20*np.log10(np.max(np.abs(enhanced_audio))/np.sqrt(np.mean(enhanced_audio**2)))
                dr_change = enhanced_dr - original_dr
                print(f"   Dynamic Range Change: {dr_change:+.1f} dB")
                
                # Create comparison plots
                plot_path = plot_audio_comparison(noisy_audio, enhanced_audio, sample_rate)
                
                # Copy files to current directory for inspection
                import shutil
                final_original = "demo_original.wav"
                final_enhanced = "demo_enhanced.wav"
                
                shutil.copy2(str(original_path), final_original)
                shutil.copy2(enhanced_path, final_enhanced)
                
                print(f"\n🎉 Enhancement completed successfully!")
                print(f"   Original file: {final_original}")
                print(f"   Enhanced file: {final_enhanced}")
                if plot_path:
                    print(f"   Comparison plot: {plot_path}")
                
                print(f"\n💡 You can listen to both files to hear the difference!")
                
            else:
                print("❌ Enhancement failed - returned original file")
                
        except Exception as e:
            print(f"❌ Enhancement failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
