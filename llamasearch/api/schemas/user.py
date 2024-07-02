# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None

class UserCreate(UserBase):
    firebase_uid: str

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: int
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

UserInDB = User
