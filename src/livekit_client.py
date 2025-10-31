# src/livekit_client.py
import asyncio
import os
import sys
import wave
from datetime import datetime
from pathlib import Path
from livekit import rtc
from dotenv import load_dotenv
import requests
import numpy as np

# Fix import path when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical
from src.schemas import ConversationSegment, ConversationSummary
from src.database import save_conversation

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")


class AudioReceiverAgent:
    """
    Enhanced agent that:
    1. Receives audio from LiveKit
    2. Detects conversation boundaries
    3. Transcribes and saves conversations
    """

    def __init__(self):
        self.room = rtc.Room()
        self.audio_stream = None
        self.is_listening = False

        # Audio buffer for recording
        self.audio_buffer = []
        self.is_recording = False
        self.silence_frames = 0
        self.speech_frames = 0

        # Thresholds (tune these based on testing)
        self.SILENCE_THRESHOLD = 50  # ~5 seconds of silence ends conversation
        self.MIN_SPEECH_FRAMES = 10  # Need at least 10 frames to start
        self.ENERGY_THRESHOLD = 300  # Lower = more sensitive (was 500)
        self.SAMPLE_RATE = 48000  # LiveKit default sample rate

        # Create recordings directory
        Path("recordings").mkdir(exist_ok=True)

        print("🎤 AudioReceiverAgent initialized")

    def is_speech(self, audio_frame):
        """
        Detect if audio frame contains speech using energy detection

        Args:
            audio_frame: LiveKit AudioFrame object

        Returns:
            bool: True if speech detected
        """
        try:
            # FIXED: Access frame.data correctly for LiveKit's AudioFrame
            # audio_frame is the actual frame, not an event
            if hasattr(audio_frame, 'data'):
                audio_data_bytes = audio_frame.data
            else:
                # Fallback if structure is different
                return False

            # Convert bytes to numpy array
            audio_data = np.frombuffer(audio_data_bytes, dtype=np.int16)

            # Calculate RMS (Root Mean Square) energy
            if len(audio_data) > 0:
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            else:
                rms = 0

            # Return True if energy exceeds threshold
            return rms > self.ENERGY_THRESHOLD

        except Exception as e:
            # Silently fail to avoid spam - just log once
            if not hasattr(self, '_error_logged'):
                print(f"⚠️ Error in is_speech (will not repeat): {e}")
                print(f"   Frame type: {type(audio_frame)}")
                print(f"   Frame attributes: {dir(audio_frame)}")
                self._error_logged = True
            return False

    def add_frame(self, audio_frame):
        """
        Add frame to buffer and detect conversation boundaries

        Args:
            audio_frame: LiveKit AudioFrame object

        Returns:
            bool: True if conversation ended and should be saved
        """
        has_speech = self.is_speech(audio_frame)

        if has_speech:
            self.speech_frames += 1
            self.silence_frames = 0

            # Start recording after detecting enough speech
            if not self.is_recording and self.speech_frames >= self.MIN_SPEECH_FRAMES:
                self.is_recording = True
                print("🎙️ Conversation started - Recording...")

            # Add frame to buffer if recording
            if self.is_recording:
                # Store the frame data
                if hasattr(audio_frame, 'data'):
                    self.audio_buffer.append(audio_frame.data)

        else:
            # Silence detected
            if self.is_recording:
                self.silence_frames += 1
                # Still add silence frames to buffer for natural pauses
                if hasattr(audio_frame, 'data'):
                    self.audio_buffer.append(audio_frame.data)

                # End conversation after prolonged silence
                if self.silence_frames >= self.SILENCE_THRESHOLD:
                    print(f"🛑 Silence detected ({self.silence_frames} frames) - Ending conversation")
                    return True  # Signal to save

            self.speech_frames = 0

        return False

    async def save_conversation(self):
        """Save, transcribe, summarize, and store conversation"""
        if not self.audio_buffer or len(self.audio_buffer) < 10:
            print("⚠️ Buffer too short, skipping save")
            self.reset()
            return False

        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"recordings/conversation_{timestamp}.wav"

            print(f"💾 Saving conversation ({len(self.audio_buffer)} frames)")

            # Save audio to WAV file
            with wave.open(audio_filename, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(b''.join(self.audio_buffer))

            print(f"✅ Audio saved: {audio_filename}")

            # Transcribe
            print("🤖 Transcribing conversation...")
            transcript = transcribe_audio(audio_filename)

            if not transcript or transcript.startswith("Error"):
                print(f"❌ Transcription failed: {transcript}")
                self.reset()
                return False

            print(f"📝 Transcript: {transcript[:100]}...")

            # Summarize
            print("✨ Generating summaries...")
            simple_summary = summarize_transcript_simple(transcript)
            clinical_data = summarize_transcript_clinical(transcript)

            if "error" in clinical_data:
                print(f"❌ Summarization failed")
                self.reset()
                return False

            print(f"✅ Summaries generated")

            # Save to database
            print("💾 Saving to database...")

            segment = ConversationSegment(
                start_time=datetime.now(),
                end_time=datetime.now(),
                transcript=transcript
            )

            summary = ConversationSummary(
                segment_id=str(segment.id),
                simple_summary=simple_summary,
                **clinical_data
            )

            save_conversation(segment, summary)

            print("🎉 Conversation saved to database!")
            print("=" * 50)

            self.reset()
            return True

        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            import traceback
            traceback.print_exc()
            self.reset()
            return False

    def reset(self):
        """Reset recorder state for next conversation"""
        self.audio_buffer = []
        self.is_recording = False
        self.silence_frames = 0
        self.speech_frames = 0
        print("🔄 Recorder reset, ready for next conversation")

    async def start(self, identity: str, token: str):
        """Connects to the LiveKit room"""
        try:
            print(f"Connecting to {LIVEKIT_URL} as {identity}...")
            await self.room.connect(LIVEKIT_URL, token)
            print(f"✅ Successfully connected to room: {self.room.name}")

            # Event handler for new tracks
            @self.room.on("track_subscribed")
            def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication,
                                    participant: rtc.RemoteParticipant):
                print(f"🎵 Track subscribed event - Kind: {track.kind}, Participant: {participant.identity}")
                if track.kind == rtc.TrackKind.KIND_AUDIO:
                    print(f"   ✅ Audio track confirmed from: {participant.identity}")
                    asyncio.ensure_future(self.process_audio_track(track))

            # Check for existing participants
            print(f"Current participants in room: {len(self.room.remote_participants)}")
            for participant in self.room.remote_participants.values():
                print(f"  - Participant: {participant.identity}")
                for track_pub in participant.track_publications.values():
                    if track_pub.track and track_pub.kind == rtc.TrackKind.KIND_AUDIO:
                        print(f"    Found existing audio track: {track_pub.sid}")
                        asyncio.ensure_future(self.process_audio_track(track_pub.track))

        except Exception as e:
            print(f"❌ Error connecting to LiveKit: {e}")
            import traceback
            traceback.print_exc()

    async def process_audio_track(self, track: rtc.Track):
        """Process incoming audio stream"""
        try:
            print(f"📡 Starting to process audio track: {track.sid}")

            # Create audio stream from track
            audio_stream = rtc.AudioStream(track)
            self.is_listening = True

            print("🎧 Audio stream active. Listening for speech...")
            print(f"   Energy threshold: {self.ENERGY_THRESHOLD}")
            print(f"   Minimum speech frames: {self.MIN_SPEECH_FRAMES}")
            print(f"   Silence threshold: {self.SILENCE_THRESHOLD}")

            frame_count = 0

            # Process each audio frame
            async for event in audio_stream:
                frame_count += 1

                # Show progress every 100 frames (about every 2 seconds)
                if frame_count % 100 == 0:
                    status = "🎙️ RECORDING" if self.is_recording else "👂 Listening"
                    print(f"{status} - Frames processed: {frame_count}, Buffer: {len(self.audio_buffer)}")

                # The event contains the frame
                # Access the actual audio frame data
                audio_frame = event.frame

                # Add frame to buffer and check if conversation ended
                should_save = self.add_frame(audio_frame)

                # Save if conversation ended
                if should_save:
                    await self.save_conversation()

        except Exception as e:
            print(f"❌ Error processing audio track: {e}")
            import traceback
            traceback.print_exc()

    async def stop(self):
        """Disconnects from the room"""
        if self.room.connection_state != rtc.ConnectionState.CONN_DISCONNECTED:
            print("Disconnecting from room...")
            await self.room.disconnect()
            self.is_listening = False
            print("✅ Disconnected")


