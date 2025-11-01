# pages/1_Caregiver_Dashboard.py
import streamlit as st
from datetime import datetime, timedelta
from src.database import get_all_conversations
from src.caregiver_chatbot import answer_caregiver_question
import pandas as pd
import calendar

st.set_page_config(page_title="Caregiver Dashboard", page_icon="🩺", layout="wide")

# Custom CSS
st.markdown("""
<style>
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
    .chatbot-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .chat-message {
        background: white;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .chat-user {
        background: #e3f2fd;
        text-align: right;
    }
    .chat-assistant {
        background: #f1f8e9;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🩺 Caregiver Dashboard")
st.caption("Monitor conversations, patterns, and ask questions")
st.divider()

# Initialize session state
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None
if 'show_date_dialog' not in st.session_state:
    st.session_state.show_date_dialog = False
if 'current_month' not in st.session_state:
    st.session_state.current_month = datetime.now().month
if 'current_year' not in st.session_state:
    st.session_state.current_year = datetime.now().year
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "month"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'show_chatbot' not in st.session_state:
    st.session_state.show_chatbot = False

# Fetch data
all_summaries = get_all_conversations()

conversations_by_date = {}
for summary in all_summaries:
    date = summary.get('generated_at', datetime.now()).date()
    if date not in conversations_by_date:
        conversations_by_date[date] = []
    conversations_by_date[date].append(summary)

# ========================================
# TOP BAR: Chatbot Toggle + Refresh
# ========================================
col_chat_toggle, col_refresh = st.columns([3, 1])

with col_chat_toggle:
    if st.button("💬 AI Assistant" if not st.session_state.show_chatbot else "📊 Hide Assistant",
                 use_container_width=True, type="primary"):
        st.session_state.show_chatbot = not st.session_state.show_chatbot
        st.rerun()

with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ========================================
# CHATBOT INTERFACE (if enabled)
# ========================================
if st.session_state.show_chatbot:
    st.markdown("### 🤖 AI Assistant")
    st.caption("Ask me anything about the patient's recent conversations")

    with st.container():
        st.markdown('<div class="chatbot-container">', unsafe_allow_html=True)

        # Display chat history
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f'<div class="chat-message chat-user">👤 You: {msg["content"]}</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message chat-assistant">🤖 Assistant: {msg["content"]}</div>',
                                unsafe_allow_html=True)
        else:
            st.info(
                "Ask me questions like:\n- How has the patient's mood been this week?\n- Did they mention any family members?\n- What concerns came up recently?")

        st.markdown('</div>', unsafe_allow_html=True)

        # Input for new question
        col_input, col_send = st.columns([4, 1])

        with col_input:
            user_question = st.text_input("Your question:", key="chatbot_input",
                                          placeholder="How has the patient been feeling?")

        with col_send:
            if st.button("Send", use_container_width=True, type="primary"):
                if user_question.strip():
                    # Add user message
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': user_question
                    })

                    # Get AI response
                    with st.spinner("🤔 Analyzing data..."):
                        answer = answer_caregiver_question(user_question)

                    # Add assistant response
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': answer
                    })

                    st.rerun()

        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    st.divider()

# ========================================
# VIEW MODE SELECTOR
# ========================================
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

    # Calendar grid
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    header_cols = st.columns(7)
    for idx, day_name in enumerate(day_names):
        with header_cols[idx]:
            st.markdown(
                f"<div style='text-align: center; font-weight: 600; color: #6b7280; margin-bottom: 10px;'>{day_name}</div>",
                unsafe_allow_html=True)

    today = datetime.now().date()

    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            with week_cols[idx]:
                if day == 0:
                    st.markdown("<div style='min-height: 100px;'></div>", unsafe_allow_html=True)
                else:
                    date_obj = datetime(st.session_state.current_year, st.session_state.current_month, day).date()
                    day_conversations = conversations_by_date.get(date_obj, [])

                    is_today = date_obj == today
                    has_data = len(day_conversations) > 0

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

                    if st.button(f"{day}", key=f"day_{date_obj}", use_container_width=True,
                                 disabled=not has_data and not is_today):
                        st.session_state.selected_date = date_obj
                        st.session_state.show_date_dialog = True
                        st.rerun()

                    if has_data:
                        st.markdown(
                            f"<div style='text-align: center;'><span style='background: #3b82f6; color: white; border-radius: 12px; padding: 2px 8px; font-size: 12px;'>{len(day_conversations)} 💬</span></div>",
                            unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align: center; font-size: 20px;'>{mood_emoji}</div>",
                                    unsafe_allow_html=True)

# ========================================
# WEEK VIEW
# ========================================
elif st.session_state.view_mode == "week":
    st.markdown("### 📊 This Week's Activity")

    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]

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
# LIST VIEW
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

                # Show CAREGIVER summary (not patient summary)
                caregiver_summary = item.get('caregiver_summary', item.get('simple_summary', 'No summary'))
                st.markdown(f"**Summary:** {caregiver_summary}")

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
# SIDEBAR ANALYTICS
# ========================================
with st.sidebar:
    st.markdown("### 📊 Quick Stats")

    st.markdown(f"""
    <div class='stats-card'>
        <div class='stats-number'>{len(all_summaries)}</div>
        <div class='stats-label'>Total Conversations</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    this_week = [s for s in all_summaries if s.get('generated_at', datetime.now()).date() >= start_of_week]

    st.metric("This Week", len(this_week))

    if all_summaries:
        moods = [s.get('patient_mood', 'unknown').lower() for s in all_summaries]
        mood_counts = pd.Series(moods).value_counts()

        st.markdown("### 😊 Overall Mood")
        for mood, count in mood_counts.items():
            percentage = (count / len(moods)) * 100
            st.progress(percentage / 100, text=f"{mood.capitalize()}: {percentage:.0f}%")

    st.divider()

    all_concerns = []
    for s in all_summaries:
        all_concerns.extend([c.strip() for c in s.get('key_concerns', []) if c.strip()])

    if all_concerns:
        concern_counts = pd.Series(all_concerns).value_counts()
        st.markdown("### ⚠️ Top Concerns")
        for concern, count in concern_counts.head(3).items():
            st.markdown(f"• {concern} ({count}x)")


# ========================================
# DATE DIALOG
# ========================================
@st.dialog("📅 Conversations Summary", width="large")
def date_dialog():
    selected_date = st.session_state.selected_date
    day_conversations = conversations_by_date.get(selected_date, [])

    st.markdown(f"### {selected_date.strftime('%A, %B %d, %Y')}")

    if not day_conversations:
        st.info("No conversations recorded on this day.")
        if st.button("Close", use_container_width=True):
            st.session_state.show_date_dialog = False
            st.rerun()
        return

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

    for idx, conv in enumerate(day_conversations):
        time_str = conv.get('generated_at', datetime.now()).strftime('%I:%M %p')

        with st.expander(f"🕐 {time_str} - {conv.get('participant', 'Unknown')}", expanded=(idx == 0)):
            # Show CAREGIVER summary
            caregiver_summary = conv.get('caregiver_summary', conv.get('simple_summary', 'No summary'))
            st.markdown(f"**Caregiver Summary:**")
            st.info(caregiver_summary)

            col_mood, col_cog = st.columns(2)
            with col_mood:
                mood = conv.get('patient_mood', 'unknown')
                mood_emoji = {"positive": "😊", "neutral": "😐", "anxious": "😟", "confused": "😕"}.get(mood.lower(), "😐")
                st.markdown(f"**Mood:** {mood_emoji} {mood.capitalize()}")

            with col_cog:
                st.markdown(f"**Cognitive State:** {conv.get('cognitive_state', 'N/A')}")

            topics = conv.get('topics_discussed', [])
            if topics:
                st.markdown("**Topics Discussed:**")
                st.markdown("• " + "\n• ".join(topics))

            concerns = conv.get('key_concerns', [])
            if concerns:
                st.warning("**⚠️ Key Concerns:**\n• " + "\n• ".join(concerns))

    st.divider()

    if st.button("✕ Close", use_container_width=True, type="secondary"):
        st.session_state.show_date_dialog = False
        st.rerun()


if st.session_state.show_date_dialog:
    date_dialog()