# run_v1.py
# This is your first "vertical slice" of the application!

from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
import os

def main():
    print("--- Welcome to RememberMe AI (v0.1) ---")
    
    recorder = AudioRecorder()
    
    # 1. Record Audio
    print("\nPress Enter to start recording for 5 seconds...")
    input()
    
    output_file = "temp_recording.wav"
    recorder.record(duration_seconds=5, output_file=output_file)
    recorder.cleanup()
    
    # 2. Transcribe Audio
    transcript = transcribe_audio(output_file)
    
    # 3. Show Result
    print("\n--- 🎙️ YOU SAID: ---")
    print(transcript)
    print("----------------------")
    
    # 4. (Optional) Clean up the temporary audio file
    try:
        os.remove(output_file)
        print(f"\n(Cleaned up {output_file})")
    except OSError as e:
        print(f"Error cleaning up file: {e}")

if __name__ == "__main__":
    main()