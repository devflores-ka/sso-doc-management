# backend/app/models/worker.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Worker(Base):
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    run = Column(String(12), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    position = Column(String(100), nullable=False)
    entry_date = Column(Date)
    is_active = Column(Boolean, default=True)
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="workers")
    documents = relationship("Document", back_populates="worker")
    credentials = relationship("Credential", back_populates="worker")