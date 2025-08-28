#!/usr/bin/env python3
"""
Example of your OpenAI transcription code with proper error handling
"""

from openai import OpenAI
import os

def test_transcription_with_your_code(audio_file_path):
    """
    Your exact code with some improvements for error handling
    """
    
    print("🎵 Testing OpenAI Audio Transcription")
    print("=" * 40)
    print(f"📁 Audio file: {audio_file_path}")
    
    try:
        # Your exact code:
        client = OpenAI()
        audio_file = open(audio_file_path, "rb")

        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", 
            file=audio_file
        )

        print("✅ Transcription successful!")
        print("📝 Result:")
        print("-" * 50)
        print(transcription.text)
        print("-" * 50)
        
        # Don't forget to close the file
        audio_file.close()
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: Audio file not found at {audio_file_path}")
        print("Please provide a valid path to an audio file")
        return False
        
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        
        # Common error scenarios:
        if "invalid_api_key" in str(e):
            print("💡 Tip: Check your OpenAI API key")
        elif "file_size" in str(e) or "25" in str(e):
            print("💡 Tip: File might be too large (max 25MB)")
        elif "format" in str(e):
            print("💡 Tip: Check if audio format is supported")
            
        return False

def alternative_with_whisper():
    """
    Alternative version using whisper-1 model (more commonly used)
    """
    
    print("\n🎵 Alternative with Whisper-1 Model")
    print("=" * 40)
    
    # This is what the IAM app uses:
    code_example = '''
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/audio.mp3", "rb")

transcription = client.audio.transcriptions.create(
    model="whisper-1",  # Most commonly used model
    file=audio_file,
    response_format="text"  # Optional: get plain text instead of JSON
)

print(transcription.text if hasattr(transcription, 'text') else transcription)
audio_file.close()
    '''
    
    print("📝 Code example:")
    print(code_example)

def main():
    """
    Main function - shows how to use your code
    """
    
    print("🧪 OpenAI Audio Transcription Examples")
    print("=" * 45)
    
    # Check if API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found in environment")
        print("To test this code:")
        print("1. Get a valid OpenAI API key from https://platform.openai.com/api-keys")
        print("2. Set it in your .env file or export it:")
        print("   export OPENAI_API_KEY='your-actual-api-key'")
        print("3. Provide a path to an audio file")
        print()
    
    # Show the code examples
    alternative_with_whisper()
    
    print("\n📋 To test your code:")
    print("1. Make sure you have a valid OpenAI API key")
    print("2. Have an audio file ready (mp3, wav, m4a, etc.)")
    print("3. Replace '/path/to/file/audio.mp3' with your actual file path")
    print("4. Run the code!")
    
    print("\n🔧 Supported audio formats:")
    print("mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg, flac")
    
    print("\n📏 File size limit: 25MB")
    
    print("\n🤖 Available models:")
    print("- whisper-1 (most common, used in IAM app)")
    print("- gpt-4o-transcribe (newer, what you're using)")
    print("- gpt-4o-mini-transcribe")

if __name__ == "__main__":
    main()
