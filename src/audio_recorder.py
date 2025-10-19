"""
Simple audio recorder for testing
Records from microphone and saves to WAV file
"""
import pyaudio
import wave
from pathlib import Path

class AudioRecorder:
    def __init__(self):
        # Audio settings (standard for speech)
        self.CHUNK = 1024  # Buffer size
        self.FORMAT = pyaudio.paInt16  # 16-bit audio
        self.CHANNELS = 1  # Mono
        self.RATE = 16000  # Sample rate (16kHz good for speech)
        
        self.audio = pyaudio.PyAudio()
        
    def list_devices(self):
        """List available audio input devices"""
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:  # Input device
                print(f"  [{i}] {info['name']}")
    
    def record(self, duration_seconds=5, output_file="recording.wav", device_index=None):
        """
        Record audio for specified duration
        
        Args:
            duration_seconds: How long to record
            output_file: Where to save the recording
            device_index: Specific device to use (None = default)
        """
        print(f"🎤 Recording for {duration_seconds} seconds...")
        
        # Open audio stream
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.CHUNK
        )
        
        frames = []
        
        # Record
        num_chunks = int(self.RATE / self.CHUNK * duration_seconds)
        for i in range(num_chunks):
            data = stream.read(self.CHUNK)
            frames.append(data)
            
            # Progress indicator
            if i % 16 == 0:  # Every ~1 second
                print(".", end="", flush=True)
        
        print("\n✅ Recording complete!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        
        # Save to WAV file
        self._save_wav(frames, output_file)
        print(f"💾 Saved to: {output_file}")
        
        return output_file
    
    def _save_wav(self, frames, filename):
        """Save recorded frames to WAV file"""
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    
    def cleanup(self):
        """Clean up audio resources"""
        self.audio.terminate()

# Test the recorder
if __name__ == "__main__":
    recorder = AudioRecorder()
    
    # List available devices
    recorder.list_devices()
    
    # Record 5 seconds
    print("\nPress Enter to start recording...")
    input()
    
    output_file = "test_recording.wav"
    recorder.record(duration_seconds=5, output_file=output_file)
    
    recorder.cleanup()
    
    print(f"\n🎉 Success! Play {output_file} to verify.")