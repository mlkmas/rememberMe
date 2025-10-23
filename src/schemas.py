# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from uuid import uuid4

# --- Helper for MongoDB's _id ---
# This lets us use 'id' in our code but store it as '_id' in Mongo
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not isinstance(v, str):
            raise TypeError('string required')
        if not v.strip(): # Handle empty strings if needed
             raise ValueError('string must not be empty')
        return str(v) # Return it as a string

# --- Conversation Schemas ---

class ConversationSegment(BaseModel):
    id: PyObjectId = Field(default_factory=lambda: str(uuid4()), alias="_id")
    patient_id: str = "default_patient" # Hardcoded for now
    start_time: datetime
    end_time: datetime
    transcript: str
    
    class Config:
        populate_by_name = True # Use the alias "_id"
        json_encoders = {PyObjectId: str}

class ConversationSummary(BaseModel):
    id: PyObjectId = Field(default_factory=lambda: str(uuid4()), alias="_id")
    segment_id: str # Links to the ConversationSegment
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Patient-facing
    simple_summary: str
    
    # Caregiver-facing (from summarizer.py)
    participant: str
    topics_discussed: List[str]
    patient_mood: str
    cognitive_state: str
    key_concerns: List[str]
    
    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}

# --- Medication Schema ---

class Medication(BaseModel):
    id: PyObjectId = Field(default_factory=lambda: str(uuid4()), alias="_id")
    name: str
    dosage: str
    purpose: str
    time_to_take: str # e.g., "08:00 AM"
    schedule_type: str # "Daily", "Weekly", "One-Time"
    days_of_week: Optional[List[str]] = None # For "Weekly"
    specific_date: Optional[datetime] = None # For "One-Time"
    
    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str, datetime: lambda d: d.isoformat()}

# --- People Schema (THIS IS THE ONE YOU WERE MISSING) ---

class PersonProfile(BaseModel):
    id: PyObjectId = Field(default_factory=lambda: str(uuid4()), alias="_id")
    patient_id: str = "default_patient" # Hardcoded for now
    name: str
    relationship: str # "Daughter", "Son", "Caregiver"
    photo_url: str
    notes: Optional[str] = ""
    
    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}