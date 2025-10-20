import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical
import os
from datetime import datetime, time
from src.schemas import ConversationSegment, ConversationSummary, Medication
from src.database import save_conversation, add_medication, get_all_medications, update_medication, delete_medication

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin & Caregiver Tools")
st.divider()

# --- Initialize session state for editing ---
if 'editing_med_id' not in st.session_state:
    st.session_state.editing_med_id = None

# --- UI Layout ---
col1, col2 = st.columns(2)

# --- COLUMN 1: MANAGE MEDICATIONS ---
with col1:
    st.header("Manage Medication Schedule")
    
    # --- Display Current Schedule ---
    st.subheader("Current Medication Schedule")
    medications = get_all_medications()
    
    if not medications:
        st.info("No medications have been added to the schedule yet.")
    else:
        for med in medications:
            med_id = med.get('_id')
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{med.get('time_to_take', '')} - {med.get('name', '')}** ({med.get('dosage', '')})")
                    st.caption(f"Purpose: {med.get('purpose', '')}")
                with c2:
                    # Edit Button
                    if st.button("Edit", key=f"edit_{med_id}", use_container_width=True):
                        st.session_state.editing_med_id = med_id
                        st.rerun() # Rerun to switch form to edit mode
                    
                    # Delete Button
                    if st.button("Delete", key=f"del_{med_id}", type="secondary", use_container_width=True):
                        delete_medication(med_id)
                        st.rerun() # Rerun to refresh the list
    
    st.divider()

    # --- Add or Edit Form ---
    # Find the medication being edited, if any
    med_to_edit = next((med for med in medications if med.get('_id') == st.session_state.editing_med_id), None)

    form_title = "Edit Medication" if med_to_edit else "Add a New Medication"
    with st.form("medication_form", clear_on_submit=False):
        st.subheader(form_title)
        
        # Pre-fill form if editing, otherwise use placeholders
        default_name = med_to_edit.get('name', '') if med_to_edit else ''
        default_dosage = med_to_edit.get('dosage', '') if med_to_edit else ''
        default_purpose = med_to_edit.get('purpose', '') if med_to_edit else ''
        default_time_str = med_to_edit.get('time_to_take', '08:00 AM') if med_to_edit else '08:00 AM'
        
        # Convert time string to time object for the widget
        try:
            default_time = datetime.strptime(default_time_str, '%I:%M %p').time()
        except ValueError:
            default_time = time(8, 0)
        
        med_name = st.text_input("Medication Name", value=default_name)
        med_dosage = st.text_input("Dosage", value=default_dosage)
        med_purpose = st.text_input("Purpose", value=default_purpose)
        med_time = st.time_input("Time to Take", value=default_time)
        
        # --- Form Submission Buttons ---
        form_col1, form_col2 = st.columns([3, 1])
        with form_col1:
            submit_button_text = "Update Medication" if med_to_edit else "Add Medication"
            submitted = st.form_submit_button(submit_button_text, type="primary", use_container_width=True)
        with form_col2:
            if med_to_edit:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.editing_med_id = None
                    st.rerun()

    if submitted:
        if not all([med_name, med_dosage, med_purpose]):
            st.error("Please fill out all fields.")
        else:
            time_str = med_time.strftime("%I:%M %p")
            update_data = {
                "name": med_name,
                "dosage": med_dosage,
                "purpose": med_purpose,
                "time_to_take": time_str
            }
            if med_to_edit:
                # Update existing medication
                update_medication(st.session_state.editing_med_id, update_data)
                st.success(f"Updated {med_name} successfully!")
                st.session_state.editing_med_id = None # Exit edit mode
            else:
                # Add new medication
                new_med = Medication(**update_data)
                add_medication(new_med)
                st.success(f"Added {med_name} to the schedule!")
            st.rerun()


# --- COLUMN 2: SIMULATE CONVERSATION (Unchanged) ---
with col2:
    st.header("Simulate a Conversation")
    st.caption("This is a developer tool for Feature #1")
    # (The code for this section is exactly the same as before)
    if st.button("Start 5-Second Recording", key="record_button", type="secondary", use_container_width=True):
        record_start_time = datetime.utcnow()
        with st.spinner("🎤 Recording..."):
            # ... recording logic ...
            recorder = AudioRecorder()
            output_file = "temp_recording.wav"
            recorder.record(duration_seconds=5, output_file=output_file)
            record_end_time = datetime.utcnow()
            recorder.cleanup()
        with st.spinner("🤖 AI Processing..."):
            # ... AI processing logic ...
            transcript = transcribe_audio(output_file)
            if transcript.startswith("Error:"): st.error(transcript); st.stop()
            simple_summary_text = summarize_transcript_simple(transcript)
            clinical_data_dict = summarize_transcript_clinical(transcript)
        with st.spinner("💾 Saving..."):
            # ... saving logic ...
            segment = ConversationSegment(end_time=record_end_time, transcript=transcript)
            summary = ConversationSummary(segment_id=segment.segment_id, simple_summary=simple_summary_text, **clinical_data_dict)
            save_conversation(segment, summary)
        st.success("Recording Processed and Saved!")
        st.info("Data added. Check the Caregiver Dashboard.")
        try:
            os.remove(output_file)
        except:
            pass
    else:
        st.info("Click to simulate a conversation.")

