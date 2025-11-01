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
    - Comprehensive view for caregivers to monitor conversation timelines
    - Track cognitive patterns and manage patient information
    - AI Chatbot to ask questions about patient's day/week

    ### 2. 😊 Patient View
    - Simple voice-activated interface for daily recaps and reminders
    - AI Assistant for answering questions and emergency detection
    - Automatic medication reminders at scheduled times

    ### 3. 🛠️ Admin Tools
    - Manage medications and people profiles
    - Control LiveKit recording sessions
    - Configure automatic daily recap schedule

    ### 4. 🤔 Who Is This?
    - Live facial recognition to help identify people

    **👈 Select a page from the sidebar to get started!**
    """
)