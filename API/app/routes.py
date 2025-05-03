from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File, Form, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import random
from passlib.context import CryptContext
import yagmail

from .config import settings
from . import schemas, crud, tables
from .database import get_db

router = APIRouter(tags=["routes"])

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="routes/login")

# In-memory storage for verification codes (use database in production)
verification_codes: Dict[str, Dict[str, Any]] = {}

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

@router.post("/current-user", response_model=schemas.User)
async def current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> tables.User:
    user = await get_current_user(token, db)
    return user

async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
) -> tables.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        print("payload: ", payload)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user(db, email=email)
    print("user: ",user)
    if user is None:
        raise credentials_exception
    return user

def generate_verification_code(email: str) -> str:
    code = f"{random.randint(100000, 999999)}"
    expiration = datetime.now() + timedelta(minutes=10)
    verification_codes[email] = {
        "code": code,
        "expires_at": expiration,
        "verified": False
    }
    return code

async def verify_code_dependency(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    email = user_data.email
    record = verification_codes.get(email)
    if not record or not record["verified"]:
        raise HTTPException(status_code=400, detail="Email not verified")
    return True

@router.post("/send-verification")
async def send_verification(
    request: schemas.EmailRequest,
    db: Session = Depends(get_db)
):
    if crud.get_user(db, email=request.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    code = generate_verification_code(request.email)
    yag = yagmail.SMTP(user="your_email@gmail.com", password="your_app_password")
    subject = "Verification Code - Skin Cancer Detection App"
    body = f"""
        Dear User,

        Your verification code for Skin Cancer Detection App is: {code}

        Please enter this code to verify your email address.

        Regards,
        Skin Cancer Detection Team
    """
    try:
        yag.send(
            to=request.email,
            subject=subject,
            contents=body
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send verification email: {e}")
    print(f"Verification code for {request.email}: {code}")
    return {"message": "Verification code sent"}

@router.post("/verify-code")
async def verify_code(
    data: schemas.VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    record = verification_codes.get(data.email)
    
    if not record or datetime.now() > record["expires_at"]:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    if data.code != record["code"]:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    verification_codes[data.email]["verified"] = True
    return {"verified": True}

@router.post("/register", response_model=schemas.User)
async def register(
    user_data: schemas.UserCreate,
    verified: bool = Depends(verify_code_dependency),
    db: Session = Depends(get_db)
):
    if user_data.role not in ["doctor", "patient"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    try:
        return crud.create_user(db=db, user=user_data)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
 
@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    
    user = crud.get_user(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "email": user.email,
        "role": user.role,
        "user_id": user.id
    }