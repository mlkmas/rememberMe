# src/livekit_client.py
import asyncio
import os
import wave
import io
from datetime import datetime
from pathlib import Path
from livekit import rtc
from dotenv import load_dotenv
import requests
import numpy as np

# Import your existing modules
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

        # Thresholds (tune these)
        self.SILENCE_THRESHOLD = 50  # ~5 seconds of silence ends conversation
        self.MIN_SPEECH_FRAMES = 10  # Need at least 10 frames to start
        self.ENERGY_THRESHOLD = 500  # Adjust based on your mic
        self.SAMPLE_RATE = 48000  # LiveKit default

        # Create recordings directory
        Path("recordings").mkdir(exist_ok=True)

        print("🎤 AudioReceiverAgent initialized")

    def is_speech(self, audio_frame):
        """Detect if audio frame contains speech"""
        try:
            # Convert frame data to numpy array
            audio_data = np.frombuffer(audio_frame.data, dtype=np.int16)

            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_data ** 2))

            return rms > self.ENERGY_THRESHOLD
        except Exception as e:
            print(f"Error in is_speech: {e}")
            return False

    def add_frame(self, audio_frame):
        """
        Add frame to buffer and detect conversation boundaries
        Returns True if conversation ended and should be saved
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
                self.audio_buffer.append(audio_frame.data)

        else:
            # Silence detected
            if self.is_recording:
                self.silence_frames += 1
                self.audio_buffer.append(audio_frame.data)

                # End conversation after prolonged silence
                if self.silence_frames >= self.SILENCE_THRESHOLD:
                    print(f"🛑 Silence detected - Ending conversation")
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
            print("🤖 Transcribing...")
            transcript = transcribe_audio(audio_filename)

            if not transcript or transcript.startswith("Error"):
                print(f"❌ Transcription failed")
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

            self.reset()
            return True

        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            import traceback
            traceback.print_exc()
            self.reset()
            return False

    def reset(self):
        """Reset recorder state"""
        self.audio_buffer = []
        self.is_recording = False
        self.silence_frames = 0
        self.speech_frames = 0
        print("🔄 Recorder reset")

    async def start(self, identity: str, token: str):
        """Connects to the LiveKit room"""
        try:
            print(f"Connecting to {LIVEKIT_URL} as {identity}...")
            await self.room.connect(LIVEKIT_URL, token)
            print(f"✅ Successfully connected to room: {self.room.name}")

            @self.room.on("track_published")
            def on_track_published(publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
                if publication.kind == rtc.TrackKind.KIND_AUDIO and participant.identity != identity:
                    print(f"🎵 Audio track from: {participant.identity}")
                    asyncio.ensure_future(self.subscribe_to_track(publication))

            # Check for existing tracks
            for participant in self.room.remote_participants.values():
                for track_pub in participant.track_publications.values():
                    if track_pub.kind == rtc.TrackKind.KIND_AUDIO:
                        print(f"Found existing audio track from: {participant.identity}")
                        asyncio.ensure_future(self.subscribe_to_track(track_pub))

        except Exception as e:
            print(f"❌ Error connecting to LiveKit: {e}")
            import traceback
            traceback.print_exc()

    async def subscribe_to_track(self, publication: rtc.TrackPublication):
        """Subscribes to track and processes audio"""
        try:
            track = publication.track
            print(f"✅ Subscribed to track: {publication.sid}")

            self.audio_stream = rtc.AudioStream(track)
            self.is_listening = True
            print("🎧 Audio stream started. Listening...")

            # Process each audio frame
            async for frame in self.audio_stream:
                # Add frame to buffer
                should_save = self.add_frame(frame)

                # Save if conversation ended
                if should_save:
                    await self.save_conversation()

        except Exception as e:
            print(f"❌ Error processing audio: {e}")
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
        res = requests.get(f"http://localhost:5000/get_token?identity={identity}")
        res.raise_for_status()
        return res.json()["token"]
    except requests.RequestException as e:
        print(f"❌ Error getting token: {e}")
        print("Make sure token server is running: poetry run python src/token_server.py")
        return None


# --- Main function for testing ---
async def main():
    print("--- Testing LiveKit Client ---")

    token = get_token(identity="rememberme-agent")
    if not token:
        print("Test failed: Could not get token")
        return

    agent = AudioReceiverAgent()
    try:
        await agent.start(identity="rememberme-agent", token=token)
        print("\n✅ Agent is running and listening for audio")
        print("Join the room from another device and start speaking!")

        # Keep running
        await asyncio.sleep(300)  # Run for 5 minutes

    except asyncio.CancelledError:
        print("Test cancelled")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())