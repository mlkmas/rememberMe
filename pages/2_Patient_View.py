import streamlit as st
from datetime import datetime, time
# --- FIX: Correct import ---
from src.database import get_all_medications
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
from src.smart_reminder import generate_smart_reminder
import os # Import os for file cleanup

st.set_page_config(page_title="Patient View", page_icon="😊", layout="centered")

st.title("😊 Hello! Here is your day.")
st.caption(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
st.divider()

# --- Feature #4: Daily Recap ---
st.header("What Happened Today?")

if 'recap_audio_path' not in st.session_state:
    st.session_state.recap_audio_path = None

if st.button("Tell Me About My Day", use_container_width=True, type="primary"):
    with st.spinner("Thinking about your day..."):
        recap_script = generate_daily_recap()
        st.session_state.recap_audio_path = text_to_speech(recap_script)
        st.rerun() # Rerun to make the audio player appear

if st.session_state.recap_audio_path:
    st.audio(str(st.session_state.recap_audio_path), autoplay=True)
    # Clean up after playing (or trying to play)
    try:
        os.remove(st.session_state.recap_audio_path)
    except Exception as e:
        st.warning(f"Could not remove temp recap audio: {e}")
    st.session_state.recap_audio_path = None # Reset state
else:
    st.info("Click the button above and I'll tell you about your day!")

st.divider()

# --- Feature #6: Medication Schedule & Smart Reminders ---
st.header("Today's Medication Schedule")

# --- FIX: Fetch all meds and filter here ---
all_medications = get_all_medications()
todays_meds = []
today_date = datetime.now().date()
today_name = today_date.strftime('%A')

for med in all_medications:
    stype = med.get('schedule_type')
    if stype == 'Daily':
        todays_meds.append(med)
    elif stype == 'Weekly':
        if today_name in med.get('days_of_week', []):
            todays_meds.append(med)
    elif stype == 'One-Time':
        sdate_raw = med.get('specific_date')
        sdate = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw
        if sdate == today_date:
            todays_meds.append(med)

# Sort today's meds by time
todays_meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())
# --- End of Filtering Logic ---

if not todays_meds:
    st.success("You have no medications scheduled for today. ✅")
else:
    st.info("Here are your medications for today. You can press the 🔊 button to hear a reminder.")

    # --- State to manage which reminder is playing ---
    if 'reminder_audio_path' not in st.session_state:
        st.session_state.reminder_audio_path = None
    if 'active_med_id' not in st.session_state:
        st.session_state.active_med_id = None

    for med in todays_meds:
        med_id = med.get('_id')
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"{med.get('time_to_take', '')} - {med.get('name', '')}")
                st.write(f"**Dosage:** {med.get('dosage', '')}")
                st.caption(f"**Purpose:** {med.get('purpose', '')}")
            with col2:
                # --- The "Hear Reminder" button ---
                if st.button("🔊", key=f"speak_{med_id}", help="Hear a smart reminder for this medication", use_container_width=True):
                    with st.spinner("Preparing your reminder..."):
                        # Generate the audio and store its path
                        audio_path = generate_smart_reminder(med)
                        if audio_path:
                            st.session_state.reminder_audio_path = str(audio_path)
                            st.session_state.active_med_id = med_id
                        else:
                            st.error("Sorry, I couldn't generate the reminder audio.")
                        st.rerun() # Rerun to update the UI and play audio

    # --- Audio Player Logic ---
    if st.session_state.reminder_audio_path and st.session_state.active_med_id:
        st.subheader("Playing Your Reminder")
        st.audio(st.session_state.reminder_audio_path, autoplay=True)

        # Clean up the temporary audio file after playing
        try:
            os.remove(st.session_state.reminder_audio_path)
        except Exception as e:
            st.warning(f"Could not remove temp reminder audio: {e}")

        # Reset state so it doesn't play again automatically
        st.session_state.reminder_audio_path = None
        st.session_state.active_med_id = None