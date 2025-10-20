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

# --- Session state initialization ---
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
    
    # --- FIX: Function to pre-fill the form state for editing ---
    def set_edit_state(med_id):
        med_to_edit = next((m for m in medications if m.get('_id') == med_id), None)
        if med_to_edit:
            st.session_state.editing_med_id = med_id
            st.session_state.med_name = med_to_edit.get('name', '')
            st.session_state.med_dosage = med_to_edit.get('dosage', '')
            st.session_state.med_purpose = med_to_edit.get('purpose', '')
            
            time_str = med_to_edit.get('time_to_take', '08:00 AM')
            try:
                st.session_state.med_time = datetime.strptime(time_str, '%I:%M %p').time()
            except:
                st.session_state.med_time = time(8,0)

            schedule_type = med_to_edit.get('schedule_type', 'Daily')
            st.session_state.schedule_type = schedule_type

            if schedule_type == 'Weekly':
                st.session_state.days_of_week = med_to_edit.get('days_of_week', [])
            if schedule_type == 'One-Time':
                sdate_raw = med_to_edit.get('specific_date', date.today())
                st.session_state.specific_date = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw

    # --- Function to clear form state ---
    def clear_form_state():
        st.session_state.editing_med_id = None
        for key in ['med_name', 'med_dosage', 'med_purpose', 'med_time', 'schedule_type', 'days_of_week', 'specific_date']:
            if key in st.session_state:
                del st.session_state[key]

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
                        if isinstance(sdate, datetime): sdate = sdate.date()
                        schedule_info += f" — *One-time on {sdate.strftime('%Y-%m-%d')}*"
                    else: schedule_info += " — *Daily*"
                    st.markdown(schedule_info)
                    st.caption(f"Purpose: {med.get('purpose', '')}")
                with c2:
                    if st.button("Edit", key=f"edit_{med_id}", use_container_width=True, on_click=set_edit_state, args=(med_id,)):
                        pass
                    if st.button("Delete", key=f"del_{med_id}", type="secondary", use_container_width=True):
                        delete_medication(med_id)
                        clear_form_state()
                        st.rerun()
    
    st.divider()

    form_title = "Edit Medication" if st.session_state.editing_med_id else "Add a New Medication"
    st.subheader(form_title)
    
    # --- Form Widgets (now they read directly from session state) ---
    med_name = st.text_input("Medication Name", key="med_name")
    med_dosage = st.text_input("Dosage", key="med_dosage")
    med_purpose = st.text_input("Purpose", key="med_purpose")
    med_time = st.time_input("Time to Take", key="med_time", step=60)

    st.subheader("Scheduling Options")
    schedule_type = st.radio("Schedule Type", ["Daily", "Weekly", "One-Time"], horizontal=True, key="schedule_type")
    
    days_of_week = None
    specific_date = None
    if schedule_type == 'Weekly':
        days_of_week = st.multiselect("Select days", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="days_of_week")
    elif schedule_type == 'One-Time':
        specific_date = st.date_input("Select date", key="specific_date")

    # --- Submission Buttons ---
    form_col1, form_col2 = st.columns([3, 1])
    with form_col1:
        submit_button_text = "Update Medication" if st.session_state.editing_med_id else "Add Medication"
        if st.button(submit_button_text, type="primary", use_container_width=True):
            is_valid = all([st.session_state.med_name, st.session_state.med_dosage, st.session_state.med_purpose]) and \
                       (st.session_state.schedule_type != 'Weekly' or st.session_state.days_of_week) and \
                       (st.session_state.schedule_type != 'One-Time' or st.session_state.specific_date)
            
            if not is_valid:
                st.error("Please fill out all fields for the selected schedule type.")
            else:
                time_str = st.session_state.med_time.strftime("%I:%M %p")
                final_specific_date = datetime.combine(st.session_state.specific_date, time(0, 0)) if st.session_state.schedule_type == 'One-Time' else None
                
                update_data = {
                    "name": st.session_state.med_name, "dosage": st.session_state.med_dosage, "purpose": st.session_state.med_purpose,
                    "time_to_take": time_str, "schedule_type": st.session_state.schedule_type,
                    "days_of_week": st.session_state.days_of_week if st.session_state.schedule_type == 'Weekly' else None,
                    "specific_date": final_specific_date
                }
                try:
                    if st.session_state.editing_med_id:
                        update_medication(st.session_state.editing_med_id, update_data)
                        st.success(f"Updated {st.session_state.med_name}!")
                    else:
                        new_med = Medication(**update_data)
                        add_medication(new_med)
                        st.success(f"Added {st.session_state.med_name}!")
                    clear_form_state()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save to database: {e}")

    with form_col2:
        if st.session_state.editing_med_id:
            if st.button("Cancel", use_container_width=True, on_click=clear_form_state):
                pass

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

