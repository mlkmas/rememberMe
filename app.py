import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript
import os
from datetime import datetime

# --- NEW IMPORTS ---
from src.schemas import ConversationSegment, ConversationSummary
from src.database import save_conversation, get_all_conversations
# ---------------------

# --- Page Configuration ---
st.set_page_config(page_title="RememberMe AI", page_icon="🧠", layout="wide") # Use "wide" layout
st.title("🧠 RememberMe AI")

# --- Create two columns: 1. Record, 2. Dashboard ---
col1, col2 = st.columns(2)

# --- COLUMN 1: RECORD NEW MEMORY ---
with col1:
    st.header("Record a New Memory")
    st.caption("Your personal conversation memory assistant.")

    if st.button("Start 5-Second Recording", type="primary", use_container_width=True):
        
        with st.spinner("🎤 Recording for 5 seconds..."):
            try:
                recorder = AudioRecorder()
                output_file = "temp_recording.wav"
                record_start_time = datetime.utcnow()
                recorder.record(duration_seconds=5, output_file=output_file)
                record_end_time = datetime.utcnow()
                recorder.cleanup()
            except Exception as e:
                st.error(f"Error during recording: {e}")
                st.stop()

        with st.spinner("📝 Transcribing and summarizing..."):
            try:
                transcript = transcribe_audio(output_file)
                summary_text = summarize_transcript(transcript)
            except Exception as e:
                st.error(f"Error during AI processing: {e}")
                st.stop()

        # --- NEW: Create Pydantic models and save to DB ---
        try:
            segment = ConversationSegment(
                end_time=record_end_time,
                transcript=transcript
            )
            
            summary = ConversationSummary(
                segment_id=segment.segment_id,
                simple_summary=summary_text
            )
            
            # Save to MongoDB
            save_conversation(segment, summary)

        except Exception as e:
            st.error(f"Error saving to database: {e}")
        # ----------------------------------------------------

        st.success("Recording Processed and Saved!")
        st.subheader("Your Simple Summary")
        st.info(summary_text)
        st.subheader("Full Transcript")
        st.text_area("Here's what you said:", transcript, height=150)
        
        try:
            os.remove(output_file)
        except OSError as e:
            st.warning(f"Could not clean up temp file: {e}")

    else:
        st.info("Click the button to start a 5-second recording.")


# --- COLUMN 2: Patient DASHBOARD (Feature 5) ---
with col2:
    st.header("Patient Dashboard")
    st.caption("A timeline of recent conversations.")
    
    # Add a refresh button
    if st.button("Refresh Timeline", use_container_width=True):
        st.rerun() # This will rerun the whole script to fetch new data

    # Get all conversations from the database
    all_summaries = get_all_conversations()
    
    if not all_summaries:
        st.write("No conversations recorded yet.")
    else:
        st.write(f"Showing {len(all_summaries)} most recent memories:")
        
        # Loop through and display each one
        for item in all_summaries:
            # We use item.get('key', 'default') in case the key is missing
            with st.container(border=True):
                col_date, col_summary = st.columns([1, 3])
                
                with col_date:
                    # Parse the datetime to show it nicely
                    date = item.get('generated_at', datetime.now())
                    st.write(f"**{date.strftime('%Y-%m-%d')}**")
                    st.write(f"{date.strftime('%I:%M %p')}")

                with col_summary:
                    st.write(item.get('simple_summary', 'No summary available.'))