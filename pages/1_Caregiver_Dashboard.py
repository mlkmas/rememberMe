# pages/1_Caregiver_Dashboard.py
import streamlit as st
from datetime import datetime
from src.database import get_all_conversations
import pandas as pd # <-- ADDED IMPORT

# --- Page Config ---
st.set_page_config(page_title="Caregiver Dashboard", page_icon="🩺", layout="wide")

# --- Header ---
st.title("🩺 Caregiver Dashboard")
st.caption("A timeline of recent conversations and clinical insights")

# --- Main Content ---
if st.button("Refresh Timeline", use_container_width=True):
    st.rerun()

all_summaries = get_all_conversations()
    
if not all_summaries:
    st.info("No conversations have been recorded yet. Use the 'Admin Tools' page to add data.")
else:
    # --- NEW: Dashboard Analytics (Step 2) ---
    st.subheader("Cognitive & Mood Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="Total Memories Recorded", value=len(all_summaries))
        
        # Create a list of all moods
        moods = [s.get('patient_mood', 'unknown') for s in all_summaries]
        if moods:
            # Use pandas to count mood occurrences
            mood_counts = pd.Series(moods).value_counts()
            st.write("**Mood Distribution:**")
            st.bar_chart(mood_counts)
        
    with col2:
        # Collect all key concerns
        all_concerns = []
        for s in all_summaries:
            all_concerns.extend(s.get('key_concerns', []))
            
        if all_concerns:
            # Use pandas to count concern occurrences
            concern_counts = pd.Series(all_concerns).value_counts()
            st.write("**⚠️ Top Recurring Concerns:**")
            st.dataframe(concern_counts, use_container_width=True)
        else:
            st.info("No key concerns noted.")
            
    st.divider()
    # --- END NEW ---
    
    st.subheader(f"Showing {len(all_summaries)} most recent memories:")
    
    for item in all_summaries:
        with st.container(border=True):
            date = item.get('generated_at', datetime.now())
            st.caption(f"Recorded on: {date.strftime('%Y-%m-%d at %I:%M %p')}")
            
            st.write(item.get('simple_summary', 'No summary available.'))

        with st.expander("Show Clinical Insights"):
            st.markdown(f"**Mood:** `{item.get('patient_mood', 'unknown')}`")
            st.markdown(f"**Cognitive State:** {item.get('cognitive_state', 'unknown')}")
            
            topics = item.get('topics_discussed', [])
            if topics:
                st.markdown("**Topics:**")
                st.markdown(", ".join(topics))
                    
            concerns = item.get('key_concerns', [])
            if concerns:
                st.markdown("**⚠️ Key Concerns:**")
                for concern in concerns:
                    st.markdown(f"- {concern}")
        
        st.divider()