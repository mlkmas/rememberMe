from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import uuid

class ConversationSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = "patient_001"
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
    simple_summary: str
    participant: Optional[str] = None
    topics_discussed: List[str] = []
    patient_mood: str = "unknown"
    cognitive_state: str = "unknown"
    key_concerns: List[str] = []
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "summary_id" else x

class Medication(BaseModel):
    medication_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = "patient_001"
    name: str
    dosage: str
    purpose: str
    time_to_take: str
    
    # Advanced Scheduling Fields
    schedule_type: str  # "Daily", "Weekly", "One-Time"
    
    # For 'Weekly'
    days_of_week: Optional[List[str]] = None
    
    # --- THE FIX IS HERE ---
    # For 'One-Time' - This now expects a full datetime object
    specific_date: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "medication_id" else x

