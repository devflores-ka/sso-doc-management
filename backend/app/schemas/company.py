# backend/app/schemas/company.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .worker import WorkerResponse

class CompanyBase(BaseModel):
    rut: str = Field(..., min_length=8, max_length=12)
    name: str
    business_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class CompanyResponse(CompanyBase):
    id: int
    is_active: bool
    created_at: datetime
    workers_count: Optional[int] = 0
    documents_count: Optional[int] = 0
    compliance_percentage: Optional[float] = 0.0
    
    class Config:
        from_attributes = True

class CompanyWithDetails(CompanyResponse):
    workers: List[WorkerResponse] = []
    