from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class EmailRequest(BaseModel):
    email: EmailStr

# Update user-related schemas with additional fields
class UserBase(BaseModel):
    email: EmailStr
    role: str  # Added role to base

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime  # Add created_at field
    
    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic v2

class Token(BaseModel):
    access_token: str
    email: str
    role: str
    user_id: int

class TokenData(BaseModel):
    email: Optional[str] = None