# backend/app/api/v1/endpoints/companies.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ....core.database import get_db
from ....models import company as company_models
from ....models import worker as worker_models
from ....models import document as doc_models
from ....schemas import company as schemas
from ....core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.CompanyResponse)
def create_company(
    company: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new company"""
    
    # Only admin can create companies
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if company already exists
    existing = db.query(company_models.Company).filter(
        company_models.Company.rut == company.rut
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")
    
    db_company = company_models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return db_company

@router.get("/", response_model=List[schemas.CompanyResponse])
def get_companies(
    is_active: Optional[bool] = Query(True),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of companies with filters"""
    query = db.query(company_models.Company)
    
    # Filter by company if user is not admin
    if current_user.role != "admin" and current_user.company_id:
        query = query.filter(company_models.Company.id == current_user.company_id)
    
    if is_active is not None:
        query = query.filter(company_models.Company.is_active == is_active)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (company_models.Company.name.ilike(search_filter)) |
            (company_models.Company.business_name.ilike(search_filter)) |
            (company_models.Company.rut.ilike(search_filter))
        )
    
    companies = query.offset(skip).limit(limit).all()
    
    # Add statistics
    for company in companies:
        company.workers_count = db.query(func.count(worker_models.Worker.id)).filter(
            worker_models.Worker.company_id == company.id
        ).scalar()
        
        company.documents_count = db.query(func.count(doc_models.Document.id)).filter(
            doc_models.Document.company_id == company.id
        ).scalar()
        
        # Calculate compliance percentage
        approved_docs = db.query(func.count(doc_models.Document.id)).filter(
            doc_models.Document.company_id == company.id,
            doc_models.Document.status == "approved"
        ).scalar()
        
        company.compliance_percentage = (
            (approved_docs / company.documents_count * 100) 
            if company.documents_count > 0 else 0
        )
    
    return companies

@router.get("/{company_id}", response_model=schemas.CompanyWithDetails)
def get_company_detail(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get company details with workers and statistics"""
    
    # Check permissions
    if (current_user.role != "admin" and 
        current_user.company_id != company_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    company = db.query(company_models.Company).filter(
        company_models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get workers with their document status
    workers = db.query(worker_models.Worker).filter(
        worker_models.Worker.company_id == company_id
    ).all()
    
    company.workers = workers
    
    return company

@router.put("/{company_id}", response_model=schemas.CompanyResponse)
def update_company(
    company_id: int,
    update_data: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update company information"""
    
    # Check permissions
    if (current_user.role not in ["admin", "rrhh"] and 
        current_user.company_id != company_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    company = db.query(company_models.Company).filter(
        company_models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    
    return company

@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Deactivate a company (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    company = db.query(company_models.Company).filter(
        company_models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Soft delete
    company.is_active = False
    db.commit()
    
    return {"message": "Company deactivated successfully"}

@router.get("/{company_id}/compliance-report")
def get_company_compliance_report(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed compliance report for a company"""
    
    # Check permissions
    if (current_user.role != "admin" and 
        current_user.company_id != company_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get company statistics
    total_workers = db.query(func.count(worker_models.Worker.id)).filter(
        worker_models.Worker.company_id == company_id,
        worker_models.Worker.is_active == True
    ).scalar()
    
    total_documents = db.query(func.count(doc_models.Document.id)).filter(
        doc_models.Document.company_id == company_id
    ).scalar()
    
    # Documents by status
    doc_stats = db.query(
        doc_models.Document.status,
        func.count(doc_models.Document.id)
    ).filter(
        doc_models.Document.company_id == company_id
    ).group_by(doc_models.Document.status).all()
    
    # Document types compliance
    type_stats = db.query(
        doc_models.Document.type,
        func.count(doc_models.Document.id),
        func.count(func.nullif(doc_models.Document.status != "approved", True))
    ).filter(
        doc_models.Document.company_id == company_id
    ).group_by(doc_models.Document.type).all()
    
    # Expiring documents (next 30 days)
    from datetime import datetime, timedelta
    expiring_soon = db.query(func.count(doc_models.Document.id)).filter(
        doc_models.Document.company_id == company_id,
        doc_models.Document.expiry_date.between(
            datetime.now(),
            datetime.now() + timedelta(days=30)
        )
    ).scalar()
    
    return {
        "company_id": company_id,
        "total_workers": total_workers,
        "total_documents": total_documents,
        "documents_by_status": {status: count for status, count in doc_stats},
        "documents_by_type": [
            {
                "type": doc_type,
                "total": total,
                "approved": approved or 0,
                "compliance_rate": (approved or 0) / total * 100 if total > 0 else 0
            }
            for doc_type, total, approved in type_stats
        ],
        "expiring_soon": expiring_soon,
        "overall_compliance": (
            dict(doc_stats).get("approved", 0) / total_documents * 100
            if total_documents > 0 else 0
        )
    }
