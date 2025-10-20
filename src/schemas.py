# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class ConversationSegment(BaseModel):
    # ... (this schema stays the same) ...
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = "patient_001"
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime
    transcript: str
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "segment_id" else x

# --- UPDATE THIS SCHEMA ---
class ConversationSummary(BaseModel):
    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    segment_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Patient-facing (simple)
    simple_summary: str
    
    # Caregiver-facing (detailed) - NEW FIELDS
    topics_discussed: List[str] = []
    patient_mood: str = "unknown"
    cognitive_state: str = "unknown"
    key_concerns: List[str] = []
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "summary_id" else x