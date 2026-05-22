from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None

class UserCreate(UserBase):
    id: str  

class UserRead(UserBase):
    id: str

class AuthRequest(BaseModel):
    email: str
    password: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
