# backend/app/api/v1/endpoints/documents.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import hashlib
import os
from ....core.database import get_db
from ....models import document as models
from ....schemas import document as schemas
from ....core.security import get_current_user
from ....services.document_validator import DocumentValidator

router = APIRouter()

@router.post("/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    type: schemas.DocumentType = Form(...),
    worker_id: int = Form(...),
    company_id: int = Form(...),
    issue_date: Optional[str] = Form(None),
    expiry_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload a new document with automatic validation"""
    
    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.pdf', '.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    # Save file
    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Create upload directory if not exists
    upload_dir = f"uploads/{company_id}/{worker_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file with unique name
    file_path = f"{upload_dir}/{datetime.now().timestamp()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Validate document (OCR, format, etc.)
    validator = DocumentValidator()
    validation_result = await validator.validate(file_path, type)
    
    # Create database record
    db_document = models.Document(
        name=name,
        type=type,
        file_path=file_path,
        file_hash=file_hash,
        worker_id=worker_id,
        company_id=company_id,
        uploaded_by=current_user.id,
        status=schemas.DocumentStatus.PENDING if not validation_result.is_valid 
               else schemas.DocumentStatus.APPROVED,
        issue_date=datetime.fromisoformat(issue_date) if issue_date else None,
        expiry_date=datetime.fromisoformat(expiry_date) if expiry_date else None
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Create observations if validation failed
    if not validation_result.is_valid:
        for error in validation_result.errors:
            # Create observation logic here
            pass
    
    return db_document

@router.get("/worker/{worker_id}", response_model=List[schemas.DocumentResponse])
def get_worker_documents(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all documents for a specific worker"""
    documents = db.query(models.Document).filter(
        models.Document.worker_id == worker_id
    ).all()
    return documents

@router.get("/expiring", response_model=List[schemas.DocumentResponse])
def get_expiring_documents(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get documents expiring in the next N days"""
    expiry_date = datetime.now() + timedelta(days=days)
    
    documents = db.query(models.Document).filter(
        models.Document.expiry_date <= expiry_date,
        models.Document.expiry_date >= datetime.now(),
        models.Document.status != schemas.DocumentStatus.EXPIRED
    ).all()
    
    return documents

@router.patch("/{document_id}", response_model=schemas.DocumentResponse)
def update_document_status(
    document_id: int,
    update_data: schemas.DocumentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update document status (approve/observe)"""
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if update_data.status:
        document.status = update_data.status
        document.reviewed_by = current_user.id
        document.review_date = datetime.now()
    
    if update_data.review_comments:
        document.review_comments = update_data.review_comments
    
    db.commit()
    db.refresh(document)
    
    return document
