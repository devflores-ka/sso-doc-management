# backend/app/schemas/worker.py
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List

class WorkerBase(BaseModel):
    run: str = Field(..., min_length=8, max_length=12)
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: str
    entry_date: Optional[date] = None
    company_id: int

class WorkerCreate(WorkerBase):
    pass

class WorkerUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None

class WorkerResponse(WorkerBase):
    id: int
    is_active: bool
    created_at: datetime
    documents_count: Optional[int] = 0
    compliance_status: Optional[str] = "pending"
    
    class Config:
        from_attributes = True

class WorkerWithDocuments(WorkerResponse):
    documents: List["DocumentResponse"] = []