# src/token_server.py
import os
from flask import Flask, jsonify, request
from livekit import api  # Changed import
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Room name - can be made dynamic later
ROOM_NAME = "rememberme_call"


@app.route("/get_token", methods=['GET'])
def get_livekit_token():
    """Generate LiveKit access token for a user"""

    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        return jsonify({"error": "LiveKit server not configured. Check .env file"}), 500

    # Get identity from query parameters
    identity = request.args.get('identity', 'unknown_user')

    print(f"🎫 Generating token for: {identity}")

    try:
        # Create access token (CORRECTED API)
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(identity)
        token.with_name(identity)

        # Define permissions using VideoGrants (CORRECTED)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=ROOM_NAME,
            can_publish=True,
            can_subscribe=True,
        ))

        jwt_token = token.to_jwt()

        print(f"✅ Token generated successfully for {identity}")

        return jsonify({
            "token": jwt_token,
            "room": ROOM_NAME,
            "url": LIVEKIT_URL
        })

    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "livekit_configured": all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET])
    })


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting LiveKit Token Server")
    print("=" * 50)
    print(f"URL: http://localhost:5000")
    print(f"LiveKit URL: {LIVEKIT_URL}")
    print(f"Room Name: {ROOM_NAME}")
    print("=" * 50)

    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        print("⚠️  WARNING: LiveKit credentials not found in .env file!")
        print("Please add:")
        print("  LIVEKIT_URL=wss://your-project.livekit.cloud")
        print("  LIVEKIT_API_KEY=your_key")
        print("  LIVEKIT_API_SECRET=your_secret")
    else:
        print("✅ LiveKit credentials loaded")

    print("=" * 50)

    app.run(port=5000, debug=False)