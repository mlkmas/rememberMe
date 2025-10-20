"""
Pydantic schemas for the RememberMe AI project.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, time
import uuid

# We use Field(default_factory=...) to auto-generate IDs and timestamps

class ConversationSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = "patient_001"  # Hardcoded for now
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime
    transcript: str
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "segment_id" else x

class ConversationSummary(BaseModel):
    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    segment_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Patient-facing (simple)
    simple_summary: str
    
    # Caregiver-facing (detailed)
    participant: str = "Unknown"
    topics_discussed: List[str] = []
    patient_mood: str = "unknown"
    cognitive_state: str = "unknown"
    key_concerns: List[str] = []
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "summary_id" else x

# --- NEW SCHEMA ---
class Medication(BaseModel):
    medication_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = "patient_001" # Hardcoded for now
    name: str
    dosage: str
    purpose: str
    time_to_take: str # Storing as a string like "08:00 AM"

    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "medication_id" else x
