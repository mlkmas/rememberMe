# pages/1_Caregiver_Dashboard.py
import streamlit as st
from datetime import datetime, timedelta
from src.database import get_all_conversations
import pandas as pd
import calendar

# --- Page Config ---
st.set_page_config(page_title="Caregiver Dashboard", page_icon="🩺", layout="wide")

# Custom CSS for beautiful design
st.markdown("""
<style>
    /* Calendar styling */
    .calendar-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .calendar-header {
        font-size: 24px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 20px;
    }

    .day-cell {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        min-height: 100px;
        position: relative;
    }

    .day-cell:hover {
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }

    .day-number {
        font-size: 18px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
    }

    .day-today {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-color: #667eea;
    }

    .day-today .day-number {
        color: white !important;
    }

    .day-has-data {
        background: #f0f9ff;
        border-color: #3b82f6;
    }

    .conversation-badge {
        display: inline-block;
        background: #3b82f6;
        color: white;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 12px;
        font-weight: 600;
        margin-top: 5px;
    }

    .mood-indicator {
        font-size: 20px;
        margin-top: 5px;
    }

    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }

    .stats-number {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .stats-label {
        font-size: 14px;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🩺 Caregiver Dashboard")
st.caption("Monitor conversations, patterns, and cognitive health")
st.divider()

# --- Initialize Session State ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None
if 'show_date_dialog' not in st.session_state:
    st.session_state.show_date_dialog = False
if 'current_month' not in st.session_state:
    st.session_state.current_month = datetime.now().month
if 'current_year' not in st.session_state:
    st.session_state.current_year = datetime.now().year
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "month"  # month, week, or list

# --- Refresh Button ---
if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# --- Fetch Data ---
all_summaries = get_all_conversations()

# Organize data by date
conversations_by_date = {}
for summary in all_summaries:
    date = summary.get('generated_at', datetime.now()).date()
    if date not in conversations_by_date:
        conversations_by_date[date] = []
    conversations_by_date[date].append(summary)

# --- View Mode Selector ---
col_view1, col_view2, col_view3 = st.columns(3)
with col_view1:
    if st.button("📅 Month View", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "month" else "secondary"):
        st.session_state.view_mode = "month"
        st.rerun()
with col_view2:
    if st.button("📊 Week View", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "week" else "secondary"):
        st.session_state.view_mode = "week"
        st.rerun()
with col_view3:
    if st.button("📋 List View", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "list" else "secondary"):
        st.session_state.view_mode = "list"
        st.rerun()

st.divider()

# ========================================
# MONTH VIEW
# ========================================
if st.session_state.view_mode == "month":
    # Month/Year Navigation
    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])

    with nav_col1:
        if st.button("◀ Previous", use_container_width=True):
            if st.session_state.current_month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
            st.rerun()

    with nav_col2:
        month_name = calendar.month_name[st.session_state.current_month]
        st.markdown(f"<h2 style='text-align: center;'>{month_name} {st.session_state.current_year}</h2>",
                    unsafe_allow_html=True)

    with nav_col3:
        if st.button("Next ▶", use_container_width=True):
            if st.session_state.current_month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
            st.rerun()

    # Generate calendar
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)

    # Day headers
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for idx, day_name in enumerate(day_names):
        with header_cols[idx]:
            st.markdown(
                f"<div style='text-align: center; font-weight: 600; color: #6b7280; margin-bottom: 10px;'>{day_name}</div>",
                unsafe_allow_html=True)

    # Calendar grid
    today = datetime.now().date()

    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            with week_cols[idx]:
                if day == 0:
                    # Empty cell
                    st.markdown("<div style='min-height: 100px;'></div>", unsafe_allow_html=True)
                else:
                    # Create date object
                    date_obj = datetime(st.session_state.current_year, st.session_state.current_month, day).date()

                    # Check if this date has conversations
                    day_conversations = conversations_by_date.get(date_obj, [])

                    # Determine styling
                    is_today = date_obj == today
                    has_data = len(day_conversations) > 0

                    # Calculate mood for the day
                    if day_conversations:
                        moods = [c.get('patient_mood', '').lower() for c in day_conversations]
                        positive_count = sum(1 for m in moods if m == 'positive')
                        if positive_count > len(moods) / 2:
                            mood_emoji = "😊"
                        elif 'anxious' in moods or 'confused' in moods:
                            mood_emoji = "😟"
                        else:
                            mood_emoji = "😐"
                    else:
                        mood_emoji = ""

                    # Create cell
                    cell_class = "day-cell"
                    if is_today:
                        cell_class += " day-today"
                    elif has_data:
                        cell_class += " day-has-data"

                    # Button to open dialog
                    if st.button(
                            f"{day}",
                            key=f"day_{date_obj}",
                            use_container_width=True,
                            disabled=not has_data and not is_today
                    ):
                        st.session_state.selected_date = date_obj
                        st.session_state.show_date_dialog = True
                        st.rerun()

                    # Show badges
                    if has_data:
                        st.markdown(
                            f"<div style='text-align: center;'><span class='conversation-badge'>{len(day_conversations)} 💬</span></div>",
                            unsafe_allow_html=True)
                        st.markdown(f"<div class='mood-indicator' style='text-align: center;'>{mood_emoji}</div>",
                                    unsafe_allow_html=True)
                    elif is_today:
                        st.markdown(
                            "<div style='text-align: center; color: white; font-size: 12px; margin-top: 5px;'>Today</div>",
                            unsafe_allow_html=True)

# ========================================
# WEEK VIEW
# ========================================
elif st.session_state.view_mode == "week":
    st.markdown("### 📊 This Week's Activity")

    # Get current week dates
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]

    # Display week
    for date in week_dates:
        day_conversations = conversations_by_date.get(date, [])
        is_today = date == today

        with st.container():
            col_date, col_count, col_view = st.columns([2, 1, 1])

            with col_date:
                date_str = date.strftime("%A, %B %d")
                if is_today:
                    st.markdown(f"**🔵 {date_str} (Today)**")
                else:
                    st.markdown(f"**{date_str}**")

            with col_count:
                if day_conversations:
                    st.metric("Conversations", len(day_conversations))
                else:
                    st.caption("No activity")

            with col_view:
                if day_conversations:
                    if st.button("View Details", key=f"week_{date}", use_container_width=True):
                        st.session_state.selected_date = date
                        st.session_state.show_date_dialog = True
                        st.rerun()

            st.divider()

# ========================================
# LIST VIEW (Original)
# ========================================
elif st.session_state.view_mode == "list":
    st.markdown("### 📋 All Conversations (Latest First)")

    if not all_summaries:
        st.info("No conversations recorded yet.")
    else:
        for idx, item in enumerate(all_summaries):
            generated_at = item.get('generated_at', datetime.now())

            with st.expander(
                    f"📅 {generated_at.strftime('%b %d, %Y at %I:%M %p')} - {item.get('participant', 'Unknown')}"):
                st.markdown(f"**Summary:** {item.get('simple_summary', 'No summary')}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Mood:** {item.get('patient_mood', 'unknown')}")
                with col2:
                    st.markdown(f"**Cognitive State:** {item.get('cognitive_state', 'unknown')}")

                topics = item.get('topics_discussed', [])
                if topics:
                    st.markdown("**Topics:** " + ", ".join(topics))

                concerns = item.get('key_concerns', [])
                if concerns:
                    st.warning("**⚠️ Concerns:** " + ", ".join(concerns))

# ========================================
# ANALYTICS SIDEBAR
# ========================================
with st.sidebar:
    st.markdown("### 📊 Quick Stats")

    # Total conversations
    st.markdown(f"""
    <div class='stats-card'>
        <div class='stats-number'>{len(all_summaries)}</div>
        <div class='stats-label'>Total Conversations</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # This week
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    this_week = [s for s in all_summaries if s.get('generated_at', datetime.now()).date() >= start_of_week]

    st.metric("This Week", len(this_week))

    # Mood distribution
    if all_summaries:
        moods = [s.get('patient_mood', 'unknown').lower() for s in all_summaries]
        mood_counts = pd.Series(moods).value_counts()

        st.markdown("### 😊 Overall Mood")
        for mood, count in mood_counts.items():
            percentage = (count / len(moods)) * 100
            st.progress(percentage / 100, text=f"{mood.capitalize()}: {percentage:.0f}%")

    st.divider()

    # Top concerns
    all_concerns = []
    for s in all_summaries:
        all_concerns.extend([c.strip() for c in s.get('key_concerns', []) if c.strip()])

    if all_concerns:
        concern_counts = pd.Series(all_concerns).value_counts()
        st.markdown("### ⚠️ Top Concerns")
        for concern, count in concern_counts.head(3).items():
            st.markdown(f"• {concern} ({count}x)")


# ========================================
# DATE DIALOG (Popup with day's details)
# ========================================
@st.dialog("📅 Conversations Summary", width="large")
def date_dialog():
    """Show all conversations for selected date"""

    selected_date = st.session_state.selected_date
    day_conversations = conversations_by_date.get(selected_date, [])

    # Header
    st.markdown(f"### {selected_date.strftime('%A, %B %d, %Y')}")

    if not day_conversations:
        st.info("No conversations recorded on this day.")
        if st.button("Close", use_container_width=True):
            st.session_state.show_date_dialog = False
            st.rerun()
        return

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Conversations", len(day_conversations))
    with col2:
        moods = [c.get('patient_mood', '').lower() for c in day_conversations]
        positive_pct = (sum(1 for m in moods if m == 'positive') / len(moods)) * 100 if moods else 0
        st.metric("Positive Mood", f"{positive_pct:.0f}%")
    with col3:
        all_concerns_day = []
        for c in day_conversations:
            all_concerns_day.extend(c.get('key_concerns', []))
        st.metric("Concerns", len(all_concerns_day))

    st.divider()

    # List all conversations
    for idx, conv in enumerate(day_conversations):
        time_str = conv.get('generated_at', datetime.now()).strftime('%I:%M %p')

        with st.expander(f"🕐 {time_str} - {conv.get('participant', 'Unknown')}", expanded=(idx == 0)):
            # Simple summary
            st.markdown(f"**Summary:**")
            st.info(conv.get('simple_summary', 'No summary available'))

            # Clinical details
            col_mood, col_cog = st.columns(2)
            with col_mood:
                mood = conv.get('patient_mood', 'unknown')
                mood_emoji = {"positive": "😊", "neutral": "😐", "anxious": "😟", "confused": "😕"}.get(mood.lower(), "😐")
                st.markdown(f"**Mood:** {mood_emoji} {mood.capitalize()}")

            with col_cog:
                st.markdown(f"**Cognitive State:** {conv.get('cognitive_state', 'N/A')}")

            # Topics
            topics = conv.get('topics_discussed', [])
            if topics:
                st.markdown("**Topics Discussed:**")
                st.markdown("• " + "\n• ".join(topics))

            # Concerns
            concerns = conv.get('key_concerns', [])
            if concerns:
                st.warning("**⚠️ Key Concerns:**\n• " + "\n• ".join(concerns))

    st.divider()

    # Close button
    if st.button("✕ Close", use_container_width=True, type="secondary"):
        st.session_state.show_date_dialog = False
        st.rerun()


# Show dialog if triggered
if st.session_state.show_date_dialog:
    date_dialog()