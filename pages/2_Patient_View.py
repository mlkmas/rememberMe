import streamlit as st
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
import os

st.set_page_config(page_title="Patient View", page_icon="😊")

st.title("😊 Your Daily Reminder")
st.caption("Press the button below to hear about your day.")

st.divider()

# A big, friendly button for the patient
if st.button("What happened today?", type="primary", use_container_width=True):
    
    # 1. Generate the recap story
    with st.spinner("Let me think about your day..."):
        try:
            recap_script = generate_daily_recap()
        except Exception as e:
            st.error(f"Could not generate recap: {e}")
            st.stop()
            
    # 2. Convert the story to audio
    with st.spinner("Getting the audio ready for you..."):
        try:
            audio_file_path = text_to_speech(recap_script)
        except Exception as e:
            st.error(f"Could not create audio: {e}")
            st.stop()
            
    # 3. Play the audio
    st.success("Here's your daily recap!")
    st.audio(str(audio_file_path), format="audio/mp3")
    
    # Optionally display the text for caregivers to see
    with st.expander("Show recap text"):
        st.write(recap_script)
        
    # Clean up the temporary audio file
    try:
        os.remove(audio_file_path)
    except Exception as e:
        st.warning(f"Could not remove temp audio file: {e}")

else:
    st.info("Click the big button above and I'll tell you about your day!")
