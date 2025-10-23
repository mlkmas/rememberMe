# src/database.py
import os
from pymongo import MongoClient
from pymongo.results import DeleteResult
from dotenv import load_dotenv
from src.schemas import ConversationSegment, ConversationSummary, Medication, PersonProfile # <-- Added PersonProfile
from datetime import datetime, time

load_dotenv()

DB_NAME = "RememberMeDB"
SEGMENT_COLLECTION = "conversations"
SUMMARY_COLLECTION = "summaries"
MEDICATION_COLLECTION = "medications"
PEOPLE_COLLECTION = "people" # <-- New Collection

try:
    connection_string = os.getenv("MONGO_CONNECTION_STRING")
    if not connection_string: raise ValueError("MONGO_CONNECTION_STRING not found")
    client = MongoClient(connection_string)
    db = client[DB_NAME]
    segment_collection = db[SEGMENT_COLLECTION]
    summary_collection = db[SUMMARY_COLLECTION]
    medication_collection = db[MEDICATION_COLLECTION]
    people_collection = db[PEOPLE_COLLECTION] # <-- New Collection Variable
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

def get_all_medications():
    if not client: return []
    try:
        meds = list(medication_collection.find())
        meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p'))
        return meds
    except Exception as e: print(f"❌ Error fetching medications: {e}"); return []

def delete_medication(medication_id: str):
    if not client: return
    try:
        medication_collection.delete_one({"_id": medication_id})
        print(f"✅ Medication '{medication_id}' deleted.")
    except Exception as e: print(f"❌ Error deleting medication: {e}")

def update_medication(medication_id: str, updates: dict):
    if not client: return
    try:
        medication_collection.update_one({"_id": medication_id}, {"$set": updates})
        print(f"✅ Medication '{medication_id}' updated.")
    except Exception as e: print(f"❌ Error updating medication: {e}")


# --- NEW PEOPLE FUNCTIONS ---
def add_person(person: PersonProfile):
    """Saves a new person profile to the database."""
    if not client: return
    try:
        # Check if person with the same name already exists to avoid duplicates
        existing = people_collection.find_one({"name": person.name, "patient_id": person.patient_id})
        if existing:
             print(f"⚠️ Person '{person.name}' already exists.")
             return # Or update if needed
        people_collection.insert_one(person.model_dump(by_alias=True))
        print(f"✅ Person '{person.name}' saved.")
    except Exception as e:
        print(f"❌ Error saving person: {e}")

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
    except Exception as e:
        print(f"❌ Error deleting person: {e}")

# Optional: Add update_person function similar to update_medication if needed