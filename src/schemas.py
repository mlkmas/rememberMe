"""
Pydantic schemas for the RememberMe AI project.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

# We use Field(default_factory=...) to auto-generate IDs and timestamps

class ConversationSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = "patient_001"  # Hardcoded for now
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime
    transcript: str
    
    # We'll keep these simple for now, from your v1 plan
    # speakers: List[str] = []
    # location: Optional[str] = None
    
    class Config:
        # This allows Pydantic to work nicely with MongoDB's _id
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "segment_id" else x

class ConversationSummary(BaseModel):
    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    segment_id: str  # This links the summary to the segment
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Patient-facing (simple)
    simple_summary: str
    key_people: List[str] = []
    key_events: List[str] = []
    
    # We can add the clinical summary later
    # detailed_summary: Optional[str] = None
    # patient_mood: Optional[str] = None
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: "_id" if x == "summary_id" else x