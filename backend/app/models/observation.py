# backend/app/models/observation.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base

class ObservationType(enum.Enum):
    FORMAT_ERROR = "format_error"
    EXPIRED = "expired"
    MISSING = "missing"
    ILLEGIBLE = "illegible"
    INCOMPLETE = "incomplete"
    OTHER = "other"

class ObservationStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(ObservationType), nullable=False)
    status = Column(Enum(ObservationStatus), default=ObservationStatus.OPEN)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(DateTime(timezone=True))
    
    # Foreign Keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    
    # Resolution info
    resolution_date = Column(DateTime(timezone=True))
    resolution_comments = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="observations")
    creator = relationship("User", foreign_keys=[created_by])
    resolver = relationship("User", foreign_keys=[resolved_by])