import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="RememberMe AI",
    page_icon="🧠",
    layout="centered",
)

# --- App Title ---
st.title("🧠 RememberMe AI")
st.caption("Your personal conversation memory assistant.")

# --- Main App ---
st.header("Record a New Memory")

# We use a button to trigger the recording
if st.button("Start 5-Second Recording", type="primary", use_container_width=True):
    
    # 1. Show a message while recording
    with st.spinner("🎤 Recording for 5 seconds..."):
        try:
            recorder = AudioRecorder()
            output_file = "temp_recording.wav"
            recorder.record(duration_seconds=5, output_file=output_file)
            recorder.cleanup()
        except Exception as e:
            st.error(f"Error during recording: {e}")
            st.stop() # Stop the app if recording fails

    # 2. Show a message while transcribing
    with st.spinner("📝 Transcribing audio..."):
        try:
            transcript = transcribe_audio(output_file)
        except Exception as e:
            st.error(f"Error during transcription: {e}")
            st.stop() # Stop the app if transcription fails

    # 3. Show the result
    st.success("Recording Transcribed!")
    st.text_area("Here's what you said:", transcript, height=150)

    # 4. (Optional) Clean up the temporary audio file
    try:
        os.remove(output_file)
    except OSError as e:
        st.warning(f"Could not clean up temp file: {e}")

else:
    st.info("Click the button above to start a 5-second recording.")