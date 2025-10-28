# pages/3_Admin_Tools.py
import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical
import os
from datetime import datetime, time, date
from src.schemas import Medication, ConversationSegment, ConversationSummary, PersonProfile
from src.database import (
    save_conversation, add_medication, get_all_medications, update_medication,
    delete_medication, add_person, get_all_people, delete_person, 
    update_person # <-- ADDED IMPORT
)
from pathlib import Path # <-- ADDED IMPORT
import face_recognition # <-- ADDED IMPORT
import numpy as np # <-- ADDED IMPORT

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin & Caregiver Tools")
st.divider()

if 'editing_med_id' not in st.session_state: st.session_state.editing_med_id = None
if 'editing_person_id' not in st.session_state: st.session_state.editing_person_id = None 

col1, col2, col3 = st.columns(3)

# --- COLUMN 1: MANAGE MEDICATIONS (Unchanged) ---
with col1:
    st.header("Manage Medication Schedule")
    st.subheader("Current Medication Schedule")
    medications = get_all_medications()
    
    def set_edit_state_med(med_id):
        med_to_edit = next((m for m in medications if m.get('_id') == med_id), None)
        if med_to_edit:
            st.session_state.editing_med_id = med_id; st.session_state.med_name = med_to_edit.get('name', ''); st.session_state.med_dosage = med_to_edit.get('dosage', ''); st.session_state.med_purpose = med_to_edit.get('purpose', '')
            time_str = med_to_edit.get('time_to_take', '08:00 AM');
            try: st.session_state.med_time = datetime.strptime(time_str, '%I:%M %p').time()
            except: st.session_state.med_time = time(8,0)
            schedule_type = med_to_edit.get('schedule_type', 'Daily'); st.session_state.schedule_type = schedule_type
            if schedule_type == 'Weekly': st.session_state.days_of_week = med_to_edit.get('days_of_week', [])
            if schedule_type == 'One-Time': sdate_raw = med_to_edit.get('specific_date', date.today()); st.session_state.specific_date = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw

    def clear_form_state_med():
        st.session_state.editing_med_id = None
        for key in ['med_name', 'med_dosage', 'med_purpose', 'med_time', 'schedule_type', 'days_of_week', 'specific_date']:
            if key in st.session_state: del st.session_state[key]

    if not medications: st.info("No medications added yet.")
    else:
        for med in medications:
            med_id = med.get('_id')
            with st.container(border=True):
                c1a, c2a = st.columns([3, 1])
                with c1a:
                    stype = med.get('schedule_type'); schedule_info = f"**{med.get('time_to_take', '')} - {med.get('name', '')}** ({med.get('dosage', '')})"
                    if stype == 'Weekly': schedule_info += f" — *Weekly on {', '.join(med.get('days_of_week', []))}*"
                    elif stype == 'One-Time': sdate = med.get('specific_date'); schedule_info += f" — *One-time on {(sdate.date() if isinstance(sdate, datetime) else sdate).strftime('%Y-%m-%d')}*"
                    else: schedule_info += " — *Daily*"
                    st.markdown(schedule_info); st.caption(f"Purpose: {med.get('purpose', '')}")
                with c2a:
                    if st.button("Edit", key=f"edit_med_{med_id}", use_container_width=True, on_click=set_edit_state_med, args=(med_id,)): pass
                    if st.button("Delete", key=f"del_med_{med_id}", type="secondary", use_container_width=True):
                        delete_medication(med_id);
                        if st.session_state.editing_med_id == med_id: clear_form_state_med()
                        st.rerun()
    st.divider()

    form_title_med = "Edit Medication" if st.session_state.editing_med_id else "Add New Medication"
    st.subheader(form_title_med)
    submit_button_text_med = "Update Medication" if st.session_state.editing_med_id else "Add Medication"
    with st.form(key="med_form", clear_on_submit=True):
        med_name = st.text_input("Medication Name", value=st.session_state.get('med_name', ''))
        med_dosage = st.text_input("Dosage", value=st.session_state.get('med_dosage', ''))
        med_purpose = st.text_input("Purpose", value=st.session_state.get('med_purpose', ''))
        med_time = st.time_input("Time to Take", value=st.session_state.get('med_time', time(8,0)), step=60)
        st.subheader("Scheduling Options")
        schedule_type = st.radio("Schedule Type", ["Daily", "Weekly", "One-Time"], 
                                 horizontal=True, index=["Daily", "Weekly", "One-Time"].index(st.session_state.get('schedule_type', 'Daily')))
        days_of_week, specific_date = None, None
        if schedule_type == 'Weekly': 
            days_of_week = st.multiselect("Select days", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 
                                          default=st.session_state.get('days_of_week', []))
        elif schedule_type == 'One-Time': 
            specific_date = st.date_input("Select date", value=st.session_state.get('specific_date', date.today()))
        
        submitted = st.form_submit_button(submit_button_text_med, type="primary", use_container_width=True)
        if submitted:
            is_valid = all([med_name, med_dosage, med_purpose])
            if not is_valid: st.error("Please fill out medication details.")
            else:
                time_str = med_time.strftime("%I:%M %p")
                final_specific_date = datetime.combine(specific_date, time(0, 0)) if schedule_type == 'One-Time' and specific_date else None
                update_data = {
                    "name": med_name, "dosage": med_dosage, "purpose": med_purpose, "time_to_take": time_str, 
                    "schedule_type": schedule_type, 
                    "days_of_week": days_of_week if schedule_type == 'Weekly' else None, 
                    "specific_date": final_specific_date
                }
                try:
                    if st.session_state.editing_med_id: 
                        update_medication(st.session_state.editing_med_id, update_data); st.success(f"Updated {med_name}!")
                    else: 
                        add_medication(Medication(**update_data)); st.success(f"Added {med_name}!")
                    clear_form_state_med(); st.rerun()
                except Exception as e: st.error(f"Failed to save medication: {e}")

    if st.session_state.editing_med_id:
        if st.button("Cancel", key="cancel_med", use_container_width=True, on_click=clear_form_state_med): pass

