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
    delete_medication, add_person, get_all_people, delete_person, update_person
)
from pathlib import Path
import face_recognition
import numpy as np

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")
st.title("🛠️ Admin & Caregiver Tools")
st.divider()

# --- Initialize Session State for Dialogs ---
if 'show_med_dialog' not in st.session_state:
    st.session_state.show_med_dialog = False
if 'show_person_dialog' not in st.session_state:
    st.session_state.show_person_dialog = False
if 'editing_med_id' not in st.session_state:
    st.session_state.editing_med_id = None
if 'editing_med_data' not in st.session_state:
    st.session_state.editing_med_data = None

# --- UI Layout ---
col1, col2, col3 = st.columns(3)

# ========================================
# COLUMN 1: MEDICATIONS
# ========================================
with col1:
    st.header("💊 Manage Medications")

    # Add Button (opens dialog)
    if st.button("➕ Add New Medication", use_container_width=True, type="primary"):
        st.session_state.show_med_dialog = True
        st.session_state.editing_med_id = None
        st.session_state.editing_med_data = None
        st.rerun()

    st.divider()

    # Display Current Medications
    st.subheader("Current Medication Schedule")
    medications = get_all_medications()

    if not medications:
        st.info("No medications added yet.")
    else:
        for med in medications:
            med_id = str(med.get('_id'))
            with st.container(border=True):
                # Header row
                col_info, col_actions = st.columns([3, 1])

                with col_info:
                    stype = med.get('schedule_type', 'Daily')
                    time_str = med.get('time_to_take', 'N/A')
                    name = med.get('name', 'N/A')
                    dosage = med.get('dosage', 'N/A')

                    st.markdown(f"**⏰ {time_str} - {name}**")
                    st.caption(f"Dosage: {dosage}")
                    st.caption(f"Purpose: {med.get('purpose', 'N/A')}")

                    # Schedule info
                    if stype == 'Weekly':
                        days = med.get('days_of_week', [])
                        st.caption(f"📅 Weekly: {', '.join(days) if days else 'Not set'}")
                    elif stype == 'One-Time':
                        sdate = med.get('specific_date')
                        if isinstance(sdate, datetime):
                            st.caption(f"📅 One-time: {sdate.strftime('%Y-%m-%d')}")
                    else:
                        st.caption("📅 Daily")

                with col_actions:
                    # Edit button
                    if st.button("✏️", key=f"edit_med_{med_id}", use_container_width=True):
                        st.session_state.show_med_dialog = True
                        st.session_state.editing_med_id = med_id
                        st.session_state.editing_med_data = med
                        st.rerun()

                    # Delete button
                    if st.button("🗑️", key=f"del_med_{med_id}", type="secondary", use_container_width=True):
                        delete_medication(med_id)
                        st.rerun()

# ========================================
# COLUMN 2: PEOPLE
# ========================================
with col2:
    st.header("👥 Manage People Profiles")

    # Add Button (opens dialog)
    if st.button("➕ Add New Person", use_container_width=True, type="primary"):
        st.session_state.show_person_dialog = True
        st.rerun()

    st.divider()

    st.subheader("Registered People")
    people = get_all_people()

    if not people:
        st.info("No people profiles added yet.")
    else:
        for person in people:
            person_id = str(person.get('_id'))
            with st.container(border=True):
                p_col1, p_col2, p_col3 = st.columns([1, 3, 1])

                with p_col1:
                    photo_path = person.get('photo_url', 'https://via.placeholder.com/150')
                    if Path(photo_path).is_file():
                        st.image(photo_path, width=60)
                    else:
                        st.image('https://via.placeholder.com/150', width=60)

                with p_col2:
                    st.markdown(f"**{person.get('name', 'N/A')}**")
                    st.caption(f"{person.get('relationship', 'N/A')}")
                    if person.get("face_encoding"):
                        st.caption("✅ Face data saved")
                    else:
                        st.caption("⚠️ No face data")

                with p_col3:
                    if st.button("🗑️", key=f"del_person_{person_id}", use_container_width=True):
                        delete_person(person_id)
                        st.rerun()

