# pages/2_Patient_View.py
import streamlit as st
from datetime import datetime, time
# Added get_all_people
from src.database import get_all_medications, get_all_people
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
from src.smart_reminder import generate_smart_reminder
import os
import re # Import regular expressions for name finding

st.set_page_config(page_title="Patient View", page_icon="😊", layout="centered")

st.title("😊 Hello! Here is your day.")
st.caption(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
st.divider()

# --- Load People Profiles ---
# We load this once at the top to use later
people_profiles = {person['name'].lower(): person for person in get_all_people()}

# --- Feature #4: Daily Recap ---
st.header("What Happened Today?")

if 'recap_audio_path' not in st.session_state: st.session_state.recap_audio_path = None
if 'recap_script' not in st.session_state: st.session_state.recap_script = None

if st.button("Tell Me About My Day", use_container_width=True, type="primary"):
    with st.spinner("Thinking about your day..."):
        st.session_state.recap_script = generate_daily_recap()
        st.session_state.recap_audio_path = text_to_speech(st.session_state.recap_script)
        st.rerun()

# --- NEW: Display Recap with Photos ---
if st.session_state.recap_script:
    st.subheader("Your Recap:")
    
    # Split the script into sentences or paragraphs for better display
    sentences = re.split(r'(?<=[.!?])\s+', st.session_state.recap_script)
    
    for sentence in sentences:
        if not sentence: continue
        
        # Check if any known person's name is in the sentence
        found_person = None
        for name, profile in people_profiles.items():
             # Simple case-insensitive check
            if name in sentence.lower():
                found_person = profile
                break # Show first person found in sentence

        if found_person:
            # Display with photo
            col_img, col_text = st.columns([1, 4])
            with col_img:
                st.image(found_person['photo_url'], width=80, caption=f"{found_person['name']} ({found_person['relationship']})")
            with col_text:
                st.write(sentence)
        else:
            # Display text only
            st.write(sentence)

    # Play the audio
    if st.session_state.recap_audio_path:
        st.audio(str(st.session_state.recap_audio_path), autoplay=True)
        try: os.remove(st.session_state.recap_audio_path)
        except Exception as e: st.warning(f"Could not remove temp recap audio: {e}")
        st.session_state.recap_audio_path = None
else:
    st.info("Click the button above and I'll tell you about your day!")
    
st.divider()

# --- Feature #6: Medication Schedule & Smart Reminders (Unchanged) ---
st.header("Today's Medication Schedule")
# ... (Medication display logic remains the same) ...
all_medications = get_all_medications()
todays_meds = []
today_date = datetime.now().date(); today_name = today_date.strftime('%A')
for med in all_medications:
    stype = med.get('schedule_type'); is_today = False
    if stype == 'Daily': is_today = True
    elif stype == 'Weekly':
        if today_name in med.get('days_of_week', []): is_today = True
    elif stype == 'One-Time':
        sdate_raw = med.get('specific_date'); sdate = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw
        if sdate == today_date: is_today = True
    if is_today: todays_meds.append(med)
todays_meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())

if not todays_meds: st.success("No medications scheduled today. ✅")
else:
    st.info("Press 🔊 to hear a reminder.")
    if 'reminder_audio_path' not in st.session_state: st.session_state.reminder_audio_path = None
    if 'active_med_id_for_audio' not in st.session_state: st.session_state.active_med_id_for_audio = None
    for med in todays_meds:
        med_id = med.get('_id')
        with st.container(border=True):
            col1m, col2m = st.columns([4, 1])
            with col1m:
                st.subheader(f"{med.get('time_to_take', '')} - {med.get('name', '')}"); st.write(f"**Dosage:** {med.get('dosage', '')}"); st.caption(f"**Purpose:** {med.get('purpose', '')}")
            with col2m:
                if st.button("🔊", key=f"speak_{med_id}", help="Hear reminder", use_container_width=True):
                    with st.spinner("Preparing reminder..."):
                        audio_path = generate_smart_reminder(med)
                        if audio_path: st.session_state.reminder_audio_path = str(audio_path); st.session_state.active_med_id_for_audio = med_id
                        else: st.error("Couldn't generate reminder audio.")
                        st.rerun()
    if st.session_state.reminder_audio_path and st.session_state.active_med_id_for_audio:
        st.subheader("Playing Reminder"); st.audio(st.session_state.reminder_audio_path, autoplay=True)
        try: os.remove(st.session_state.reminder_audio_path)
        except Exception as e: st.warning(f"Could not remove temp reminder audio: {e}")
        st.session_state.reminder_audio_path = None; st.session_state.active_med_id_for_audio = None