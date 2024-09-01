# app/db/models.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from llamasearch.api.db.session import Base
from llamasearch.api.schemas.chat import MessageType

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    tenant_id = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    saved_state = Column(Text)

    chats = relationship("Chat", back_populates="user")
    sessions = relationship("Session", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
    }

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, ForeignKey("users.firebase_uid"), index=True, nullable=False)
    query = Column(Text, nullable=False)
    context = Column(JSON)
    response = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.firebase_uid"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", order_by="Message.sequence_number")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    chat_id = Column(String, ForeignKey("chats.id"), index=True, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    sequence_number = Column(Integer, nullable=False)

    chat = relationship("Chat", back_populates="messages")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.firebase_uid"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", back_populates="sessions")

class UserBase(BaseModel):
    email: str
    display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class UserCreate(UserBase):
    firebase_uid: str

class UserUpdate(UserBase):
    pass

class UserInDB(UserBase):
    id: int
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

User.sessions = relationship("Session", back_populates="user")