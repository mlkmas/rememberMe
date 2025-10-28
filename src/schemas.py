# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from uuid import uuid4

# --- Helper for MongoDB's _id ---
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not isinstance(v, str):
            raise TypeError('string required')
        # Generate a new string ID if v is None or empty
        if v is None or not v.strip():
            return str(uuid4())
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type='string')

# --- Conversation Schemas ---

class ConversationSegment(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    patient_id: str = "default_patient"
    start_time: datetime
    end_time: datetime
    transcript: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

class ConversationSummary(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    segment_id: str
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
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

# --- Medication Schema ---

class Medication(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    dosage: str
    purpose: str
    time_to_take: str
    schedule_type: str
    days_of_week: Optional[List[str]] = None
    specific_date: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda d: d.isoformat()}

# --- People Schema ---

class PersonProfile(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    patient_id: str = "default_patient"
    name: str
    relationship: str
    photo_url: str
    notes: Optional[str] = ""
    face_encoding: Optional[List[float]] = None # <-- ADDED FOR STEP 4

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}