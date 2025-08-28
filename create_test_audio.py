#!/usr/bin/env python3
"""
Create a test audio file using OpenAI's text-to-speech API
This will generate an audio file that we can then test transcription with
"""

import os
from openai import OpenAI

def create_test_audio(text="Hello, this is a test audio file for transcription testing. The quick brown fox jumps over the lazy dog.", 
                     output_file="test_audio.mp3", 
                     voice="alloy"):
    """
    Create a test audio file using OpenAI TTS
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Output filename
        voice (str): Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    """
    
    try:
        print("🔊 Creating test audio file...")
        print(f"📝 Text: {text}")
        print(f"🎤 Voice: {voice}")
        print(f"📁 Output: {output_file}")
        
        # Initialize OpenAI client
        client = OpenAI()
        
        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to file
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        file_size = os.path.getsize(output_file)
        print(f"✅ Audio file created successfully!")
        print(f"📊 File size: {file_size / 1024:.1f}KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create audio file: {str(e)}")
        return False

def main():
    """Main function"""
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    print("🎵 OpenAI Test Audio Generator")
    print("=" * 35)
    
    # Create test audio file
    success = create_test_audio()
    
    if success:
        print("\n🎉 Test audio file created!")
        print("\nNow you can test transcription with:")
        print("python test_transcription.py test_audio.mp3")
    else:
        print("\n💥 Failed to create test audio file!")

if __name__ == "__main__":
    main()
