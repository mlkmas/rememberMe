# pages/4_Who_Is_This.py
import streamlit as st
import face_recognition
from src.database import get_all_people
import numpy as np
from PIL import Image # Import Pillow
import io # Import io

st.set_page_config(page_title="Who Is This?", page_icon="🤔", layout="centered")

st.title("🤔 Who Am I Talking To?")
st.info("Point the camera at a person and take a photo to see who they are.")

# --- Load Known Faces ---
@st.cache_data(ttl=600) # Cache for 10 minutes
def load_known_faces():
    known_face_encodings = []
    known_face_profiles = []
    
    people = get_all_people()
    for person in people:
        if "face_encoding" in person and person["face_encoding"]:
            known_face_encodings.append(np.array(person["face_encoding"]))
            known_face_profiles.append(person)
    return known_face_encodings, known_face_profiles

known_face_encodings, known_face_profiles = load_known_faces()

if not known_face_encodings:
    st.error("No faces have been saved. Please add people and their photos in the 🛠️ Admin Tools page first.")
else:
    # 1. Take a picture
    img_file_buffer = st.camera_input("Take a photo")

    if img_file_buffer:
        with st.spinner("Analyzing..."):
            # 3. Process the new photo
            # Convert buffer to PIL Image
            img = Image.open(io.BytesIO(img_file_buffer.getvalue()))
            # Convert to numpy array
            unknown_image = np.array(img)
            
            # Find face locations and encodings
            unknown_encodings = face_recognition.face_encodings(unknown_image)

            if not unknown_encodings:
                st.warning("I couldn't find a clear face in that photo. Please try again.")
            else:
                # 4. Compare the face to the ones you know
                unknown_encoding = unknown_encodings[0] # Just check the first face
                matches = face_recognition.compare_faces(known_face_encodings, unknown_encoding)
                
                found_match = False
                for i, match in enumerate(matches):
                    if match:
                        # 5. Show the result!
                        profile = known_face_profiles[i]
                        st.success(f"I see **{profile['name']} ({profile['relationship']})**!")
                        
                        photo_path = profile['photo_url']
                        if Path(photo_path).exists():
                            st.image(photo_path, width=200)
                        else:
                            st.image('https://via.placeholder.com/150', width=200)
                            
                        st.write(f"**Notes:** {profile.get('notes', 'N/A')}")
                        found_match = True
                        break
                
                if not found_match:
                    st.error("I don't recognize that person.")