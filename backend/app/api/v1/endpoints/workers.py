# backend/app/api/v1/endpoints/workers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ....core.database import get_db
from ....models import worker as worker_models
from ....models import document as doc_models
from ....schemas import worker as schemas
from ....core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.WorkerResponse)
def create_worker(
    worker: schemas.WorkerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new worker"""
    
    # Check if worker already exists
    existing = db.query(worker_models.Worker).filter(
        worker_models.Worker.run == worker.run
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Worker already exists")
    
    db_worker = worker_models.Worker(**worker.dict())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    
    return db_worker

@router.get("/", response_model=List[schemas.WorkerResponse])
def get_workers(
    company_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(True),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of workers with filters"""
    query = db.query(worker_models.Worker)
    
    if company_id:
        query = query.filter(worker_models.Worker.company_id == company_id)
    
    if is_active is not None:
        query = query.filter(worker_models.Worker.is_active == is_active)
    
    workers = query.offset(skip).limit(limit).all()
    
    # Add document count and compliance status
    for worker in workers:
        worker.documents_count = db.query(func.count(doc_models.Document.id)).filter(
            doc_models.Document.worker_id == worker.id
        ).scalar()
        
        # Calculate compliance status
        approved_docs = db.query(func.count(doc_models.Document.id)).filter(
            doc_models.Document.worker_id == worker.id,
            doc_models.Document.status == "approved"
        ).scalar()
        
        if worker.documents_count == 0:
            worker.compliance_status = "no_documents"
        elif approved_docs == worker.documents_count:
            worker.compliance_status = "compliant"
        else:
            worker.compliance_status = "non_compliant"
    
    return workers

@router.get("/{worker_id}", response_model=schemas.WorkerWithDocuments)
def get_worker_detail(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get worker details with all documents"""
    worker = db.query(worker_models.Worker).filter(
        worker_models.Worker.id == worker_id
    ).first()
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Get documents
    documents = db.query(doc_models.Document).filter(
        doc_models.Document.worker_id == worker_id
    ).all()
    
    worker.documents = documents
    
    return worker