# ========================================
# COLUMN 3: SIMULATE CONVERSATION
# ========================================
with col3:
    st.header("🎤 Test Conversation")
    st.caption("Quick test for recording pipeline")

    pyaudio_installed = True
    try:
        import pyaudio
    except ImportError:
        pyaudio_installed = False
        st.warning("PyAudio not installed. Recording disabled.")

    if st.button("🔴 Record 5 Seconds", use_container_width=True, type="secondary", disabled=not pyaudio_installed):
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
                st.success(f"✅ Transcript: {transcript[:100]}...")

            with st.spinner("✨ Summarizing..."):
                simple_summary = summarize_transcript_simple(transcript)
                clinical_data = summarize_transcript_clinical(transcript)

                if "error" in clinical_data or simple_summary.startswith("Error:"):
                    raise Exception("Summarization failed")

            with st.spinner("💾 Saving..."):
                segment = ConversationSegment(
                    start_time=start_time,
                    end_time=end_time,
                    transcript=transcript
                )

                summary = ConversationSummary(
                    segment_id=str(segment.id),
                    simple_summary=simple_summary,
                    **clinical_data
                )

                save_conversation(segment, summary)

            st.success("🎉 Recording saved to dashboard!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")
        finally:
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass

    st.divider()
    st.caption("This simulates a 5-second conversation and saves it to the database.")


# ========================================
# MEDICATION DIALOG (POPUP)
# ========================================
@st.dialog("💊 Medication Details", width="large")
def medication_dialog():
    """Dialog popup for adding/editing medications"""

    # Determine if editing or adding
    is_editing = st.session_state.editing_med_id is not None
    med_data = st.session_state.editing_med_data or {}

    st.subheader("✏️ Edit Medication" if is_editing else "➕ Add New Medication")

    # Form fields with pre-filled data if editing
    med_name = st.text_input(
        "Medication Name *",
        value=med_data.get('name', ''),
        placeholder="e.g., Ibuprofen"
    )

    med_dosage = st.text_input(
        "Dosage *",
        value=med_data.get('dosage', ''),
        placeholder="e.g., 200mg"
    )

    med_purpose = st.text_input(
        "Purpose *",
        value=med_data.get('purpose', ''),
        placeholder="e.g., Pain relief"
    )

    # Time picker
    default_time = time(8, 0)
    if is_editing and med_data.get('time_to_take'):
        try:
            default_time = datetime.strptime(med_data['time_to_take'], '%I:%M %p').time()
        except:
            pass

    med_time = st.time_input(
        "Time to Take *",
        value=default_time,
        step=timedelta(minutes=15)
    )

    st.divider()

    # Schedule type
    schedule_options = ["Daily", "Weekly", "One-Time"]
    current_schedule = med_data.get('schedule_type', 'Daily')
    schedule_index = schedule_options.index(current_schedule) if current_schedule in schedule_options else 0

    schedule_type = st.radio(
        "Schedule Type",
        options=schedule_options,
        index=schedule_index,
        horizontal=True
    )

    # Conditional fields based on schedule type
    days_of_week = None
    specific_date = None

    if schedule_type == 'Weekly':
        days_of_week = st.multiselect(
            "Select Days",
            options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=med_data.get('days_of_week', [])
        )

    elif schedule_type == 'One-Time':
        default_date = date.today()
        if is_editing and med_data.get('specific_date'):
            if isinstance(med_data['specific_date'], datetime):
                default_date = med_data['specific_date'].date()
            elif isinstance(med_data['specific_date'], date):
                default_date = med_data['specific_date']

        specific_date = st.date_input(
            "Select Date",
            value=default_date
        )

    st.divider()

    # Action buttons
    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Save" if is_editing else "➕ Add", type="primary", use_container_width=True):
            # Validation
            if not all([med_name, med_dosage, med_purpose]):
                st.error("⚠️ Please fill out all required fields (*)")
                st.stop()

            # Prepare data
            time_str = med_time.strftime("%I:%M %p")
            final_specific_date = None

            if schedule_type == 'One-Time' and specific_date:
                final_specific_date = datetime.combine(specific_date, time(0, 0))

            med_dict = {
                "name": med_name,
                "dosage": med_dosage,
                "purpose": med_purpose,
                "time_to_take": time_str,
                "schedule_type": schedule_type,
                "days_of_week": days_of_week if schedule_type == 'Weekly' else None,
                "specific_date": final_specific_date
            }

            try:
                if is_editing:
                    # Update existing
                    update_medication(st.session_state.editing_med_id, med_dict)
                    st.success(f"✅ Updated {med_name}!")
                else:
                    # Add new
                    new_med = Medication(**med_dict)
                    add_medication(new_med)
                    st.success(f"✅ Added {med_name}!")

                # Close dialog and refresh
                st.session_state.show_med_dialog = False
                st.session_state.editing_med_id = None
                st.session_state.editing_med_data = None
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to save: {e}")

    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_med_dialog = False
            st.session_state.editing_med_id = None
            st.session_state.editing_med_data = None
            st.rerun()


