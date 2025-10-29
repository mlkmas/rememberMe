# pages/3_Admin_Tools.py
import streamlit as st
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical
import os
from datetime import datetime, time, date, timedelta
from src.schemas import Medication, ConversationSegment, ConversationSummary, PersonProfile
from src.database import (
    save_conversation, add_medication, get_all_medications, update_medication,
    delete_medication, add_person, get_all_people, delete_person,
    update_person
)
from pathlib import Path
import face_recognition
import numpy as np

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin & Caregiver Tools")
st.divider()

# --- State Initialization ---
if 'editing_med_id' not in st.session_state:
    st.session_state.editing_med_id = None
if 'editing_person_id' not in st.session_state:
    st.session_state.editing_person_id = None
# This is the "source of truth" for the schedule type
if 'schedule_type' not in st.session_state:
    st.session_state.schedule_type = "Daily"

# --- UI Layout ---
col1, col2, col3 = st.columns(3)

# --- COLUMN 1: MANAGE MEDICATIONS ---
with col1:
    st.header("Manage Medication Schedule")
    st.subheader("Current Medication Schedule")
    medications = get_all_medications()


    # --- Callbacks and Logic ---
    def set_edit_state_med(med_id):
        med_to_edit = next((m for m in medications if m.get('_id') == med_id), None)
        if med_to_edit:
            st.session_state.editing_med_id = med_id
            st.session_state.med_name = med_to_edit.get('name', '')
            st.session_state.med_dosage = med_to_edit.get('dosage', '')
            st.session_state.med_purpose = med_to_edit.get('purpose', '')
            time_str = med_to_edit.get('time_to_take', '08:00 AM')
            try:
                st.session_state.med_time = datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                st.session_state.med_time = time(8, 0)

            # This is the important part: set the "source of truth"
            schedule_type = med_to_edit.get('schedule_type', 'Daily')
            st.session_state.schedule_type = schedule_type

            if schedule_type == 'Weekly':
                st.session_state.days_of_week = med_to_edit.get('days_of_week', [])
            if schedule_type == 'One-Time':
                sdate_raw = med_to_edit.get('specific_date', None)
                if isinstance(sdate_raw, datetime):
                    st.session_state.specific_date = sdate_raw.date()
                elif isinstance(sdate_raw, date):
                    st.session_state.specific_date = sdate_raw
                else:
                    st.session_state.specific_date = date.today()


    def clear_form_state_med():
        st.session_state.editing_med_id = None
        # Clear all form fields
        keys_to_clear = ['med_name', 'med_dosage', 'med_purpose', 'med_time',
                         'days_of_week', 'specific_date']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        # --- FIX: Manually reset the "source of truth" ---
        # This is safe because the radio button will just read this value
        st.session_state.schedule_type = 'Daily'


    # --- Display Current Medications (No changes here) ---
    if not medications:
        st.info("No medications added yet.")
    else:
        for med in medications:
            med_id = str(med.get('_id'))
            with st.container(border=True):
                c1a, c2a = st.columns([3, 1])
                with c1a:
                    stype = med.get('schedule_type', 'Daily')
                    time_to_take = med.get('time_to_take', 'N/A')
                    name = med.get('name', 'N/A')
                    dosage = med.get('dosage', 'N/A')
                    schedule_info = f"**{time_to_take} - {name}** ({dosage})"
                    if stype == 'Weekly':
                        days = med.get('days_of_week', [])
                        schedule_info += f" — *Weekly on {', '.join(days)}*" if days else " — *Weekly*"
                    elif stype == 'One-Time':
                        sdate = med.get('specific_date')
                        sdate_str = "N/A"
                        if isinstance(sdate, datetime):
                            sdate_str = sdate.strftime('%Y-%m-%d')
                        elif isinstance(sdate, date):
                            sdate_str = sdate.strftime('%Y-%m-%d')
                        schedule_info += f" — *One-time on {sdate_str}*"
                    else:
                        schedule_info += " — *Daily*"
                    st.markdown(schedule_info)
                    st.caption(f"Purpose: {med.get('purpose', 'N/A')}")
                with c2a:
                    st.button("Edit", key=f"edit_med_{med_id}", use_container_width=True, on_click=set_edit_state_med,
                              args=(med_id,))
                    if st.button("Delete", key=f"del_med_{med_id}", type="secondary", use_container_width=True):
                        delete_medication(med_id)
                        if st.session_state.editing_med_id == med_id:
                            clear_form_state_med()
                        st.rerun()
    st.divider()

    # --- Medication Add/Edit Form ---
    form_title_med = "Edit Medication" if st.session_state.editing_med_id else "Add New Medication"
    st.subheader(form_title_med)
    submit_button_text_med = "Update Medication" if st.session_state.editing_med_id else "Add Medication"


    # --- FIX: Use an on_change callback ---

    # This function will be called *by* the radio button
    # It updates the "source of truth"
    def on_schedule_type_change():
        # 'radio_schedule_key' is the widget's key
        # 'schedule_type' is our app's "source of truth"
        st.session_state.schedule_type = st.session_state.radio_schedule_key


    schedule_options = ["Daily", "Weekly", "One-Time"]
    # The radio button reads its default index from our "source of truth"
    current_schedule_index = schedule_options.index(st.session_state.schedule_type)

    # This radio button is outside the form and updates state immediately
    st.radio(
        "Schedule Type",
        options=schedule_options,
        index=current_schedule_index,
        horizontal=True,
        key='radio_schedule_key',  # Give the widget its own key
        on_change=on_schedule_type_change  # Tell it to run our function when clicked
    )

    # The form starts *after* the radio button
    with st.form(key="med_form", clear_on_submit=True):
        med_name = st.text_input("Medication Name", value=st.session_state.get('med_name', ''))
        med_dosage = st.text_input("Dosage", value=st.session_state.get('med_dosage', ''))
        med_purpose = st.text_input("Purpose", value=st.session_state.get('med_purpose', ''))
        med_time = st.time_input("Time to Take", value=st.session_state.get('med_time', time(8, 0)),
                                 step=timedelta(minutes=1))

        # These widgets now read from 'st.session_state.schedule_type'
        # This works because the radio button (outside) updates it
        days_of_week_val = None
        specific_date_val = None

        if st.session_state.schedule_type == 'Weekly':
            days_of_week_val = st.multiselect(
                "Select days",
                options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=st.session_state.get('days_of_week', [])
            )
        elif st.session_state.schedule_type == 'One-Time':
            specific_date_val = st.date_input(
                "Select date",
                value=st.session_state.get('specific_date', date.today())
            )

        # Submit button
        submitted = st.form_submit_button(submit_button_text_med, type="primary", use_container_width=True)

        if submitted:
            if not all([med_name, med_dosage, med_purpose]):
                st.error("Please fill out Medication Name, Dosage, and Purpose.")
            else:
                time_str = med_time.strftime("%I:%M %p")
                final_specific_date = None

                # The form also reads from the "source of truth" when saving
                schedule_type_to_save = st.session_state.schedule_type

                if schedule_type_to_save == 'One-Time' and specific_date_val:
                    final_specific_date = datetime.combine(specific_date_val, time(0, 0))

                med_data = {
                    "name": med_name,
                    "dosage": med_dosage,
                    "purpose": med_purpose,
                    "time_to_take": time_str,
                    "schedule_type": schedule_type_to_save,
                    "days_of_week": days_of_week_val if schedule_type_to_save == 'Weekly' else None,
                    "specific_date": final_specific_date
                }

                try:
                    if st.session_state.editing_med_id:
                        update_medication(st.session_state.editing_med_id, med_data)
                        st.success(f"Updated {med_name}!")
                    else:
                        new_med = Medication(**med_data)
                        add_medication(new_med)
                        st.success(f"Added {med_name}!")

                    # This is now safe, as it only touches 'schedule_type'
                    clear_form_state_med()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save medication: {e}")

    # Cancel button
    if st.session_state.editing_med_id:
        if st.button("Cancel Edit", key="cancel_med", use_container_width=True, on_click=clear_form_state_med):
            st.rerun()

