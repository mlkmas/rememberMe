import streamlit as st
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
from src.database import get_all_medications
import os
from datetime import datetime

st.set_page_config(page_title="Patient View", page_icon="😊", layout="wide")
st.title("😊 Your Daily Reminder")

col1, col2 = st.columns(2)

# --- COLUMN 1: DAILY RECAP (Unchanged) ---
with col1:
    st.header("Hear About Your Day")
    st.caption("Press the button below to get a spoken summary of your day.")
    if st.button("What happened today?", type="primary", use_container_width=True):
        with st.spinner("Let me think about your day..."):
            recap_script = generate_daily_recap()
        with st.spinner("Getting the audio ready..."):
            audio_file_path = text_to_speech(recap_script)
        st.success("Here's your daily recap!")
        st.audio(str(audio_file_path))
        with st.expander("Show recap text"):
            st.write(recap_script)
        try: os.remove(audio_file_path)
        except: pass
    else:
        st.info("Click the big button above and I'll tell you about your day!")

# --- COLUMN 2: TODAY'S MEDICATION SCHEDULE ---
with col2:
    st.header("Today's Medication")
    st.caption("Here is your medication schedule for today.")
    
    # --- UPGRADED LOGIC TO FILTER FOR TODAY ---
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
            # MongoDB stores dates as datetime objects, so we must convert to date
            sdate = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw
            if sdate == today_date:
                todays_meds.append(med)
    
    # Sort today's meds by time
    todays_meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())

    if not todays_meds:
        st.info("You have no medications scheduled for today.")
    else:
        for med in todays_meds:
            with st.container(border=True):
                st.subheader(f"{med.get('time_to_take', '')} - {med.get('name', 'N/A')}")
                st.write(f"**Dosage:** {med.get('dosage', 'N/A')}")
                st.write(f"**Reason:** {med.get('purpose', 'N/A')}")

