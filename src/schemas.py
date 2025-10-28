# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional # Ensure Optional is imported
from datetime import datetime, date

# --- REMOVED PyObjectId class ---
# MongoDB will generate the _id automatically.

# --- Conversation Schemas ---

class ConversationSegment(BaseModel):
    # Changed: id is now Optional[str], default=None, no default_factory
    id: Optional[str] = Field(default=None, alias="_id")
    patient_id: str = "default_patient"
    start_time: datetime
    end_time: datetime
    transcript: str

    class Config:
        populate_by_name = True
        # Allow ObjectId to be validated if needed when reading from DB
        arbitrary_types_allowed = True


class ConversationSummary(BaseModel):
    # Changed: id is now Optional[str], default=None, no default_factory
    id: Optional[str] = Field(default=None, alias="_id")
    segment_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    simple_summary: str
    participant: str
    topics_discussed: List[str]
    patient_mood: str
    cognitive_state: str
    key_concerns: List[str]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# --- Medication Schema ---

class Medication(BaseModel):
    # Changed: id is now Optional[str], default=None, no default_factory
    id: Optional[str] = Field(default=None, alias="_id")
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
        json_encoders = {datetime: lambda d: d.isoformat() if d else None}

# --- People Schema ---

class PersonProfile(BaseModel):
    # Changed: id is now Optional[str], default=None, no default_factory
    id: Optional[str] = Field(default=None, alias="_id")
    patient_id: str = "default_patient"
    name: str
    relationship: str
    photo_url: str
    notes: Optional[str] = ""
    face_encoding: Optional[List[float]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True