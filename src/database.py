"""
Module for all MongoDB database interactions.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from src.schemas import ConversationSegment, ConversationSummary
from datetime import datetime, time # <--- ADD 'time' IMPORT

# Load environment variables
load_dotenv()

# --- Database Connection ---
DB_NAME = "RememberMeDB"
SEGMENT_COLLECTION = "conversations"
SUMMARY_COLLECTION = "summaries"

try:
    connection_string = os.getenv("MONGO_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("MONGO_CONNECTION_STRING not found in .env file")
        
    client = MongoClient(connection_string)
    db = client[DB_NAME]
    segment_collection = db[SEGMENT_COLLECTION]
    summary_collection = db[SUMMARY_COLLECTION]
    
    # Test connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")

except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    client = None

# --- Database Functions ---

def save_conversation(segment: ConversationSegment, summary: ConversationSummary):
    """
    Saves a conversation segment and its summary to the database.
    """
    if not client:
        print("Database not connected. Cannot save.")
        return

    try:
        print(f"💾 Saving segment {segment.segment_id} to database...")
        segment_collection.insert_one(segment.model_dump(by_alias=True))
        
        print(f"💾 Saving summary {summary.summary_id} to database...")
        summary_collection.insert_one(summary.model_dump(by_alias=True))
        
        print("✅ Data saved successfully.")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

def get_all_conversations():
    """
    Fetches all conversation summaries from the database.
    """
    if not client: return []
    try:
        summaries = summary_collection.find().sort("generated_at", -1)
        return list(summaries)
    except Exception as e:
        print(f"❌ Error fetching from database: {e}")
        return []

# --- NEW FUNCTION ---
def get_todays_conversations():
    """
    Fetches all conversation summaries recorded today.
    """
    if not client: return []
    try:
        # Define the start of today (midnight)
        today = datetime.now().date()
        start_of_day = datetime.combine(today, time.min)

        # Query for summaries generated since the start of today
        query = {"generated_at": {"$gte": start_of_day}}
        summaries = summary_collection.find(query).sort("generated_at", 1) # Oldest first
        return list(summaries)
    except Exception as e:
        print(f"❌ Error fetching today's conversations: {e}")
        return []
