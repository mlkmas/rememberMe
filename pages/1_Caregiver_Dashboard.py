# pages/1_Caregiver_Dashboard.py
import streamlit as st
from datetime import datetime
from src.database import get_all_conversations
import pandas as pd # <-- ADD THIS IMPORT for data analysis

# --- Page Config ---
st.set_page_config(page_title="Caregiver Dashboard", page_icon="🩺", layout="wide")

# --- Header ---
st.title("🩺 Caregiver Dashboard")
st.caption("A timeline of recent conversations and clinical insights")

# --- Refresh Button ---
if st.button("Refresh Data", use_container_width=True):
    # Clear Streamlit's cache for database functions to force refetch
    st.cache_data.clear()
    st.rerun()

# --- Fetch Data ---
# This function is cached in database.py, but Refresh button clears it
all_summaries = get_all_conversations()

# --- Main Content ---
if not all_summaries:
    st.info("No conversations have been recorded yet. Use the 'Admin Tools' page to add data.")
else:
    # --- NEW: Dashboard Analytics ---
    st.subheader("📊 Cognitive & Mood Analytics")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Total Memories Recorded", value=len(all_summaries))

        # --- Mood Distribution Chart ---
        moods = [s.get('patient_mood', 'unknown').lower() for s in all_summaries if s.get('patient_mood')] # Get moods, handle missing, convert to lower
        if moods:
            # Use pandas Series to easily count occurrences
            mood_counts = pd.Series(moods).value_counts()
            st.write("**Mood Distribution:**")
            st.bar_chart(mood_counts)
            #
        else:
            st.write("No mood data recorded yet.")

    with col2:
        # --- Top Key Concerns Table ---
        all_concerns = []
        for s in all_summaries:
            # s.get('key_concerns', []) returns a list, extend adds all elements
            all_concerns.extend([concern.strip() for concern in s.get('key_concerns', []) if concern.strip()]) # Add concerns, strip whitespace

        if all_concerns:
            # Use pandas Series to count occurrences
            concern_counts = pd.Series(all_concerns).value_counts()
            st.write("**⚠️ Top Recurring Concerns:**")
            # Display as a table (dataframe)
            st.dataframe(concern_counts, use_container_width=True)
            #
        else:
            st.write("No key concerns noted yet.")

    st.divider()
    # --- END NEW ---

    # --- Conversation Timeline (Existing Logic) ---
    st.subheader(f"Timeline: {len(all_summaries)} Recent Memories")

    for item in all_summaries:
        # Use .get() for safety, provide default value, ensure ID is string
        item_id = str(item.get('_id', 'N/A')) # Use item_id for keys if needed
        generated_at = item.get('generated_at', datetime.now()) # Default if missing

        with st.container(border=True):
            st.caption(f"Recorded on: {generated_at.strftime('%Y-%m-%d at %I:%M %p')}")

            # Display the simple summary
            st.write(item.get('simple_summary', 'No summary available.'))

            # Expander for clinical insights
            with st.expander("Show Clinical Insights"):
                st.markdown(f"**Mood:** `{item.get('patient_mood', 'unknown')}`")
                st.markdown(f"**Cognitive State:** {item.get('cognitive_state', 'unknown')}")

                topics = item.get('topics_discussed', [])
                if topics:
                    st.markdown("**Topics Discussed:**")
                    # Display topics as a list or comma-separated string
                    st.markdown(", ".join(topic for topic in topics if topic)) # Filter empty topics

                concerns = item.get('key_concerns', [])
                if concerns:
                    st.markdown("**⚠️ Key Concerns Noted:**")
                    for concern in concerns:
                         if concern: # Avoid printing empty concerns
                            st.markdown(f"- {concern.strip()}") # Use markdown list

        st.divider() # Separator between timeline entries