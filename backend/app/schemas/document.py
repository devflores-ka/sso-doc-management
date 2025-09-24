# backend/app/schemas/document.py
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    OBSERVED = "observed"
    EXPIRED = "expired"

class DocumentType(str, Enum):
    CONTRATO = "contrato"
    EXAMEN_MEDICO = "examen_medico"
    CERTIFICADO_ALTURA = "certificado_altura"
    EPP = "epp"
    INDUCCION = "induccion"
    ANEXO = "anexo"
    ODI = "odi"
    REGLAMENTO = "reglamento"
    OTHER = "other"

class DocumentBase(BaseModel):
    name: str
    type: DocumentType
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    worker_id: int
    company_id: int

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    status: Optional[DocumentStatus] = None
    review_comments: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    status: DocumentStatus
    upload_date: datetime
    review_date: Optional[datetime] = None
    review_comments: Optional[str] = None
    
    class Config:
        from_attributes = True