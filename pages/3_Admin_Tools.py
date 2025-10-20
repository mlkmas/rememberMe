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

if 'editing_med_id' not in st.session_state:
    st.session_state.editing_med_id = None

col1, col2 = st.columns(2)

with col1:
    st.header("Manage Medication Schedule")
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
                    schedule_info = f"**{med.get('time_to_take', '')} - {med.get('name', '')}** ({med.get('dosage', '')})"
                    if med.get('frequency') == 'Weekly':
                        days = ", ".join(med.get('days_of_week', []))
                        schedule_info += f" — *Weekly on {days}*"
                    else:
                        schedule_info += " — *Daily*"
                    st.markdown(schedule_info)
                    st.caption(f"Purpose: {med.get('purpose', '')}")
                with c2:
                    if st.button("Edit", key=f"edit_{med_id}", use_container_width=True):
                        st.session_state.editing_med_id = med_id
                        st.rerun()
                    if st.button("Delete", key=f"del_{med_id}", type="secondary", use_container_width=True):
                        delete_medication(med_id)
                        st.session_state.editing_med_id = None # Clear edit state if deleting
                        st.rerun()
    
    st.divider()

    med_to_edit = next((med for med in medications if med.get('_id') == st.session_state.editing_med_id), None)
    form_title = "Edit Medication" if med_to_edit else "Add a New Medication"

    with st.form("medication_form", clear_on_submit=False):
        st.subheader(form_title)
        
        # Pre-fill form fields if in edit mode
        default_name = med_to_edit.get('name', '') if med_to_edit else ''
        default_dosage = med_to_edit.get('dosage', '') if med_to_edit else ''
        default_purpose = med_to_edit.get('purpose', '') if med_to_edit else ''
        default_time_str = med_to_edit.get('time_to_take', '08:00 AM') if med_to_edit else '08:00 AM'
        try:
            default_time = datetime.strptime(default_time_str, '%I:%M %p').time()
        except ValueError:
            default_time = time(8, 0)
        
        default_freq_index = 0 if (med_to_edit is None or med_to_edit.get('frequency') == 'Daily') else 1
        default_days = med_to_edit.get('days_of_week', []) if med_to_edit else []

        med_name = st.text_input("Medication Name", value=default_name)
        med_dosage = st.text_input("Dosage", value=default_dosage)
        med_purpose = st.text_input("Purpose", value=default_purpose)
        med_time = st.time_input("Time to Take", value=default_time, step=60) # <-- FIX: step=60 allows minute selection

        # --- NEW SCHEDULING FIELDS ---
        st.subheader("Scheduling Options")
        frequency = st.radio("Frequency", ["Daily", "Weekly"], index=default_freq_index, horizontal=True)
        days_of_week = None
        if frequency == 'Weekly':
            days_of_week = st.multiselect(
                "Select days of the week",
                options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=default_days
            )

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
        if not all([med_name, med_dosage, med_purpose]) or (frequency == 'Weekly' and not days_of_week):
            st.error("Please fill out all required fields.")
        else:
            time_str = med_time.strftime("%I:%M %p")
            update_data = {
                "name": med_name,
                "dosage": med_dosage,
                "purpose": med_purpose,
                "time_to_take": time_str,
                "frequency": frequency,
                "days_of_week": days_of_week if frequency == 'Weekly' else None
            }
            if med_to_edit:
                update_medication(st.session_state.editing_med_id, update_data)
                st.success(f"Updated {med_name} successfully!")
                st.session_state.editing_med_id = None
            else:
                new_med = Medication(**update_data)
                add_medication(new_med)
                st.success(f"Added {med_name} to the schedule!")
            st.rerun()

with col2:
    st.header("Simulate a Conversation")
    st.caption("This is a developer tool for Feature #1")
    if st.button("Start 5-Second Recording", key="record_button", type="secondary", use_container_width=True):
        with st.spinner("🎤 Recording..."):
            recorder = AudioRecorder()
            output_file = "temp_recording.wav"
            recorder.record(duration_seconds=5, output_file=output_file)
        with st.spinner("🤖 AI Processing..."):
            transcript = transcribe_audio(output_file)
            if transcript.startswith("Error:"): st.error(transcript); st.stop()
            simple_summary_text = summarize_transcript_simple(transcript)
            clinical_data_dict = summarize_transcript_clinical(transcript)
        with st.spinner("💾 Saving..."):
            segment = ConversationSegment(end_time=datetime.utcnow(), transcript=transcript, start_time=datetime.utcnow())
            summary = ConversationSummary(segment_id=segment.segment_id, simple_summary=simple_summary_text, **clinical_data_dict)
            save_conversation(segment, summary)
        st.success("Recording Processed and Saved!")
        try:
            os.remove(output_file)
        except: pass
    else:
        st.info("Click to simulate a conversation.")

