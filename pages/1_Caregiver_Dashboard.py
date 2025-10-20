import streamlit as st
from datetime import datetime
from src.database import get_all_conversations

# --- Page Config ---
# Streamlit automatically uses the filename as the page title
st.set_page_config(page_title="Caregiver Dashboard", page_icon="🩺", layout="wide")

# --- Header ---
st.title("🩺 Caregiver Dashboard")
st.caption("A timeline of recent conversations and clinical insights (Feature #5)")

# --- Main Content ---
# Add a refresh button
if st.button("Refresh Timeline", use_container_width=True):
    # This just forces a rerun to fetch the latest data from the DB
    st.rerun()

all_summaries = get_all_conversations()
    
if not all_summaries:
    st.info("No conversations have been recorded yet. Use the 'Admin Tools' page to add data.")
else:
    st.write(f"Showing {len(all_summaries)} most recent memories:")
    
    for item in all_summaries:
        with st.container(border=True):
            # Use .get() for safety, providing a default value
            date = item.get('generated_at', datetime.now())
            st.caption(f"Recorded on: {date.strftime('%Y-%m-%d at %I:%M %p')}")
            
            # This is the "Level 1: Patient Summary"
            st.write(item.get('simple_summary', 'No summary available.'))

        # This is the "Level 2: Clinical Insights" in an expander
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
        
        st.divider() # Add a line between entries
