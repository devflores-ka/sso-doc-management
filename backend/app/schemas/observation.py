# backend/app/schemas/observation.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class ObservationType(str, Enum):
    FORMAT_ERROR = "format_error"
    EXPIRED = "expired"
    MISSING = "missing"
    ILLEGIBLE = "illegible"
    INCOMPLETE = "incomplete"
    OTHER = "other"

class ObservationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

class ObservationCreate(BaseModel):
    type: ObservationType
    title: str
    description: str
    deadline: datetime
    document_id: int

class ObservationUpdate(BaseModel):
    status: Optional[ObservationStatus] = None
    resolution_comments: Optional[str] = None

class ObservationResponse(BaseModel):
    id: int
    type: ObservationType
    status: ObservationStatus
    title: str
    description: str
    deadline: datetime
    document_id: int
    created_at: datetime
    resolution_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True