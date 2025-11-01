# src/database.py
import streamlit as st
import os
from pymongo import MongoClient
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult
from bson.objectid import ObjectId, InvalidId
from dotenv import load_dotenv
from src.schemas import ConversationSegment, ConversationSummary, Medication, PersonProfile, AppSettings
from datetime import datetime, time

load_dotenv()

DB_NAME = "RememberMeDB"
SEGMENT_COLLECTION = "conversations"
SUMMARY_COLLECTION = "summaries"
MEDICATION_COLLECTION = "medications"
PEOPLE_COLLECTION = "people"
SETTINGS_COLLECTION = "settings"  # NEW

try:
    connection_string = os.getenv("MONGO_CONNECTION_STRING")
    if not connection_string: raise ValueError("MONGO_CONNECTION_STRING not found in .env file")
    client = MongoClient(connection_string)
    db = client[DB_NAME]
    segment_collection = db[SEGMENT_COLLECTION]
    summary_collection = db[SUMMARY_COLLECTION]
    medication_collection = db[MEDICATION_COLLECTION]
    people_collection = db[PEOPLE_COLLECTION]
    settings_collection = db[SETTINGS_COLLECTION]  # NEW
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    client = None

def convert_document_id(doc):
    """Converts MongoDB ObjectId _id to string 'id'."""
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
    return doc

# --- Conversation Functions ---
def save_conversation(segment: ConversationSegment, summary: ConversationSummary):
    if not client: return
    try:
        segment_data = segment.model_dump(by_alias=True, exclude_none=True)
        summary_data = summary.model_dump(by_alias=True, exclude_none=True)
        if '_id' in segment_data: del segment_data['_id']
        if '_id' in summary_data: del summary_data['_id']
        segment_collection.insert_one(segment_data)
        summary_collection.insert_one(summary_data)
        print("✅ Conversation data saved.")
    except Exception as e: print(f"❌ Error saving conversation: {e}")

@st.cache_data(ttl=60)
def get_all_conversations():
    if not client: return []
    try:
        docs = list(summary_collection.find().sort("generated_at", -1))
        return [convert_document_id(doc) for doc in docs]
    except Exception as e: print(f"❌ Error fetching conversations: {e}"); return []

def get_todays_conversations():
    if not client: return []
    try:
        start_of_day = datetime.combine(datetime.now().date(), time.min)
        query = {"generated_at": {"$gte": start_of_day}}
        docs = list(summary_collection.find(query).sort("generated_at", 1))
        return [convert_document_id(doc) for doc in docs]
    except Exception as e: print(f"❌ Error fetching today's conversations: {e}"); return []

def get_recent_conversations(days=7):
    """NEW: Get conversations from last N days"""
    if not client: return []
    try:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        query = {"generated_at": {"$gte": cutoff}}
        docs = list(summary_collection.find(query).sort("generated_at", -1))
        return [convert_document_id(doc) for doc in docs]
    except Exception as e: print(f"❌ Error fetching recent conversations: {e}"); return []

# --- Medication Functions ---
def add_medication(medication: Medication) -> str | None:
    if not client: return None
    try:
        med_data = medication.model_dump(by_alias=True, exclude_none=True)
        if '_id' in med_data: del med_data['_id']
        result: InsertOneResult = medication_collection.insert_one(med_data)
        new_id = str(result.inserted_id)
        print(f"✅ Medication '{medication.name}' saved with ID: {new_id}.")
        get_all_medications.clear()
        return new_id
    except Exception as e: print(f"❌ Error saving medication: {e}"); return None

@st.cache_data(ttl=60)
def get_all_medications():
    if not client: return []
    try:
        meds = list(medication_collection.find())
        meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())
        return [convert_document_id(med) for med in meds]
    except Exception as e: print(f"❌ Error fetching medications: {e}"); return []