# --- Helper function to get token ---
def get_token(identity: str) -> str:
    """Gets access token from token server"""
    try:
        print(f"🎫 Requesting token for: {identity}")
        res = requests.get(f"http://localhost:5000/get_token?identity={identity}", timeout=5)
        res.raise_for_status()
        token_data = res.json()
        print(f"✅ Token received")
        return token_data["token"]
    except requests.RequestException as e:
        print(f"❌ Error getting token: {e}")
        print("=" * 50)
        print("Make sure token server is running:")
        print("  poetry run python src/token_server.py")
        print("=" * 50)
        return None


# --- Main function for testing ---
async def main():
    print("=" * 50)
    print("🎙️ RememberMe LiveKit Agent")
    print("=" * 50)

    # Get token
    token = get_token(identity="rememberme-agent")
    if not token:
        print("❌ Failed to get token")
        return

    # Create and start agent
    agent = AudioReceiverAgent()
    try:
        await agent.start(identity="rememberme-agent", token=token)

        print("\n" + "=" * 50)
        print("✅ Agent is running and listening for audio")
        print("=" * 50)
        print("\nTo test:")
        print("1. Go to: http://localhost:8501")
        print("2. Navigate to '🎙️ Live Recording' page")
        print("3. Click 'Open LiveKit Room'")
        print("4. Allow microphone and start speaking!")
        print("5. Watch this terminal for processing logs")
        print("\nPress Ctrl+C to stop")
        print("=" * 50 + "\n")

        # Keep running indefinitely
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Stopping agent...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.stop()
        print("Agent stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")