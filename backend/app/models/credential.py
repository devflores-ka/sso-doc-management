# backend/app/models/credential.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Credential(Base):
    __tablename__ = "credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    qr_code = Column(String(500), unique=True, nullable=False)
    token = Column(String(200), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    
    # Foreign Keys
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True))
    
    # Relationships
    worker = relationship("Worker", back_populates="credentials")
    created_by_user = relationship("User", back_populates="credentials_created")