# --- COLUMN 2: MANAGE PEOPLE (No changes needed) ---
with col2:
    st.header("Manage People Profiles")
    st.caption("Add photos and details for people the patient interacts with.")

    st.subheader("Registered People")
    people = get_all_people()
    if not people:
        st.info("No people profiles added yet.")
    else:
        for person in people:
            person_id = str(person.get('_id'))
            with st.container(border=True):
                p_c1, p_c2, p_c3 = st.columns([1, 3, 1])
                with p_c1:
                    photo_path = person.get('photo_url', 'https://via.placeholder.com/150')
                    if Path(photo_path).is_file():
                        st.image(photo_path, width=60)
                    else:
                        st.image('https://via.placeholder.com/150', width=60)
                with p_c2:
                    st.markdown(f"**{person.get('name', 'N/A')}**")
                    st.caption(f"Relationship: {person.get('relationship', 'N/A')}")
                    if person.get("face_encoding"):
                        st.caption("✅ Face data saved")
                    else:
                        st.caption("⚠️ No face data")
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
                photo_url_to_save = "https://via.placeholder.com/150"
                face_encoding_list = None
                person_id = None

                image_dir = Path("images")
                image_dir.mkdir(parents=True, exist_ok=True)

                if uploaded_photo is not None:
                    try:
                        safe_filename = f"{person_name.lower().replace(' ', '_')}_{uploaded_photo.name}"
                        file_path = image_dir / safe_filename

                        with open(file_path, "wb") as f:
                            f.write(uploaded_photo.getbuffer())
                        photo_url_to_save = str(file_path)

                        print(f"--- DEBUG: Analyzing face for photo: {file_path} ---")
                        with st.spinner("Analyzing face..."):
                            image = face_recognition.load_image_file(file_path)
                            encodings = face_recognition.face_encodings(image)

                            if encodings:
                                face_encoding_list = encodings[0].tolist()
                                print(f"--- DEBUG: Face detected! Encoding starts with: {face_encoding_list[:5]} ---")
                                st.success(f"Photo '{uploaded_photo.name}' saved and face analyzed!")
                            else:
                                print("--- DEBUG: No face detected in the photo. ---")
                                st.warning("Photo saved, but no face found.")

                    except Exception as e:
                        st.error(f"Error saving or analyzing photo: {e}")
                        print(f"--- DEBUG: Error during photo processing: {e} ---")
                else:
                    st.warning("No photo uploaded, using placeholder.")

                new_person = PersonProfile(
                    name=person_name,
                    relationship=person_relationship,
                    photo_url=photo_url_to_save,
                    notes=person_notes
                )

                print(f"--- DEBUG: Attempting to add person: {person_name} ---")
                person_id = add_person(new_person)

                if person_id and face_encoding_list:
                    try:
                        print(f"--- DEBUG: Attempting to update person ID {person_id} with encoding ---")
                        update_person(person_id, {"face_encoding": face_encoding_list})
                        print(f"--- DEBUG: Update person called successfully for ID {person_id} ---")
                        st.success("Face encoding saved to database.")
                    except Exception as e:
                        st.error(f"Failed to save face encoding: {e}")
                        print(f"--- DEBUG: Error calling update_person: {e} ---")
                elif person_id:
                    print(
                        f"--- DEBUG: Person {person_id} added, but no face encoding to save (face not detected or no photo). ---")
                else:
                    print(
                        f"--- DEBUG: Failed to add person {person_name} (already exists or DB error), cannot save encoding. ---")
                    st.warning(f"Could not add {person_name}, possibly already exists.")
            else:
                st.error("Please provide at least Name and Relationship.")

