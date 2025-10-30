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

#Reset dialog states on page load
if 'page_loaded_admin' not in st.session_state:
    st.session_state.page_loaded_admin = True
    st.session_state.show_med_dialog = False
    st.session_state.show_person_dialog = False
    st.session_state.show_medication_dialog = False

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")

# Custom CSS for modern design
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Card styling */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* Header styling */
    h1, h2, h3 {
        color: #1f2937;
        font-weight: 600;
    }

    /* Divider styling */
    hr {
        margin: 1.5rem 0;
        border-color: #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛠️ Admin & Caregiver Tools")
st.caption("Manage medications, people profiles, and test recording features")
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


# --- Helper Functions for Dialog Control ---
def open_med_dialog(med_id=None, med_data=None):
    """Open medication dialog for add or edit"""
    st.session_state.show_med_dialog = True
    st.session_state.show_person_dialog = False  # Ensure person dialog is closed
    st.session_state.editing_med_id = med_id
    st.session_state.editing_med_data = med_data


def close_med_dialog():
    """Close medication dialog and reset state"""
    st.session_state.show_med_dialog = False
    st.session_state.editing_med_id = None
    st.session_state.editing_med_data = None


def open_person_dialog():
    """Open person dialog"""
    st.session_state.show_person_dialog = True
    st.session_state.show_med_dialog = False  # Ensure med dialog is closed


def close_person_dialog():
    """Close person dialog"""
    st.session_state.show_person_dialog = False


# --- UI Layout ---
col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

# ========================================
# COLUMN 1: MEDICATIONS
# ========================================
with col1:
    # Header with add button
    header_col1, header_col2 = st.columns([2, 1])
    with header_col1:
        st.markdown("### 💊 Medications")
    with header_col2:
        if st.button("➕ Add", key="add_med_btn", use_container_width=True, type="primary"):
            open_med_dialog()
            st.rerun()

    st.divider()

    # Display Current Medications
    medications = get_all_medications()

    if not medications:
        st.info("📭 No medications added yet.\nClick '➕ Add' to create one.")
    else:
        for idx, med in enumerate(medications):
            med_id = str(med.get('_id'))

            with st.container():
                # Create a nice card layout
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 12px; border-radius: 8px; margin-bottom: 10px;'>
                    <div style='color: white; font-weight: 600; font-size: 16px;'>
                        ⏰ {med.get('time_to_take', 'N/A')}
                    </div>
                    <div style='color: white; font-size: 18px; margin-top: 4px;'>
                        {med.get('name', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Details section
                info_col, btn_col = st.columns([3, 1])

                with info_col:
                    st.caption(f"💊 **Dosage:** {med.get('dosage', 'N/A')}")
                    st.caption(f"🎯 **Purpose:** {med.get('purpose', 'N/A')}")

                    # Schedule info with icons
                    stype = med.get('schedule_type', 'Daily')
                    if stype == 'Weekly':
                        days = med.get('days_of_week', [])
                        days_str = ', '.join(days[:3]) + ('...' if len(days) > 3 else '')
                        st.caption(f"📅 Weekly: {days_str}")
                    elif stype == 'One-Time':
                        sdate = med.get('specific_date')
                        if isinstance(sdate, datetime):
                            st.caption(f"📅 One-time: {sdate.strftime('%b %d, %Y')}")
                    else:
                        st.caption("📅 Daily")

                with btn_col:
                    # Stack buttons vertically instead of side-by-side
                    if st.button("✏️ ", key=f"edit_med_{med_id}", use_container_width=True):
                        open_med_dialog(med_id, med)
                        st.rerun()

                    if st.button("🗑️ ", key=f"del_med_{med_id}", use_container_width=True, type="secondary"):
                        delete_medication(med_id)
                        st.rerun()

                if idx < len(medications) - 1:
                    st.markdown("<hr style='margin: 10px 0; border-color: #e5e7eb;'>", unsafe_allow_html=True)

# ========================================
# COLUMN 2: PEOPLE
# ========================================
with col2:
    # Header with add button
    header_col1, header_col2 = st.columns([2, 1])
    with header_col1:
        st.markdown("### 👥 People")
    with header_col2:
        if st.button("➕ Add", key="add_person_btn", use_container_width=True, type="primary"):
            open_person_dialog()
            st.rerun()

    st.divider()

    people = get_all_people()

    if not people:
        st.info("📭 No people profiles yet.\nClick '➕ Add' to create one.")
    else:
        for idx, person in enumerate(people):
            person_id = str(person.get('_id'))

            with st.container():
                p_img_col, p_info_col, p_btn_col = st.columns([1, 3, 1])

                with p_img_col:
                    photo_path = person.get('photo_url', 'https://via.placeholder.com/150')
                    if Path(photo_path).is_file():
                        st.image(photo_path, width=70, use_container_width=True)
                    else:
                        st.image('https://via.placeholder.com/150', width=70, use_container_width=True)

                with p_info_col:
                    st.markdown(f"**{person.get('name', 'N/A')}**")
                    st.caption(f"👤 {person.get('relationship', 'N/A')}")

                    if person.get("face_encoding"):
                        st.caption("✅ Face recognized")
                    else:
                        st.caption("⚠️ No face data")

                with p_btn_col:
                    if st.button("🗑️", key=f"del_person_{person_id}", help="Delete", use_container_width=True):
                        delete_person(person_id)
                        st.rerun()

                if idx < len(people) - 1:
                    st.markdown("<hr style='margin: 10px 0; border-color: #e5e7eb;'>", unsafe_allow_html=True)

# ========================================
# COLUMN 3: TEST RECORDING
# ========================================
with col3:
    st.markdown("### 🎤 Test Recording")
    st.caption("Quick test of the conversation pipeline")
    st.divider()

    pyaudio_installed = True
    try:
        import pyaudio
    except ImportError:
        pyaudio_installed = False
        st.warning("⚠️ PyAudio not installed")

    # Recording section with better spacing
    st.markdown("##### Record a 5-second conversation")

    if st.button(
            "🔴 Start Recording",
            use_container_width=True,
            type="secondary",
            disabled=not pyaudio_installed
    ):
        output_file = "temp_recording.wav"

        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        try:
            # Recording
            progress_placeholder.progress(0, text="🎤 Initializing...")
            recorder = AudioRecorder()
            start_time = datetime.utcnow()

            progress_placeholder.progress(25, text="🎤 Recording... Speak now!")
            recorder.record(duration_seconds=5, output_file=output_file)
            end_time = datetime.utcnow()
            recorder.cleanup()

            # Transcription
            progress_placeholder.progress(50, text="🤖 Transcribing audio...")
            transcript = transcribe_audio(output_file)

            if not transcript or transcript.startswith("Error:"):
                raise Exception(f"Transcription failed: {transcript}")

            status_placeholder.success(f"✅ Transcript: *{transcript[:80]}...*")

            # Summarization
            progress_placeholder.progress(75, text="✨ Generating summaries...")
            simple_summary = summarize_transcript_simple(transcript)
            clinical_data = summarize_transcript_clinical(transcript)

            if "error" in clinical_data or simple_summary.startswith("Error:"):
                raise Exception("Summarization failed")

            # Save to database
            progress_placeholder.progress(90, text="💾 Saving to database...")

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

            # Complete
            progress_placeholder.progress(100, text="✅ Complete!")
            status_placeholder.success("🎉 Recording saved to dashboard!")

            # Small delay before refresh
            import time

            time.sleep(1)
            st.rerun()

        except Exception as e:
            progress_placeholder.empty()
            status_placeholder.error(f"❌ Error: {e}")
        finally:
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass

    st.divider()

    # Info box
    st.info("💡 This simulates recording a conversation and processing it through the full pipeline.")


# ========================================
# MEDICATION DIALOG (COMPACT POPUP)
# ========================================
@st.dialog("💊 Medication", width="small")  # Changed to "small" for compact size
def medication_dialog():
    """Compact dialog popup for adding/editing medications"""

    is_editing = st.session_state.editing_med_id is not None
    med_data = st.session_state.editing_med_data or {}

    st.markdown(f"**{'Edit' if is_editing else 'Add'} Medication**")

    # Compact form layout
    med_name = st.text_input("Name", value=med_data.get('name', ''), placeholder="e.g., Ibuprofen")

    col_dose, col_time = st.columns(2)
    with col_dose:
        med_dosage = st.text_input("Dosage", value=med_data.get('dosage', ''), placeholder="200mg")
    with col_time:
        default_time = time(8, 0)
        if is_editing and med_data.get('time_to_take'):
            try:
                default_time = datetime.strptime(med_data['time_to_take'], '%I:%M %p').time()
            except:
                pass
        med_time = st.time_input("Time", value=default_time, step=timedelta(minutes=15))

    med_purpose = st.text_input("Purpose", value=med_data.get('purpose', ''), placeholder="Pain relief")

    # Schedule type - more compact
    schedule_options = ["Daily", "Weekly", "One-Time"]
    current_schedule = med_data.get('schedule_type', 'Daily')
    schedule_index = schedule_options.index(current_schedule) if current_schedule in schedule_options else 0

    schedule_type = st.selectbox("Schedule", options=schedule_options, index=schedule_index)

    # Conditional fields
    days_of_week = None
    specific_date = None

    if schedule_type == 'Weekly':
        days_of_week = st.multiselect(
            "Days",
            options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=[d[:3] for d in med_data.get('days_of_week', [])]
        )
        # Convert back to full names
        day_map = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
                   "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
        days_of_week = [day_map[d] for d in days_of_week]

    elif schedule_type == 'One-Time':
        default_date = date.today()
        if is_editing and med_data.get('specific_date'):
            if isinstance(med_data['specific_date'], datetime):
                default_date = med_data['specific_date'].date()
        specific_date = st.date_input("Date", value=default_date)

    # Action buttons
    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Save", type="primary", use_container_width=True):
            if not all([med_name, med_dosage, med_purpose]):
                st.error("Please fill all fields")
                st.stop()

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
                    update_medication(st.session_state.editing_med_id, med_dict)
                    st.success(f"✅ Updated!")
                else:
                    new_med = Medication(**med_dict)
                    add_medication(new_med)
                    st.success(f"✅ Added!")

                close_med_dialog()  # Use helper function
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            close_med_dialog()  # Use helper function
            st.rerun()


# ========================================
# PERSON DIALOG (COMPACT POPUP)
# ========================================
@st.dialog("👤 Person Profile", width="small")  # Changed to "small"
def person_dialog():
    """Compact dialog popup for adding people"""

    st.markdown("**Add Person Profile**")

    person_name = st.text_input("Name", placeholder="Sarah")
    person_relationship = st.text_input("Relationship", placeholder="Daughter")
    person_notes = st.text_area("Notes (optional)", placeholder="Lives in Tel Aviv", height=80)
    uploaded_photo = st.file_uploader("Photo", type=["jpg", "png", "jpeg"])

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Add", type="primary", use_container_width=True):
            if not person_name or not person_relationship:
                st.error("Name and relationship required")
                st.stop()

            photo_url_to_save = "https://via.placeholder.com/150"
            face_encoding_list = None

            if uploaded_photo is not None:
                try:
                    image_dir = Path("images")
                    image_dir.mkdir(parents=True, exist_ok=True)

                    safe_filename = f"{person_name.lower().replace(' ', '_')}_{uploaded_photo.name}"
                    file_path = image_dir / safe_filename

                    with open(file_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())
                    photo_url_to_save = str(file_path)

                    with st.spinner("Analyzing face..."):
                        image = face_recognition.load_image_file(file_path)
                        encodings = face_recognition.face_encodings(image)

                        if encodings:
                            face_encoding_list = encodings[0].tolist()
                            st.success("✅ Face detected!")
                        else:
                            st.warning("⚠️ No face found")

                except Exception as e:
                    st.error(f"Photo error: {e}")

            try:
                new_person = PersonProfile(
                    name=person_name,
                    relationship=person_relationship,
                    photo_url=photo_url_to_save,
                    notes=person_notes
                )

                person_id = add_person(new_person)

                if person_id and face_encoding_list:
                    update_person(person_id, {"face_encoding": face_encoding_list})

                st.success(f"✅ Added {person_name}!")
                close_person_dialog()  # Use helper function
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            close_person_dialog()  # Use helper function
            st.rerun()


# ========================================
# SHOW DIALOGS IF TRIGGERED
# ========================================
if st.session_state.show_med_dialog:
    medication_dialog()

if st.session_state.show_person_dialog:
    person_dialog()