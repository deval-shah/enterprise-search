# app/schemas/chat.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class FileUploadResponse(BaseModel):
    filename: str
    status: str

class QueryResponse(BaseModel):
    response: str = Field(..., description="The response to the query")
    context: str = Field(..., description="Context information for the response")
    query: str = Field(..., description="The original query")
    file_upload: List[str] = Field(default_factory=list, description="List of uploaded file responses")

class UploadFilesResponse(BaseModel):
    file_upload: List[FileUploadResponse] = Field(..., description="List of uploaded file responses")

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query string")
    files: Optional[List[str]] = Field(None, description="List of file names to be uploaded")

class MessageType(str, Enum):
    USER = "user"
    SYSTEM = "system"

class MessageCreate(BaseModel):
    content: str
    message_type: MessageType

class MessageResponse(BaseModel):
    id: str
    chat_id: str
    content: str
    timestamp: datetime
    message_type: MessageType
    sequence_number: int

    class Config:
        orm_mode = True

class ChatCreate(BaseModel):
    messages: List[MessageCreate]

class ChatResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        orm_mode = True

class ChatListResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_message: MessageResponse

    class Config:
        orm_mode = True


