# pages/2_Patient_View.py
import streamlit as st
from datetime import datetime, time
from src.database import get_all_medications, get_all_people, get_settings
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
from src.smart_reminder import generate_smart_reminder
from src.patient_assistant import answer_patient_question
from src.transcriber import transcribe_audio
import os
import re
from pathlib import Path
import tempfile

st.set_page_config(page_title="Patient View", page_icon="😊", layout="centered")

# Custom CSS for large, simple buttons
st.markdown("""
<style>
    .big-font {
        font-size: 32px !important;
        font-weight: bold;
    }
    div[data-testid="stButton"] button {
        font-size: 24px;
        padding: 20px;
        height: auto;
    }
</style>
""", unsafe_allow_html=True)

st.title("😊 Hello! Here is your day.")
st.caption(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
st.divider()

# Load people profiles
try:
    people_profiles = {person['name'].lower(): person for person in get_all_people()}
except Exception as e:
    st.error(f"Failed to load people profiles: {e}")
    people_profiles = {}

# Check for scheduled audio files
scheduled_audio_dir = Path("scheduled_audio")
pending_audio = None

if scheduled_audio_dir.exists():
    # Get most recent audio file
    audio_files = sorted(scheduled_audio_dir.glob("*.mp3"), key=lambda x: x.stat().st_mtime, reverse=True)
    if audio_files:
        pending_audio = audio_files[0]

# Auto-play scheduled audio
if pending_audio and 'last_played_audio' not in st.session_state:
    st.session_state.last_played_audio = str(pending_audio)
    st.info("🔔 You have a message!")
    st.audio(str(pending_audio), autoplay=True)

    # Delete after playing
    try:
        pending_audio.unlink()
    except:
        pass

# ========================================
# VOICE ASSISTANT MODE
# ========================================
st.header("🤖 Ask Me Anything")
st.caption("Press the microphone button and ask a question")

# Initialize session state
if 'assistant_response' not in st.session_state:
    st.session_state.assistant_response = None
if 'assistant_audio' not in st.session_state:
    st.session_state.assistant_audio = None

# Voice input for assistant
assistant_audio = st.audio_input("🎤 Ask your question")

if assistant_audio is not None:
    with st.spinner("🤔 Thinking..."):
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(assistant_audio.getvalue())
            tmp_audio_path = tmp_file.name

        try:
            # Transcribe question
            question = transcribe_audio(tmp_audio_path)

            if question and not question.startswith("Error"):
                st.info(f"You asked: {question}")

                # Get answer from assistant
                answer, is_emergency = answer_patient_question(question)

                if is_emergency:
                    st.error("🚨 Emergency detected! Calling your caregiver now!")

                # Convert answer to speech
                answer_audio_path = text_to_speech(answer, "temp_assistant_answer.mp3")

                st.session_state.assistant_response = answer
                st.session_state.assistant_audio = str(answer_audio_path)
                st.rerun()
            else:
                st.error("Sorry, I couldn't understand that. Please try again.")

        except Exception as e:
            st.error(f"Sorry, I had trouble with that: {e}")

        finally:
            # Clean up temp file
            try:
                os.remove(tmp_audio_path)
            except:
                pass

# Display assistant response
if st.session_state.assistant_response:
    st.success("💬 Here's my answer:")
    st.markdown(f"**{st.session_state.assistant_response}**")

    if st.session_state.assistant_audio:
        st.audio(st.session_state.assistant_audio, autoplay=True)

        # Clean up after playing
        try:
            os.remove(st.session_state.assistant_audio)
        except:
            pass

        st.session_state.assistant_audio = None

st.divider()

# ========================================
# DAILY RECAP
# ========================================
st.header("What Happened Today?")

if 'recap_audio_path' not in st.session_state:
    st.session_state.recap_audio_path = None
if 'recap_script' not in st.session_state:
    st.session_state.recap_script = None

if st.button("Tell Me About My Day", use_container_width=True, type="primary"):
    with st.spinner("Thinking about your day..."):
        st.session_state.recap_script = generate_daily_recap()
        audio_path = text_to_speech(st.session_state.recap_script)
        st.session_state.recap_audio_path = str(audio_path)
        st.rerun()

# Display recap with photos
if st.session_state.recap_script:
    st.subheader("Your Recap:")

    sentences = re.split(r'(?<=[.!?])\s+', st.session_state.recap_script)

    for sentence in sentences:
        if not sentence:
            continue

        found_person = None
        for name, profile in people_profiles.items():
            if name in sentence.lower():
                found_person = profile
                break

        if found_person:
            col_img, col_text = st.columns([1, 4])
            with col_img:
                photo_path = found_person['photo_url']
                if Path(photo_path).exists():
                    st.image(photo_path, width=80, caption=f"{found_person['name']}")
                else:
                    st.image("https://via.placeholder.com/150", width=80, caption=f"{found_person['name']}")
            with col_text:
                st.write(sentence)
        else:
            st.write(sentence)

    if st.session_state.recap_audio_path:
        st.audio(str(st.session_state.recap_audio_path), autoplay=True)
        try:
            os.remove(st.session_state.recap_audio_path)
        except:
            pass
        st.session_state.recap_audio_path = None
else:
    st.info("Click the button above and I'll tell you about your day!")

st.divider()

# ========================================
# MEDICATION SCHEDULE
# ========================================
st.header("Today's Medication Schedule")

all_medications = get_all_medications()
todays_meds = []
today_date = datetime.now().date()
today_name = today_date.strftime('%A')

for med in all_medications:
    stype = med.get('schedule_type')
    is_today = False

    if stype == 'Daily':
        is_today = True
    elif stype == 'Weekly':
        if today_name in med.get('days_of_week', []):
            is_today = True
    elif stype == 'One-Time':
        sdate_raw = med.get('specific_date')
        sdate = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw
        if sdate == today_date:
            is_today = True

    if is_today:
        todays_meds.append(med)

todays_meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())

