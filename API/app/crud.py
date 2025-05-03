from sqlalchemy.orm import Session
from . import tables, schemas
from passlib.context import CryptContext
from fastapi import HTTPException
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, email: str):
    return db.query(tables.User).filter(tables.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Check if user with this email already exists
    existing_user = db.query(tables.User).filter(tables.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    
    # Create the base user
    db_user = tables.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user
