# backend/app/api/v1/endpoints/observations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ....core.database import get_db
from ....models import observation as models
from ....schemas import observation as schemas
from ....core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.ObservationResponse)
def create_observation(
    observation: schemas.ObservationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new observation for a document"""
    db_observation = models.Observation(
        **observation.dict(),
        created_by=current_user.id
    )
    
    db.add(db_observation)
    db.commit()
    db.refresh(db_observation)
    
    return db_observation

@router.get("/document/{document_id}", response_model=List[schemas.ObservationResponse])
def get_document_observations(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all observations for a document"""
    observations = db.query(models.Observation).filter(
        models.Observation.document_id == document_id
    ).all()
    
    return observations

@router.get("/", response_model=List[schemas.ObservationResponse])
def get_observations(
    status: Optional[schemas.ObservationStatus] = Query(None),
    type: Optional[schemas.ObservationType] = Query(None),
    company_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get observations with filters"""
    query = db.query(models.Observation)
    
    if status:
        query = query.filter(models.Observation.status == status)
    
    if type:
        query = query.filter(models.Observation.type == type)
    
    # Filter by company if user is not admin
    if current_user.role != "admin" and current_user.company_id:
        query = query.join(models.Observation.document).filter(
            models.Document.company_id == current_user.company_id
        )
    elif company_id:
        query = query.join(models.Observation.document).filter(
            models.Document.company_id == company_id
        )
    
    observations = query.offset(skip).limit(limit).all()
    return observations

@router.patch("/{observation_id}", response_model=schemas.ObservationResponse)
def resolve_observation(
    observation_id: int,
    update_data: schemas.ObservationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Resolve or update an observation"""
    observation = db.query(models.Observation).filter(
        models.Observation.id == observation_id
    ).first()
    
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    # Update fields
    if update_data.status:
        observation.status = update_data.status
        if update_data.status == schemas.ObservationStatus.CLOSED:
            observation.resolved_by = current_user.id
            observation.resolution_date = datetime.now()
    
    if update_data.resolution_comments:
        observation.resolution_comments = update_data.resolution_comments
    
    db.commit()
    db.refresh(observation)
    
    return observation

@router.delete("/{observation_id}")
def delete_observation(
    observation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an observation (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    observation = db.query(models.Observation).filter(
        models.Observation.id == observation_id
    ).first()
    
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    db.delete(observation)
    db.commit()
    
    return {"message": "Observation deleted successfully"}
