#!/usr/bin/env python3
"""
Test your exact OpenAI transcription code
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv('../.env')

def create_test_audio_first():
    """Create a test audio file using TTS"""
    try:
        print("🔊 Creating test audio file first...")
        
        client = OpenAI()
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input="Hello, this is a test audio file for transcription testing. The quick brown fox jumps over the lazy dog. This audio will be transcribed back to text."
        )
        
        with open("test_audio.mp3", "wb") as f:
            f.write(response.content)
        
        print("✅ Test audio file created: test_audio.mp3")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test audio: {str(e)}")
        return False

def test_your_transcription_code():
    """Test your exact transcription code"""
    try:
        print("\n🎵 Testing your transcription code...")
        print("=" * 40)
        
        # Your exact code with modifications for the test file
        client = OpenAI()
        audio_file = open("test_audio.mp3", "rb")

        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", 
            file=audio_file
        )

        print("✅ Transcription successful!")
        print("📝 Result:")
        print("-" * 50)
        print(transcription.text)
        print("-" * 50)
        
        audio_file.close()
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        return False

def test_whisper_model_too():
    """Also test with whisper-1 model for comparison"""
    try:
        print("\n🎵 Testing with whisper-1 model for comparison...")
        print("=" * 50)
        
        client = OpenAI()
        audio_file = open("test_audio.mp3", "rb")

        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )

        print("✅ Whisper-1 transcription successful!")
        print("📝 Result:")
        print("-" * 50)
        print(transcription.text)
        print("-" * 50)
        
        audio_file.close()
        return True
        
    except Exception as e:
        print(f"❌ Whisper-1 transcription failed: {str(e)}")
        return False

def main():
    """Main test function"""
    
    print("🧪 OpenAI Audio Transcription Test")
    print("=" * 40)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        return
    
    print(f"🔑 API Key loaded: {api_key[:20]}...")
    
    # Step 1: Create test audio
    if not create_test_audio_first():
        return
    
    # Step 2: Test your exact code
    success1 = test_your_transcription_code()
    
    # Step 3: Test with whisper-1 for comparison
    success2 = test_whisper_model_too()
    
    # Cleanup
    if os.path.exists("test_audio.mp3"):
        os.remove("test_audio.mp3")
        print("\n🧹 Cleaned up test audio file")
    
    if success1 or success2:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 All tests failed!")

if __name__ == "__main__":
    main()
