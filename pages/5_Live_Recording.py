# pages/5_Live_Recording.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Live Recording", page_icon="🎙️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .status-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.2rem;
    }
    .status-online {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    .status-offline {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎙️ Live Recording Session")
st.caption("Continuous conversation recording with LiveKit")
st.divider()

# ========================================
# CHECK SYSTEM STATUS
# ========================================

# Check token server
token_server_running = False
try:
    response = requests.get("http://localhost:5000/health", timeout=2)
    token_server_running = response.status_code == 200
except:
    pass

# Get credentials
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")

# Display status
col_status1, col_status2 = st.columns(2)

with col_status1:
    if token_server_running:
        st.markdown('<div class="status-box status-online">🟢 Token Server: Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box status-offline">🔴 Token Server: Offline</div>', unsafe_allow_html=True)

with col_status2:
    if LIVEKIT_URL:
        st.markdown('<div class="status-box status-online">🟢 LiveKit: Configured</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box status-offline">🔴 LiveKit: Not Configured</div>', unsafe_allow_html=True)

st.divider()

# ========================================
# HANDLE MISSING CONFIGURATION
# ========================================

if not token_server_running:
    st.error("❌ Token server is not running!")
    st.markdown("### 🚀 Start the token server:")
    st.code("poetry run python src/token_server.py", language="bash")
    st.info("💡 Run this command in **Terminal 1**, then refresh this page")
    st.stop()

if not LIVEKIT_URL:
    st.error("❌ LIVEKIT_URL not found in .env file!")
    st.markdown("### 📝 Add to your .env file:")
    st.code("""
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
    """, language="bash")
    st.stop()

# ========================================
# MAIN INTERFACE
# ========================================

st.success("✅ All systems ready!")

# Get token from server
try:
    response = requests.get("http://localhost:5000/get_token?identity=caregiver_web")
    token_data = response.json()
    token = token_data["token"]

    st.markdown("### 🎤 Join the Recording Room")

    # Show room info
    st.info(f"**Room:** {token_data.get('room', 'rememberme_call')}")

    # Create proper LiveKit URL
    # Use the official LiveKit Meet with proper parameters
    meet_url = f"https://meet.livekit.io/custom?liveKitUrl={LIVEKIT_URL}&token={token}"

    # Display instructions
    col_inst1, col_inst2 = st.columns([2, 1])

    with col_inst1:
        st.markdown("""
        **What will happen:**
        1. Click button below to open LiveKit room
        2. Allow microphone access when prompted
        3. Start speaking (you should see audio indicator)
        4. Backend agent is listening and will save conversations
        5. Stop speaking for 5 seconds to end conversation
        6. Check Terminal 2 for processing logs
        7. Go to Dashboard to see saved conversations!
        """)

    with col_inst2:
        st.markdown("**Status Indicators:**")
        st.markdown("🔴 = Recording")
        st.markdown("🟢 = Microphone active")
        st.markdown("⚪ = Idle")

    st.divider()

    # Button to open room
    if st.button("🚀 Open LiveKit Room", type="primary", use_container_width=True):
        # Display the URL for manual access
        st.success("✅ Opening LiveKit room in new window...")
        st.markdown(f"**If window didn't open, click here:** [Open LiveKit Room]({meet_url})")

        # JavaScript to open in new window
        st.components.v1.html(f"""
        <script>
            window.open('{meet_url}', '_blank', 'width=1200,height=800');
        </script>
        <p style='color: green; font-weight: bold;'>✅ Room opened! Check for new browser window.</p>
        """, height=100)

    st.divider()

    # Embed option (alternative)
    st.markdown("### 🖥️ Or Use Embedded Room")

    if st.button("📺 Show Embedded Room", use_container_width=True):
        st.markdown("**LiveKit Room (Embedded):**")

        # Embed LiveKit room directly
        st.components.v1.iframe(
            src=meet_url,
            height=600,
            scrolling=False
        )

    st.divider()

    # ========================================
    # TESTING GUIDE
    # ========================================

    st.markdown("### 🧪 Complete Testing Guide")

    with st.expander("📋 Step-by-Step Testing Instructions", expanded=False):
        st.markdown("""
        **Terminal Setup (3 terminals needed):**

        **Terminal 1: Token Server** ✅ (Should be running)
```bash
        poetry run python src/token_server.py
```
        Expected: `Running on http://127.0.0.1:5000`

        **Terminal 2: LiveKit Agent** (Check if running)
```bash
        poetry run python src/livekit_client.py
```
        Expected: `✅ Agent is running and listening for audio`

        **Terminal 3: Streamlit** ✅ (Currently running)
```bash
        poetry run streamlit run app.py
```

        ---

        **Testing Steps:**

        1. ✅ Verify all 3 terminals are running
        2. ✅ Click "🚀 Open LiveKit Room" button above
        3. ✅ Allow microphone access in browser
        4. ✅ You should see your name/icon in the room
        5. ✅ Speak clearly for 10-15 seconds
        6. ✅ Check Terminal 2 for these logs:
           - `🎵 New audio track from: caregiver_web`
           - `🎙️ Conversation started - Recording...`
        7. ✅ Stop speaking (wait 5 seconds for silence)
        8. ✅ Check Terminal 2 for:
           - `🛑 Silence detected - Ending conversation`
           - `💾 Saving conversation...`
           - `🤖 Transcribing...`
           - `🎉 Conversation saved to database!`
        9. ✅ Go to Dashboard page
        10. ✅ See your conversation in the calendar!

        ---

        **Troubleshooting:**

        **Problem: "No audio detected"**
        - Check microphone permissions in browser
        - Verify you see audio indicator in LiveKit room
        - Check Terminal 2 for error messages

        **Problem: "Not recording"**
        - Verify Terminal 2 shows: `🎵 New audio track from: caregiver_web`
        - Speak louder or adjust ENERGY_THRESHOLD in livekit_client.py

        **Problem: "Conversation not saving"**
        - Check Terminal 2 for error messages
        - Verify MongoDB connection in .env
        - Check OpenAI API key is valid
        """)

    # ========================================
    # TERMINAL STATUS CHECK
    # ========================================

    st.markdown("### 🖥️ Terminal Status Check")

    col_t1, col_t2, col_t3 = st.columns(3)

    with col_t1:
        st.markdown("**Terminal 1:**")
        if token_server_running:
            st.success("✅ Token Server Running")
        else:
            st.error("❌ Not Running")

    with col_t2:
        st.markdown("**Terminal 2:**")
        st.warning("⚠️ Check terminal output")
        st.caption("Should show: 'Agent is running'")

    with col_t3:
        st.markdown("**Terminal 3:**")
        st.success("✅ Streamlit Running")
        st.caption("(You're here!)")

    st.divider()

    # ========================================
    # QUICK LINKS
    # ========================================

    st.markdown("### 🔗 Quick Links")

    col_link1, col_link2 = st.columns(2)

    with col_link1:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/1_Caregiver_Dashboard.py")

    with col_link2:
        if st.button("🛠️ Admin Tools", use_container_width=True):
            st.switch_page("pages/3_Admin_Tools.py")

except Exception as e:
    st.error(f"❌ Error: {e}")
    st.markdown("**Debug Info:**")
    st.code(f"""
    LIVEKIT_URL: {LIVEKIT_URL}
    Token Server: {token_server_running}
    Error: {str(e)}
    """)