# ========================================
# PERSON DIALOG (POPUP)
# ========================================
@st.dialog("👤 Person Profile", width="large")
def person_dialog():
    """Dialog popup for adding people"""

    st.subheader("➕ Add New Person")

    person_name = st.text_input("Name *", placeholder="e.g., Sarah")
    person_relationship = st.text_input("Relationship *", placeholder="e.g., Daughter, Son, Caregiver")
    person_notes = st.text_area("Notes (Optional)", placeholder="e.g., Lives in Tel Aviv, visits every Sunday")
    uploaded_photo = st.file_uploader("Upload Photo", type=["jpg", "png", "jpeg"])

    st.divider()

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Add Person", type="primary", use_container_width=True):
            if not person_name or not person_relationship:
                st.error("⚠️ Please provide Name and Relationship")
                st.stop()

            photo_url_to_save = "https://via.placeholder.com/150"
            face_encoding_list = None

            # Handle photo upload
            if uploaded_photo is not None:
                try:
                    image_dir = Path("images")
                    image_dir.mkdir(parents=True, exist_ok=True)

                    safe_filename = f"{person_name.lower().replace(' ', '_')}_{uploaded_photo.name}"
                    file_path = image_dir / safe_filename

                    with open(file_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())
                    photo_url_to_save = str(file_path)

                    # Face detection
                    with st.spinner("🔍 Analyzing face..."):
                        image = face_recognition.load_image_file(file_path)
                        encodings = face_recognition.face_encodings(image)

                        if encodings:
                            face_encoding_list = encodings[0].tolist()
                            st.success("✅ Face detected and saved!")
                        else:
                            st.warning("⚠️ Photo saved, but no face detected")

                except Exception as e:
                    st.error(f"❌ Error processing photo: {e}")

            # Save person
            try:
                new_person = PersonProfile(
                    name=person_name,
                    relationship=person_relationship,
                    photo_url=photo_url_to_save,
                    notes=person_notes
                )

                person_id = add_person(new_person)

                # Update with face encoding if detected
                if person_id and face_encoding_list:
                    update_person(person_id, {"face_encoding": face_encoding_list})

                st.success(f"✅ Added {person_name}!")
                st.session_state.show_person_dialog = False
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to save: {e}")

    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_person_dialog = False
            st.rerun()


# ========================================
# SHOW DIALOGS IF TRIGGERED
# ========================================
if st.session_state.show_med_dialog:
    medication_dialog()

if st.session_state.show_person_dialog:
    person_dialog()