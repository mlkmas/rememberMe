# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, time as time_type


# --- Conversation Schemas ---

class ConversationSegment(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    patient_id: str = "default_patient"
    start_time: datetime
    end_time: datetime
    transcript: str
    speaker_identity: str = "patient"  # NEW: Track who was speaking

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ConversationSummary(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    segment_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    simple_summary: str
    caregiver_summary: str = ""  # NEW: Summary for caregiver perspective
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
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    dosage: str
    purpose: str
    time_to_take: str
    schedule_type: str
    days_of_week: Optional[List[str]] = None
    specific_date: Optional[datetime] = None
    last_reminded: Optional[datetime] = None  # NEW: Track last reminder

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda d: d.isoformat() if d else None}


# --- People Schema ---

class PersonProfile(BaseModel):
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


# --- NEW: Settings Schema ---

class AppSettings(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    daily_recap_enabled: bool = True
    daily_recap_time: str = "19:00"  # 7 PM default
    assistant_mode_enabled: bool = False
    livekit_session_active: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True