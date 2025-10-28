# pages/4_Who_Is_This.py
import streamlit as st
import face_recognition
from src.database import get_all_people
import numpy as np
from PIL import Image # For handling image buffer
import io # For handling image buffer
from pathlib import Path # For checking local image paths

st.set_page_config(page_title="Who Is This?", page_icon="🤔", layout="centered")

st.title("🤔 Who Am I Talking To?")
st.info("Point the camera at a person and take a photo to see who they are.")

# --- Load Known Faces ---
# Cache the loaded faces to avoid reloading on every interaction within TTL
@st.cache_data(ttl=300) # Cache for 5 minutes
def load_known_faces_from_db():
    print("--- DEBUG: Loading known faces from DB ---") # Debug print
    known_face_encodings_db = []
    known_face_profiles_db = []
    try:
        people = get_all_people()
        print(f"--- DEBUG: Found {len(people)} people in DB ---") # Debug print
        for person in people:
            # Check if 'face_encoding' exists and is a non-empty list
            if "face_encoding" in person and isinstance(person["face_encoding"], list) and person["face_encoding"]:
                try:
                    # Convert list back to numpy array for comparison
                    known_face_encodings_db.append(np.array(person["face_encoding"]))
                    known_face_profiles_db.append(person)
                    print(f"--- DEBUG: Loaded face encoding for {person.get('name', 'N/A')} ---") # Debug print
                except Exception as e:
                     print(f"--- DEBUG: Error converting encoding for {person.get('name', 'N/A')}: {e} ---") # Debug print for conversion error
            else:
                 print(f"--- DEBUG: No valid face encoding found for {person.get('name', 'N/A')} ---") # Debug print

        print(f"--- DEBUG: Successfully loaded {len(known_face_profiles_db)} profiles with face encodings ---") # Debug print
    except Exception as e:
         print(f"--- DEBUG: Error loading people from DB: {e} ---") # Debug print for DB error
         st.error(f"Error loading people data: {e}") # Show error in UI

    return known_face_encodings_db, known_face_profiles_db

# Load the data using the cached function
known_face_encodings, known_face_profiles = load_known_faces_from_db()

# Check if any faces were loaded AFTER the function call
if not known_face_encodings:
    st.error("No faces have been saved with encoding data yet. Please add people and clear photos via the 🛠️ Admin Tools page.")
else:
    st.success(f"Loaded {len(known_face_profiles)} known faces. Ready to recognize!") # Confirmation message
    # --- Camera Input ---
    img_file_buffer = st.camera_input("Take a photo")

    if img_file_buffer is not None:
        with st.spinner("Analyzing photo..."):
            try:
                # --- Process Captured Image ---
                # Convert buffer to PIL Image object
                pil_image = Image.open(io.BytesIO(img_file_buffer.getvalue()))
                # Convert PIL Image to numpy array (required by face_recognition)
                unknown_image_arr = np.array(pil_image)
                print("--- DEBUG: Captured image loaded into numpy array ---") # Debug print

                # Find all face locations and encodings in the unknown image
                # Using 'cnn' model can be more accurate but slower, 'hog' is faster
                unknown_encodings = face_recognition.face_encodings(unknown_image_arr, model="hog")
                print(f"--- DEBUG: Found {len(unknown_encodings)} face(s) in captured image ---") # Debug print

                if not unknown_encodings:
                    st.warning("I couldn't find a clear face in that photo. Please try again.")
                else:
                    # --- Compare Faces ---
                    # Compare the first detected face against all known faces
                    unknown_encoding = unknown_encodings[0]
                    # compare_faces returns a list of True/False for each known face
                    matches = face_recognition.compare_faces(known_face_encodings, unknown_encoding, tolerance=0.6) # Default tolerance is 0.6
                    print(f"--- DEBUG: Comparison results (True means match): {matches} ---") # Debug print

                    # Find the indices of all matches
                    match_indices = [i for i, match in enumerate(matches) if match]

                    if not match_indices:
                        st.error("I don't recognize this person.")
                    else:
                        # Display info for the first match found
                        first_match_index = match_indices[0]
                        profile = known_face_profiles[first_match_index]
                        name = profile.get('name', 'N/A')
                        relationship = profile.get('relationship', 'N/A')
                        notes = profile.get('notes', 'N/A')
                        photo_path = profile.get('photo_url', '')

                        st.success(f"I see **{name} ({relationship})**!")
                        print(f"--- DEBUG: Match found: {name} ---") # Debug print

                        # Display the stored photo of the recognized person
                        if Path(photo_path).is_file(): # Check if local path exists
                            st.image(photo_path, width=200)
                        elif photo_path.startswith("http"): # Basic check if it's a URL
                             st.image(photo_path, width=200)
                        else:
                            st.image('https://via.placeholder.com/150', width=200) # Fallback

                        st.write(f"**Notes:** {notes}")

                        # Optional: Calculate and display confidence (face distance)
                        face_distances = face_recognition.face_distance(known_face_encodings, unknown_encoding)
                        best_match_distance = face_distances[first_match_index]
                        st.caption(f"Match confidence (lower is better): {1 - best_match_distance:.2f}")


            except Exception as e:
                st.error(f"An error occurred during face recognition: {e}")
                print(f"--- DEBUG: Error during face recognition process: {e} ---") # Debug print