# --- COLUMN 2: MANAGE PEOPLE (Updated) ---
with col2:
    st.header("Manage People Profiles")
    st.caption("Add photos and details for people the patient interacts with.")

    st.subheader("Registered People")
    people = get_all_people()
    if not people:
        st.info("No people profiles added yet.")
    else:
        for person in people:
            person_id = person.get('_id')
            with st.container(border=True):
                p_c1, p_c2, p_c3 = st.columns([1, 3, 1])
                with p_c1:
                    photo_path = person.get('photo_url', 'https://via.placeholder.com/150')
                    if Path(photo_path).exists():
                        st.image(photo_path, width=60)
                    else:
                        st.image('https://via.placeholder.com/150', width=60)
                with p_c2:
                    st.markdown(f"**{person.get('name', 'N/A')}**")
                    st.caption(f"Relationship: {person.get('relationship', 'N/A')}")
                with p_c3:
                    if st.button("Delete", key=f"del_person_{person_id}", type="secondary", use_container_width=True):
                        delete_person(person_id)
                        st.rerun()
    st.divider()

    st.subheader("Add New Person")
    with st.form(key="person_form", clear_on_submit=True):
        person_name = st.text_input("Name")
        person_relationship = st.text_input("Relationship to Patient", placeholder="e.g., Daughter, Son")
        person_notes = st.text_area("Notes (Optional)", placeholder="e.g., Lives in Tel Aviv")
        
        uploaded_photo = st.file_uploader("Upload Photo", type=["jpg", "png", "jpeg"])
        
        person_submitted = st.form_submit_button("Add Person Profile", type="primary", use_container_width=True)
        
        if person_submitted:
            if person_name and person_relationship:
                photo_url_to_save = "https://via.placeholder.com/150" # Default
                face_encoding = None
                
                # Create a directory to store images
                image_dir = Path("images")
                image_dir.mkdir(exist_ok=True)

                if uploaded_photo is not None:
                    try:
                        file_path = image_dir / uploaded_photo.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_photo.getbuffer())
                        
                        photo_url_to_save = str(file_path) # Save local path
                        
                        # --- Face Recognition Logic ---
                        with st.spinner("Analyzing face..."):
                            image = face_recognition.load_image_file(file_path)
                            encodings = face_recognition.face_encodings(image)
                            
                            if encodings:
                                face_encoding = encodings[0].tolist() # Save encoding as a list
                                st.success(f"Photo '{uploaded_photo.name}' saved and face analyzed!")
                            else:
                                st.warning("Photo saved, but no face found.")
                        # --- End Face Recognition ---
                        
                    except Exception as e:
                        st.error(f"Error saving photo: {e}")
                
                # Save person to DB
                new_person = PersonProfile(
                    name=person_name,
                    relationship=person_relationship,
                    photo_url=photo_url_to_save,
                    notes=person_notes
                )
                person_id = add_person(new_person) # Get the ID of the new person
                
                # If we have an encoding, update the new person record
                if person_id and face_encoding:
                    try:
                        update_person(person_id, {"face_encoding": face_encoding})
                        st.success("Face encoding saved to database.")
                    except Exception as e:
                        st.error(f"Failed to save face encoding: {e}")
                
                st.rerun() # Rerun to clear form and update list
            else:
                st.error("Please provide at least Name and Relationship.")


# --- COLUMN 3: SIMULATE CONVERSATION (Moved) ---
with col3:
    st.header("Simulate a Conversation")
    st.caption("This is a developer tool for Feature #1")
    if st.button("Start 5-Second Recording", key="record_button", type="secondary", use_container_width=True):
        try:
            with st.spinner("🎤 Recording..."):
                recorder = AudioRecorder(); output_file = "temp_recording.wav"; start_time = datetime.utcnow(); recorder.record(duration_seconds=5, output_file=output_file); end_time = datetime.utcnow()
            with st.spinner("🤖 AI Processing..."):
                transcript = transcribe_audio(output_file)
                if not transcript or transcript.startswith("Error:"): raise Exception(f"Transcription failed: {transcript}")
                
                # Get both simple and clinical summaries
                simple_summary_text = summarize_transcript_simple(transcript)
                clinical_data_dict = summarize_transcript_clinical(transcript)
                
                if "error" in clinical_data_dict: raise Exception(f"Clinical summarization failed: {clinical_data_dict['error']}")
            
            with st.spinner("💾 Saving..."):
                segment = ConversationSegment(start_time=start_time, end_time=end_time, transcript=transcript)
                # Combine summaries into one record
                summary_data = {
                    "segment_id": segment.id,
                    "simple_summary": simple_summary_text,
                    **clinical_data_dict # Unpack clinical data
                }
                summary = ConversationSummary(**summary_data)
                save_conversation(segment, summary)
            st.success("Recording Processed and Saved!"); st.toast("Refreshing dashboard...")
        except Exception as e: st.error(f"Error: {e}")
        finally:
            if os.path.exists("temp_recording.wav"): os.remove("temp_recording.wav")
    else:
        st.info("Click to simulate a conversation.")