# src/database.py
import os
from pymongo import MongoClient
from pymongo.results import DeleteResult, InsertOneResult
from dotenv import load_dotenv
from src.schemas import ConversationSegment, ConversationSummary, Medication, PersonProfile
from datetime import datetime, time
import streamlit as st

load_dotenv()

DB_NAME = "RememberMeDB"
SEGMENT_COLLECTION = "conversations"
SUMMARY_COLLECTION = "summaries"
MEDICATION_COLLECTION = "medications"
PEOPLE_COLLECTION = "people"

try:
    connection_string = os.getenv("MONGO_CONNECTION_STRING")
    if not connection_string: raise ValueError("MONGO_CONNECTION_STRING not found")
    client = MongoClient(connection_string)
    db = client[DB_NAME]
    segment_collection = db[SEGMENT_COLLECTION]
    summary_collection = db[SUMMARY_COLLECTION]
    medication_collection = db[MEDICATION_COLLECTION]
    people_collection = db[PEOPLE_COLLECTION] 
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    client = None

# --- Conversation Functions (Unchanged) ---
def save_conversation(segment: ConversationSegment, summary: ConversationSummary):
    if not client: return
    try:
        segment_collection.insert_one(segment.model_dump(by_alias=True))
        summary_collection.insert_one(summary.model_dump(by_alias=True))
        print("✅ Conversation data saved.")
    except Exception as e: print(f"❌ Error saving conversation: {e}")

@st.cache_data(ttl=60) # Cache for 60 seconds
def get_all_conversations():
    if not client: return []
    try: return list(summary_collection.find().sort("generated_at", -1))
    except Exception as e: print(f"❌ Error fetching conversations: {e}"); return []

def get_todays_conversations():
    if not client: return []
    try:
        start_of_day = datetime.combine(datetime.now().date(), time.min)
        query = {"generated_at": {"$gte": start_of_day}}
        return list(summary_collection.find(query).sort("generated_at", 1))
    except Exception as e: print(f"❌ Error fetching today's conversations: {e}"); return []

# --- Medication Functions (Unchanged) ---
def add_medication(medication: Medication):
    if not client: return
    try:
        medication_collection.insert_one(medication.model_dump(by_alias=True))
        print(f"✅ Medication '{medication.name}' saved.")
    except Exception as e: print(f"❌ Error saving medication: {e}")

@st.cache_data(ttl=60) # Cache for 60 seconds
def get_all_medications():
    if not client: return []
    try:
        meds = list(medication_collection.find())
        # Sort by time
        meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())
        return meds
    except Exception as e: print(f"❌ Error fetching medications: {e}"); return []

def delete_medication(medication_id: str):
    if not client: return
    try:
        medication_collection.delete_one({"_id": medication_id})
        print(f"✅ Medication '{medication_id}' deleted.")
        get_all_medications.clear() # Clear cache
    except Exception as e: print(f"❌ Error deleting medication: {e}")

def update_medication(medication_id: str, updates: dict):
    if not client: return
    try:
        medication_collection.update_one({"_id": medication_id}, {"$set": updates})
        print(f"✅ Medication '{medication_id}' updated.")
        get_all_medications.clear() # Clear cache
    except Exception as e: print(f"❌ Error updating medication: {e}")


# --- PEOPLE FUNCTIONS (Updated) ---
def add_person(person: PersonProfile) -> str | None:
    """Saves a new person and returns their new ID."""
    if not client: return None
    try:
        existing = people_collection.find_one({"name": person.name})
        if existing:
             print(f"⚠️ Person '{person.name}' already exists.")
             return None
        
        result: InsertOneResult = people_collection.insert_one(person.model_dump(by_alias=True))
        print(f"✅ Person '{person.name}' saved.")
        get_all_people.clear() # Clear cache
        return str(result.inserted_id) # <-- RETURN THE ID
    except Exception as e:
        print(f"❌ Error saving person: {e}")
        return None

@st.cache_data(ttl=60) # Cache for 60 seconds
def get_all_people():
    """Fetches all person profiles from the database."""
    if not client: return []
    try:
        return list(people_collection.find())
    except Exception as e:
        print(f"❌ Error fetching people: {e}")
        return []

def delete_person(person_id: str):
    """Deletes a person profile by ID."""
    if not client: return
    try:
        people_collection.delete_one({"_id": person_id})
        print(f"✅ Person '{person_id}' deleted.")
        get_all_people.clear() # Clear cache
    except Exception as e: print(f"❌ Error deleting person: {e}")

# --- NEW FUNCTION FOR STEP 4 ---
def update_person(person_id: str, updates: dict):
    """Updates a person record with new data (e.g., face encoding)."""
    if not client: return
    try:
        people_collection.update_one({"_id": person_id}, {"$set": updates})
        print(f"✅ Person '{person_id}' updated with encoding.")
        get_all_people.clear() # Clear cache
    except Exception as e:
        print(f"❌ Error updating person: {e}")