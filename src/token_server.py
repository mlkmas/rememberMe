# src/token_server.py
import os
from flask import Flask, jsonify, request
from livekit.api import AccessToken, VideoGrant
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# This is the name of the "room" the patient and caregiver will join.
# We can make this dynamic later, but a single room is fine for now.
ROOM_NAME = "rememberme_call"


@app.route("/get_token", methods=['GET'])
def get_livekit_token():
    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        return jsonify({"error": "LiveKit server not configured"}), 500

    # Get the 'identity' from the query parameters (e.g., ?identity=patient)
    identity = request.args.get('identity', 'unknown_user')

    # Create an access token
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET,
                        identity=identity,
                        name=identity)  # You can use name to show in LiveKit

    # Define what this user can do.
    # We want them to be able to join a room.
    grant = VideoGrant(
        room=ROOM_NAME,
        room_join=True,
        can_publish=True,
        can_subscribe=True
    )

    token.add_grant(grant)

    # Return the token as a string (JWT)
    return jsonify({"token": token.to_jwt()})


if __name__ == "__main__":
    # You will run this server in a *separate* terminal from Streamlit
    print("Starting LiveKit token server on http://localhost:5000")
    app.run(port=5000)