if not todays_meds:
    st.success("No medications scheduled today. ✅")
else:
    st.info("Press 🔊 to hear a reminder.")

    if 'reminder_audio_path' not in st.session_state:
        st.session_state.reminder_audio_path = None
    if 'active_med_id_for_audio' not in st.session_state:
        st.session_state.active_med_id_for_audio = None

    for med in todays_meds:
        med_id = med.get('_id') or med.get('id')

        with st.container(border=True):
            col1m, col2m = st.columns([4, 1])

            with col1m:
                st.subheader(f"{med.get('time_to_take', '')} - {med.get('name', '')}")
                st.write(f"**Dosage:** {med.get('dosage', '')}")
                st.caption(f"**Purpose:** {med.get('purpose', '')}")

            with col2m:
                if st.button("🔊", key=f"speak_{med_id}", help="Hear reminder", use_container_width=True):
                    with st.spinner("Preparing reminder..."):
                        audio_path = generate_smart_reminder(med)
                        if audio_path:
                            st.session_state.reminder_audio_path = str(audio_path)
                            st.session_state.active_med_id_for_audio = med_id
                        else:
                            st.error("Couldn't generate reminder audio.")
                        st.rerun()

    if st.session_state.reminder_audio_path and st.session_state.active_med_id_for_audio:
        st.subheader("Playing Reminder")
        st.audio(st.session_state.reminder_audio_path, autoplay=True)

        try:
            os.remove(st.session_state.reminder_audio_path)
        except:
            pass

        st.session_state.reminder_audio_path = None
        st.session_state.active_med_id_for_audio = None

st.divider()

# ========================================
# SIMPLE LIVEKIT INTERFACE (if enabled)
# ========================================
settings = get_settings()

if settings.get('livekit_session_active', False):
    st.header("📞 Voice Call Active")
    st.success("Your caregiver is listening. You can talk normally.")
    st.caption("The conversation will be saved automatically.")
else:
    st.caption("Voice call not active. Ask your caregiver to start it if needed.")