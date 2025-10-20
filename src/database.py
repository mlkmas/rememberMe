"""
Module for all MongoDB database interactions.
"""
import os
from pymongo import MongoClient
from pymongo.results import DeleteResult
from bson import ObjectId
from dotenv import load_dotenv
from src.schemas import ConversationSegment, ConversationSummary, Medication
from datetime import datetime, time

# Load environment variables
load_dotenv()

# --- Database Connection ---
DB_NAME = "RememberMeDB"
SEGMENT_COLLECTION = "conversations"
SUMMARY_COLLECTION = "summaries"
MEDICATION_COLLECTION = "medications"

try:
    connection_string = os.getenv("MONGO_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("MONGO_CONNECTION_STRING not found in .env file")
        
    client = MongoClient(connection_string)
    db = client[DB_NAME]
    segment_collection = db[SEGMENT_COLLECTION]
    summary_collection = db[SUMMARY_COLLECTION]
    medication_collection = db[MEDICATION_COLLECTION]
    
    # Test connection
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
        print("✅ Conversation data saved successfully.")
    except Exception as e:
        print(f"❌ Error saving conversation to database: {e}")

def get_all_conversations():
    if not client: return []
    try:
        return list(summary_collection.find().sort("generated_at", -1))
    except Exception as e:
        print(f"❌ Error fetching conversations: {e}")
        return []

def get_todays_conversations():
    if not client: return []
    try:
        start_of_day = datetime.combine(datetime.now().date(), time.min)
        query = {"generated_at": {"$gte": start_of_day}}
        return list(summary_collection.find(query).sort("generated_at", 1))
    except Exception as e:
        print(f"❌ Error fetching today's conversations: {e}")
        return []

# --- Medication Functions (UPDATED) ---
def add_medication(medication: Medication):
    """Saves a new medication to the database."""
    if not client: return
    try:
        medication_collection.insert_one(medication.model_dump(by_alias=True))
        print(f"✅ Medication '{medication.name}' saved successfully.")
    except Exception as e:
        print(f"❌ Error saving medication: {e}")

def get_all_medications():
    """Fetches all medications from the database, sorted by time."""
    if not client: return []
    try:
        meds = list(medication_collection.find())
        meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p'))
        return meds
    except Exception as e:
        print(f"❌ Error fetching medications: {e}")
        return []

# --- NEW: DELETE FUNCTION ---
def delete_medication(medication_id: str) -> DeleteResult:
    """Deletes a medication from the database by its ID."""
    if not client: return
    try:
        result = medication_collection.delete_one({"_id": medication_id})
        print(f"✅ Medication '{medication_id}' deleted successfully.")
        return result
    except Exception as e:
        print(f"❌ Error deleting medication: {e}")

# --- NEW: UPDATE FUNCTION ---
def update_medication(medication_id: str, updates: dict):
    """Updates a medication in the database."""
    if not client: return
    try:
        result = medication_collection.update_one(
            {"_id": medication_id},
            {"$set": updates}
        )
        print(f"✅ Medication '{medication_id}' updated successfully.")
        return result
    except Exception as e:
        print(f"❌ Error updating medication: {e}")

