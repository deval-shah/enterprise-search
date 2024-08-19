# app/schemas/user.py

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None

class UserCreate(UserBase):
    firebase_uid: str
    tenant_id: Optional[str] = None

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: int
    firebase_uid: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

UserInDB = User
