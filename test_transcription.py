#!/usr/bin/env python3
"""
Test script for OpenAI audio transcription functionality
"""

import os
import sys
from openai import OpenAI

def test_transcription(audio_file_path, model="whisper-1"):
    """
    Test OpenAI audio transcription with the provided audio file
    
    Args:
        audio_file_path (str): Path to the audio file
        model (str): Model to use for transcription ("whisper-1" or "gpt-4o-transcribe")
    """
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: Audio file not found at {audio_file_path}")
        return False
    
    # Check file size (OpenAI has a 25MB limit)
    file_size = os.path.getsize(audio_file_path)
    max_size = 25 * 1024 * 1024  # 25MB
    
    if file_size > max_size:
        print(f"❌ Error: File size ({file_size / (1024*1024):.1f}MB) exceeds 25MB limit")
        return False
    
    print(f"📁 File: {audio_file_path}")
    print(f"📊 Size: {file_size / (1024*1024):.2f}MB")
    print(f"🤖 Model: {model}")
    print("🔄 Starting transcription...")
    
    try:
        # Initialize OpenAI client (will use OPENAI_API_KEY from environment)
        client = OpenAI()
        
        # Open and transcribe the audio file
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text"
            )
        
        print("✅ Transcription successful!")
        print("📝 Result:")
        print("-" * 50)
        print(transcription)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        return False

def main():
    """Main function to run transcription test"""
    
    # Check if audio file path is provided
    if len(sys.argv) < 2:
        print("Usage: python test_transcription.py <path_to_audio_file> [model]")
        print("\nExamples:")
        print("  python test_transcription.py /path/to/audio.mp3")
        print("  python test_transcription.py /path/to/audio.wav whisper-1")
        print("  python test_transcription.py /path/to/audio.m4a gpt-4o-transcribe")
        print("\nSupported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg, flac")
        return
    
    audio_file_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "whisper-1"
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("🎵 OpenAI Audio Transcription Test")
    print("=" * 40)
    
    success = test_transcription(audio_file_path, model)
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")

if __name__ == "__main__":
    main()
