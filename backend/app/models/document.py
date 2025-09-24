# backend/app/models/document.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base

class DocumentStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    OBSERVED = "observed"
    EXPIRED = "expired"

class DocumentType(enum.Enum):
    CONTRATO = "contrato"
    EXAMEN_MEDICO = "examen_medico"
    CERTIFICADO_ALTURA = "certificado_altura"
    EPP = "epp"
    INDUCCION = "induccion"
    ANEXO = "anexo"
    ODI = "odi"
    REGLAMENTO = "reglamento"
    OTHER = "other"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64))  # SHA256
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    
    # Dates
    issue_date = Column(Date)
    expiry_date = Column(Date)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    
    # Review info
    review_date = Column(DateTime(timezone=True))
    review_comments = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    worker = relationship("Worker", back_populates="documents")
    company = relationship("Company", back_populates="documents")
    observations = relationship("Observation", back_populates="document")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])