# app.py
import streamlit as st

st.set_page_config(
    page_title="RememberMe AI - Home",
    page_icon="🧠",
    layout="wide"
)

st.title("Welcome to RememberMe AI 🧠")
st.sidebar.success("Select a page above.")

st.markdown(
    """
    **RememberMe AI** is a conversation memory assistant designed to help 
    dementia patients and their caregivers.

    This application provides multiple views:
    
    ### 1. 🩺 Caregiver Dashboard
    - A comprehensive view for caregivers to monitor conversation timelines,
      track cognitive patterns, and manage patient information.
      
    ### 2. 😊 Patient View
    - A simple, voice-activated interface for the patient to get daily recaps
      and reminders about their day.

    ### 3. 🛠️ Admin Tools
    - A page for caregivers to add/manage medications and people.
    
    ### 4. 🤔 Who Is This? (NEW)
    - A live tool to help the patient recognize who they are talking to.

    **👈 Select a page from the sidebar to get started!**
    """
)