import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical
import os
from datetime import datetime
from src.schemas import ConversationSegment, ConversationSummary
from src.database import save_conversation

st.set_page_config(page_title="Admin Tools", page_icon="🛠️")

st.title("🛠️ Admin: Record New Data")
st.caption("This page is a developer tool to simulate Feature #1 (Ambient Recording)")

if st.button("Start 5-Second Recording", type="primary", use_container_width=True):
    
    record_start_time = datetime.utcnow()
    with st.spinner("🎤 Recording for 5 seconds..."):
        try:
            recorder = AudioRecorder()
            output_file = "temp_recording.wav"
            recorder.record(duration_seconds=5, output_file=output_file)
            record_end_time = datetime.utcnow()
            recorder.cleanup()
        except Exception as e:
            st.error(f"Error during recording: {e}")
            st.stop()

    with st.spinner("🤖 AI Brain Processing..."):
        transcript = transcribe_audio(output_file)
        
        if transcript.startswith("Error:"):
            st.error(transcript)
            st.stop()

        simple_summary_text = summarize_transcript_simple(transcript)
        clinical_data_dict = summarize_transcript_clinical(transcript)

    with st.spinner("💾 Saving to database..."):
        try:
            segment = ConversationSegment(
                end_time=record_end_time,
                transcript=transcript
            )
            
            summary = ConversationSummary(
                segment_id=segment.segment_id,
                simple_summary=simple_summary_text,
                **clinical_data_dict 
            )
            
            save_conversation(segment, summary)
        except Exception as e:
            st.error(f"Error saving to database: {e}")
            st.stop()

    st.success("Recording Processed and Saved!")
    st.subheader("Patient Summary (Level 1)")
    st.info(simple_summary_text)
    
    st.subheader("Clinical Data (Level 2)")
    st.json(clinical_data_dict)
    
    try:
        os.remove(output_file)
    except OSError as e:
        st.warning(f"Could not clean up temp file: {e}")
    
    st.info("Data has been added. Check the Caregiver Dashboard.")

else:
    st.info("Click the button to simulate a 5-second conversation and add it to the database.")
