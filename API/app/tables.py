from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Date
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)