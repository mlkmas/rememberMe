"""
Module for all MongoDB database interactions.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from src.schemas import ConversationSegment, ConversationSummary

# Load environment variables (MONGO_CONNECTION_STRING)
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
        # Convert Pydantic models to dicts for MongoDB
        # We use by_alias=True to use "_id" instead of "segment_id"
        print(f"💾 Saving segment {segment.segment_id} to database...")
        segment_collection.insert_one(segment.model_dump(by_alias=True))
        
        print(f"💾 Saving summary {summary.summary_id} to database...")
        summary_collection.insert_one(summary.model_dump(by_alias=True))
        
        print("✅ Data saved successfully.")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

def get_all_conversations():
    """
    Fetches all conversations and their summaries from the database.
    """
    if not client:
        print("Database not connected. Cannot fetch.")
        return []

    # For simplicity, we'll just fetch all summaries for now
    # A real app would use a more complex query (a $lookup pipeline)
    
    try:
        summaries = summary_collection.find().sort("generated_at", -1) # Get newest first
        return list(summaries) # Return a list of dicts
    except Exception as e:
        print(f"❌ Error fetching from database: {e}")
        return []