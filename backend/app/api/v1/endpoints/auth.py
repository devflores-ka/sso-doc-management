# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from ....core.database import get_db
from ....core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)
from ....models import user as user_models
from ....schemas import user as schemas

router = APIRouter()

@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint"""
    user = db.query(user_models.User).filter(
        user_models.User.username == form_data.username
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_id": user.company_id
        }
    }

@router.post("/register", response_model=schemas.UserResponse)
def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Register a new user (admin or company RRHH only)"""
    
    # Check permissions
    if current_user.role not in ["admin", "rrhh"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if user already exists
    existing_user = db.query(user_models.User).filter(
        (user_models.User.username == user_data.username) |
        (user_models.User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="User already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    db_user = user_models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        company_id=user_data.company_id if current_user.role == "admin" else current_user.company_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
def update_current_user(
    update_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update current user profile"""
    
    # Update allowed fields
    if update_data.email:
        # Check if email is already taken
        existing = db.query(user_models.User).filter(
            user_models.User.email == update_data.email,
            user_models.User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        current_user.email = update_data.email
    
    if update_data.full_name:
        current_user.full_name = update_data.full_name
    
    if update_data.password:
        current_user.hashed_password = get_password_hash(update_data.password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/users", response_model=List[schemas.UserResponse])
def get_users(
    company_id: Optional[int] = None,
    role: Optional[schemas.UserRole] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of users (admin or RRHH only)"""
    
    if current_user.role not in ["admin", "rrhh"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(user_models.User)
    
    # Filter by company if not admin
    if current_user.role != "admin":
        query = query.filter(user_models.User.company_id == current_user.company_id)
    elif company_id:
        query = query.filter(user_models.User.company_id == company_id)
    
    if role:
        query = query.filter(user_models.User.role == role)
    
    if is_active is not None:
        query = query.filter(user_models.User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Activate/deactivate user (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user = db.query(user_models.User).filter(
        user_models.User.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    db.commit()
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}

@router.post("/refresh-token", response_model=schemas.TokenResponse)
def refresh_token(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    
    # Create new access token
    access_token = create_access_token(
        data={
            "sub": current_user.username, 
            "user_id": current_user.id, 
            "role": current_user.role.value
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "company_id": current_user.company_id
        }
    }
