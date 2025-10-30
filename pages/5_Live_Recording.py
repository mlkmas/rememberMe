# pages/5_Live_Recording.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Live Recording", page_icon="🎙️", layout="wide")

st.title("🎙️ Live Recording Session")
st.caption("Continuous conversation recording with LiveKit")
st.divider()

# Check token server status
token_server_running = False
try:
    response = requests.get("http://localhost:5000/get_token?identity=test", timeout=2)
    token_server_running = response.status_code == 200
except:
    pass

if not token_server_running:
    st.error("❌ Token server is not running!")
    st.markdown("### 🚀 Start the token server:")
    st.code("poetry run python src/token_server.py", language="bash")
    st.info("Run this in a separate terminal, then refresh this page")
    st.stop()

st.success("✅ Token server is running")

# Get token for web client
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

if not LIVEKIT_URL:
    st.error("LIVEKIT_URL not found in .env file")
    st.stop()

try:
    # Get token from server
    response = requests.get("http://localhost:5000/get_token?identity=caregiver_web")
    token = response.json()["token"]

    st.markdown("### 🎤 Join the Room")
    st.info("Click below to open LiveKit room in a new window, then start speaking!")

    # Room URL
    room_url = f"https://meet.livekit.io/custom?url={LIVEKIT_URL}&token={token}"

    if st.button("🚀 Open LiveKit Room", type="primary", use_container_width=True):
        st.markdown(f'<a href="{room_url}" target="_blank">Click here if window didn\'t open</a>',
                    unsafe_allow_html=True)
        st.components.v1.html(f'<script>window.open("{room_url}", "_blank");</script>')

    st.divider()

    st.markdown("### 📊 How It Works")
    st.markdown("""
    **Backend Agent (must be running):**
```bash
    poetry run python src/livekit_client.py
```

    **What happens:**
    1. You join the room (web browser)
    2. Backend agent listens to your audio
    3. Detects conversations automatically
    4. Transcribes and saves after 5 seconds of silence
    5. Check dashboard to see results!

    **Status:**
    - Token Server: 🟢 Running
    - Backend Agent: Check terminal
    """)

    st.divider()

    st.markdown("### 🧪 Testing Steps")
    st.markdown("""
    **Terminal 1:**
```bash
    poetry run python src/token_server.py
```

    **Terminal 2:**
```bash
    poetry run python src/livekit_client.py
```

    **Terminal 3:**
```bash
    poetry run streamlit run app.py
```

    **Then:**
    1. Click "Open LiveKit Room" above
    2. Allow microphone access
    3. Start speaking for 10-15 seconds
    4. Stop speaking (5 seconds silence)
    5. Check Terminal 2 for processing logs
    6. Go to Dashboard to see saved conversation!
    """)

except Exception as e:
    st.error(f"Error: {e}")