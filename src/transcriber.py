"""
Module for transcribing audio files using OpenAI's Whisper API.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load API key from .env file
load_dotenv()

# Initialize the OpenAI client
# It will automatically pick up the OPENAI_API_KEY from your environment
try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please make sure your OPENAI_API_KEY is set in the .env file.")
    client = None

def transcribe_audio(audio_file_path: str | Path) -> str:
    """
    Transcribes the given audio file using the Whisper-1 model.

    Args:
        audio_file_path: The path to the audio file (e.g., "recording.wav").

    Returns:
        The transcribed text as a string, or an error message.
    """
    if not client:
        return "Error: OpenAI client not initialized."

    if not Path(audio_file_path).exists():
        return f"Error: Audio file not found at {audio_file_path}"

    print(f"📝 Transcribing {audio_file_path}...")
    
    try:
        # Open the audio file in binary read mode
        with open(audio_file_path, "rb") as audio_file:
            # Call the OpenAI API
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text" # Ask for plain text
            )
        
        print("✅ Transcription complete!")
        return transcription

    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return f"Error: {e}"

# --- Test this module independently ---
if __name__ == "__main__":
    # This block runs ONLY when you execute this file directly
    # e.g., by running `python src/transcriber.py` in your terminal
    
    # We assume you have a file from your recorder test
    test_file = "test_recording.wav"
    
    if Path(test_file).exists():
        print(f"--- Testing Transcriber Module ---")
        transcript = transcribe_audio(test_file)
        print("\n--- Transcript ---")
        print(transcript)
        print("--------------------")
    else:
        print(f"Please run `python src/audio_recorder.py` first to create a '{test_file}'.")