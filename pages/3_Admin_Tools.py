import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical
import os
from datetime import datetime, time, date
from src.schemas import Medication, ConversationSegment, ConversationSummary
from src.database import save_conversation, add_medication, get_all_medications, update_medication, delete_medication

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin & Caregiver Tools")
st.divider()

# Session state to track which medication is being edited
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
                    schedule_info = f"**{med.get('time_to_take', '')} - {med.get('name', '')}** ({med.get('dosage', '')})"
                    stype = med.get('schedule_type')
                    if stype == 'Weekly':
                        days = ", ".join(med.get('days_of_week', []))
                        schedule_info += f" — *Weekly on {days}*"
                    elif stype == 'One-Time':
                        sdate = med.get('specific_date')
                        # Ensure sdate is a date object before formatting
                        if isinstance(sdate, datetime): 
                            sdate = sdate.date()
                        schedule_info += f" — *One-time on {sdate.strftime('%Y-%m-%d')}*"
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
                        if st.session_state.editing_med_id == med_id:
                            st.session_state.editing_med_id = None
                        st.rerun()
    
    st.divider()

    # --- THE DYNAMIC MEDICATION FORM (NO LONGER USES st.form) ---
    med_to_edit = next((med for med in medications if med.get('_id') == st.session_state.editing_med_id), None)
    form_title = "Edit Medication" if med_to_edit else "Add a New Medication"
    st.subheader(form_title)
    
    # --- Pre-fill form fields if we are in edit mode ---
    default_name = med_to_edit.get('name', '') if med_to_edit else ''
    default_dosage = med_to_edit.get('dosage', '') if med_to_edit else ''
    default_purpose = med_to_edit.get('purpose', '') if med_to_edit else ''
    default_time_str = med_to_edit.get('time_to_take', '08:00 AM') if med_to_edit else '08:00 AM'
    try:
        default_time = datetime.strptime(default_time_str, '%I:%M %p').time()
    except:
        default_time = time(8, 0)
    
    schedule_type_options = ["Daily", "Weekly", "One-Time"]
    default_stype_index = schedule_type_options.index(med_to_edit.get('schedule_type', 'Daily')) if med_to_edit else 0
    default_days = med_to_edit.get('days_of_week', []) if med_to_edit else []
    default_sdate_raw = med_to_edit.get('specific_date') if med_to_edit else date.today()
    default_sdate = default_sdate_raw.date() if isinstance(default_sdate_raw, datetime) else default_sdate_raw

    # --- Form Widgets ---
    med_name = st.text_input("Medication Name", value=default_name, key="med_name")
    med_dosage = st.text_input("Dosage", value=default_dosage, key="med_dosage")
    med_purpose = st.text_input("Purpose", value=default_purpose, key="med_purpose")
    # FIX: Set step to 60 seconds (1 minute)
    med_time = st.time_input("Time to Take", value=default_time, key="med_time", step=60)

    st.subheader("Scheduling Options")
    schedule_type = st.radio("Schedule Type", schedule_type_options, index=default_stype_index, horizontal=True, key="schedule_type")
    
    days_of_week = None
    specific_date = None
    
    if schedule_type == 'Weekly':
        days_of_week = st.multiselect("Select days of the week", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], default=default_days, key="days_of_week")
    elif schedule_type == 'One-Time':
        specific_date = st.date_input("Select the date", value=default_sdate, key="specific_date")

    # --- Submission Buttons ---
    form_col1, form_col2 = st.columns([3, 1])
    with form_col1:
        submit_button_text = "Update Medication" if med_to_edit else "Add Medication"
        if st.button(submit_button_text, type="primary", use_container_width=True):
            
            is_valid = all([med_name, med_dosage, med_purpose]) and \
                       (schedule_type != 'Weekly' or days_of_week) and \
                       (schedule_type != 'One-Time' or specific_date)
            
            if not is_valid:
                st.error("Please fill out all required fields for the selected schedule type.")
            else:
                time_str = med_time.strftime("%I:%M %p")

                # FINAL FIX: Convert date object to datetime object for MongoDB
                final_specific_date = None
                if schedule_type == 'One-Time' and specific_date:
                    final_specific_date = datetime.combine(specific_date, time(0, 0))

                update_data = {
                    "name": med_name, "dosage": med_dosage, "purpose": med_purpose,
                    "time_to_take": time_str, "schedule_type": schedule_type,
                    "days_of_week": days_of_week if schedule_type == 'Weekly' else None,
                    "specific_date": final_specific_date
                }

                try:
                    if med_to_edit:
                        update_medication(st.session_state.editing_med_id, update_data)
                        st.success(f"Updated {med_name}!")
                        st.session_state.editing_med_id = None
                    else:
                        new_med = Medication(**update_data)
                        add_medication(new_med)
                        st.success(f"Added {med_name}!")
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"Failed to save to database.")
                    st.error(f"Error details: The database rejected the data provided. Check the terminal for the full error.")

    with form_col2:
        if med_to_edit:
            if st.button("Cancel", use_container_width=True):
                st.session_state.editing_med_id = None
                st.rerun()

# --- COLUMN 2: SIMULATE CONVERSATION (Unchanged) ---
with col2:
    st.header("Simulate a Conversation")
    st.caption("This is a developer tool for Feature #1")
    if st.button("Start 5-Second Recording", key="record_button", type="secondary", use_container_width=True):
        with st.spinner("🎤 Recording..."):
            recorder = AudioRecorder(); output_file = "temp_recording.wav"; recorder.record(duration_seconds=5, output_file=output_file)
        with st.spinner("🤖 AI Processing..."):
            transcript = transcribe_audio(output_file)
            simple_summary_text = summarize_transcript_simple(transcript)
            clinical_data_dict = summarize_transcript_clinical(transcript)
        with st.spinner("💾 Saving..."):
            segment = ConversationSegment(end_time=datetime.utcnow(), transcript=transcript, start_time=datetime.utcnow())
            summary = ConversationSummary(segment_id=segment.segment_id, simple_summary=simple_summary_text, **clinical_data_dict)
            save_conversation(segment, summary)
        st.success("Recording Processed and Saved!")
        try: os.remove(output_file)
        except: pass
    else:
        st.info("Click to simulate a conversation.")