# --- COLUMN 3: SIMULATE CONVERSATION (No changes needed) ---
with col3:
    st.header("Simulate a Conversation")
    st.caption("This is a developer tool for Feature #1")

    pyaudio_installed = True
    try:
        import pyaudio
    except ImportError:
        pyaudio_installed = False
        st.warning("PyAudio not installed. Recording feature disabled. Run 'pip install PyAudio'.")

    if st.button("Start 5-Second Recording", key="record_button", type="secondary", use_container_width=True,
                 disabled=not pyaudio_installed):
        output_file = "temp_recording.wav"
        try:
            with st.spinner("🎤 Recording..."):
                recorder = AudioRecorder()
                start_time = datetime.utcnow()
                recorder.record(duration_seconds=5, output_file=output_file)
                end_time = datetime.utcnow()
                recorder.cleanup()

            with st.spinner("🤖 Transcribing..."):
                transcript = transcribe_audio(output_file)
                if not transcript or transcript.startswith("Error:"):
                    raise Exception(f"Transcription failed: {transcript}")
                st.write(f"Transcript: {transcript}")

            with st.spinner("✨ Summarizing..."):
                simple_summary_text = summarize_transcript_simple(transcript)
                clinical_data_dict = summarize_transcript_clinical(transcript)
                if "error" in clinical_data_dict or simple_summary_text.startswith("Error:"):
                    st.error(f"Simple Summary: {simple_summary_text}")
                    st.error(f"Clinical Summary: {clinical_data_dict}")
                    raise Exception(f"Summarization failed.")
                st.write(f"Simple Summary: {simple_summary_text}")

            with st.spinner("💾 Saving..."):
                segment = ConversationSegment(start_time=start_time, end_time=end_time, transcript=transcript)
                summary_data = {
                    "segment_id": str(segment.id),
                    "simple_summary": simple_summary_text,
                    **clinical_data_dict
                }
                summary = ConversationSummary(**summary_data)
                save_conversation(segment, summary)

            st.success("Recording Processed and Saved!")
            st.toast("Refreshing dashboard...")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            print(f"--- DEBUG: Error in simulation: {e} ---")
        finally:
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception as remove_e:
                    st.warning(f"Could not remove temporary file {output_file}: {remove_e}")
    else:
        if pyaudio_installed:
            st.info("Click the button above to simulate a 5-second conversation.")