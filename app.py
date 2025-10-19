import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript  # <--- 1. IMPORT IT
import os

# --- Page Configuration ---
st.set_page_config(page_title="RememberMe AI", page_icon="🧠", layout="centered")

# --- App Title ---
st.title("🧠 RememberMe AI")
st.caption("Your personal conversation memory assistant.")

# --- Main App ---
st.header("Record a New Memory")

if st.button("Start 5-Second Recording", type="primary", use_container_width=True):
    
    with st.spinner("🎤 Recording for 5 seconds..."):
        # ... (recording code is the same) ...
        try:
            recorder = AudioRecorder()
            output_file = "temp_recording.wav"
            recorder.record(duration_seconds=5, output_file=output_file)
            recorder.cleanup()
        except Exception as e:
            st.error(f"Error during recording: {e}")
            st.stop()

    with st.spinner("📝 Transcribing and summarizing..."):
        try:
            # ... (transcription code is the same) ...
            transcript = transcribe_audio(output_file)
            
            # <--- 2. CALL THE SUMMARIZER ---
            summary = summarize_transcript(transcript) 

        except Exception as e:
            st.error(f"Error during AI processing: {e}")
            st.stop() 

    # 3. Show the results
    st.success("Recording Processed!")
    
    # <--- 3. DISPLAY THE NEW SUMMARY ---
    st.subheader("Your Simple Summary")
    st.info(summary)  # Use st.info for a nice blue box

    st.subheader("Full Transcript")
    st.text_area("Here's what you said:", transcript, height=150)

    try:
        os.remove(output_file)
    except OSError as e:
        st.warning(f"Could not clean up temp file: {e}")

else:
    st.info("Click the button above to start a 5-second recording.")