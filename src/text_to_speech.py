"""
Module for converting text to speech using OpenAI's TTS API.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

def text_to_speech(text_to_speak: str, output_filename: str = "temp_recap.mp3") -> Path:
    """
    Converts a string of text into a spoken audio file.

    Args:
        text_to_speak: The text to be spoken.
        output_filename: The name of the file to save the audio to.

    Returns:
        The Path object of the generated audio file.
    """
    if not client:
        raise ConnectionError("OpenAI client not initialized.")
    
    print(f"🗣️ Converting text to speech...")
    
    try:
        # Using the TTS API
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova", # A warm, friendly female voice
            input=text_to_speak
        )

        # Stream the audio data to a file
        output_path = Path(output_filename)
        response.stream_to_file(output_path)
        
        print(f"✅ Audio saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error during text-to-speech conversion: {e}")
        raise e

# --- Test this module independently ---
if __name__ == "__main__":
    print("--- Testing Text-to-Speech Module ---")
    test_text = "Hello! This is a test of the text to speech system for the RememberMe AI project. I hope it sounds pleasant."
    
    try:
        audio_file = text_to_speech(test_text)
        print(f"\n🎉 Success! Play {audio_file} to verify.")
    except Exception as e:
        print(f"Test failed: {e}")
