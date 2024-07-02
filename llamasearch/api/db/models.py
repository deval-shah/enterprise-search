# app/db/models.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional
import uuid
from pydantic import BaseModel
from datetime import datetime
from llamasearch.api.db.session import Base
from llamasearch.api.schemas.chat import MessageType

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    chats = relationship("Chat", back_populates="user")

class UserBase(BaseModel):
    email: str
    display_name: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

class UserCreate(UserBase):
    firebase_uid: str

class UserUpdate(UserBase):
    pass

class UserInDB(UserBase):
    id: int
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, index=True)
    query = Column(Text)
    context = Column(JSON)
    response = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(timezone=True), onupdate=func.now(timezone=True), nullable=False)

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.firebase_uid"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(timezone=True), onupdate=func.now(timezone=True), nullable=False)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", order_by="Message.sequence_number")
    
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: generate_uuid())
    chat_id = Column(String, ForeignKey("chats.id"), index=True)
    content = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    sequence_number = Column(Integer, nullable=False)

    chat = relationship("Chat", back_populates="messages")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: generate_uuid())
    user_id = Column(String, ForeignKey("users.firebase_uid"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(timezone=True))
    ended_at = Column(DateTime(timezone=True), server_default=func.now(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(timezone=True), onupdate=func.now(timezone=True))
    
    user = relationship("User", back_populates="sessions")

User.sessions = relationship("Session", back_populates="user")