def delete_medication(medication_id: str):
    if not client: return
    try:
        obj_id = ObjectId(medication_id)
        result: DeleteResult = medication_collection.delete_one({"_id": obj_id})
        if result.deleted_count > 0:
            print(f"✅ Medication '{medication_id}' deleted.")
            get_all_medications.clear()
        else:
            print(f"⚠️ Medication '{medication_id}' not found.")
    except InvalidId:
         print(f"❌ Error: Invalid ID format for deletion: {medication_id}")
    except Exception as e: print(f"❌ Error deleting medication: {e}")

def update_medication(medication_id: str, updates: dict):
    if not client: return
    try:
        obj_id = ObjectId(medication_id)
        result: UpdateResult = medication_collection.update_one({"_id": obj_id}, {"$set": updates})
        if result.matched_count > 0:
            print(f"✅ Medication '{medication_id}' updated.")
            get_all_medications.clear()
        else:
            print(f"⚠️ Medication '{medication_id}' not found.")
    except InvalidId:
         print(f"❌ Error: Invalid ID format for update: {medication_id}")
    except Exception as e: print(f"❌ Error updating medication: {e}")

# --- People Functions ---
def add_person(person: PersonProfile) -> str | None:
    if not client: return None
    try:
        existing = people_collection.find_one({"name": person.name})
        if existing:
             print(f"⚠️ Person '{person.name}' already exists.")
             return str(existing['_id'])
        person_data = person.model_dump(by_alias=True, exclude_none=True)
        if '_id' in person_data: del person_data['_id']
        result: InsertOneResult = people_collection.insert_one(person_data)
        new_id = str(result.inserted_id)
        print(f"✅ Person '{person.name}' saved with ID: {new_id}.")
        get_all_people.clear()
        return new_id
    except Exception as e:
        print(f"❌ Error saving person: {e}")
        return None

@st.cache_data(ttl=60)
def get_all_people():
    if not client: return []
    try:
        people_docs = list(people_collection.find())
        return [convert_document_id(person) for person in people_docs]
    except Exception as e:
        print(f"❌ Error fetching people: {e}")
        return []

def delete_person(person_id: str):
    if not client: return
    try:
        obj_id = ObjectId(person_id)
        result: DeleteResult = people_collection.delete_one({"_id": obj_id})
        if result.deleted_count > 0:
            print(f"✅ Person '{person_id}' deleted.")
            get_all_people.clear()
        else:
            print(f"⚠️ Person '{person_id}' not found.")
    except InvalidId:
         print(f"❌ Error: Invalid ID format for deletion: {person_id}")
    except Exception as e: print(f"❌ Error deleting person: {e}")

def update_person(person_id: str, updates: dict):
    if not client: return
    try:
        obj_id = ObjectId(person_id)
        result: UpdateResult = people_collection.update_one({"_id": obj_id}, {"$set": updates})
        if result.matched_count > 0:
            print(f"✅ Person '{person_id}' updated.")
            get_all_people.clear()
        else:
            print(f"⚠️ Person '{person_id}' not found.")
    except InvalidId:
        print(f"❌ Error: Invalid ID format for update: {person_id}")
    except Exception as e:
        print(f"❌ Error updating person: {e}")

# --- NEW: Settings Functions ---
def get_settings() -> dict:
    """Get app settings, create default if doesn't exist"""
    if not client: return {}
    try:
        settings = settings_collection.find_one()
        if not settings:
            # Create default settings
            default_settings = AppSettings()
            settings_data = default_settings.model_dump(by_alias=True, exclude_none=True)
            if '_id' in settings_data: del settings_data['_id']
            settings_collection.insert_one(settings_data)
            return default_settings.model_dump()
        return convert_document_id(settings)
    except Exception as e:
        print(f"❌ Error fetching settings: {e}")
        return {}

def update_settings(updates: dict):
    """Update app settings"""
    if not client: return
    try:
        settings = settings_collection.find_one()
        if settings:
            settings_collection.update_one({"_id": settings["_id"]}, {"$set": updates})
        else:
            settings_collection.insert_one(updates)
        print(f"✅ Settings updated")
    except Exception as e:
        print(f"❌ Error updating settings: {e}")