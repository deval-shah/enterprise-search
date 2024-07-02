from sqlalchemy.orm import Session
from llamasearch.api.db.models import Chat, Message, User, QueryLog
from llamasearch.api.schemas.chat import ChatCreate, ChatResponse, ChatListResponse, MessageCreate, MessageResponse, MessageType
from llamasearch.logger import logger
from datetime import datetime
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

class ChatService:
    @staticmethod
    async def create_chat(db: Session, uid: str, chat_create: ChatCreate) -> ChatResponse:
        try:
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                raise ValueError("User not found")

            chat = Chat(user_id=user.id)
            db.add(chat)
            db.flush()  # This assigns an ID to the chat

            for idx, message in enumerate(chat_create.messages):
                db_message = Message(
                    chat_id=chat.id,
                    content=message.content,
                    message_type=MessageType[message.message_type.upper()],
                    sequence_number=idx
                )
                db.add(db_message)

            db.commit()
            db.refresh(chat)
            return ChatResponse.from_orm(chat)
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while creating the chat")
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    @staticmethod
    async def get_user_chats(db: Session, uid: str, skip: int = 0, limit: int = 10) -> List[ChatListResponse]:
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            raise ValueError("User not found")

        chats = db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()
        chat_responses = []
        for chat in chats:
            last_message = max(chat.messages, key=lambda m: m.sequence_number) if chat.messages else None
            chat_responses.append(ChatListResponse(
                id=chat.id,
                user_id=chat.user_id,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
                last_message=MessageResponse.from_orm(last_message) if last_message else None
            ))
        return chat_responses

    @staticmethod
    async def get_chat(db: Session, chat_id: str) -> ChatResponse:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError("Chat not found")
        return ChatResponse.from_orm(chat)

    @staticmethod
    async def add_message_to_chat(db: Session, chat_id: str, message_create: MessageCreate) -> MessageResponse:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError("Chat not found")

        try:
            db_message_type = MessageType[message_create.message_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid message type: {message_create.message_type}")

        sequence_number = len(chat.messages)
        db_message = Message(
            chat_id=chat_id,
            content=message_create.content,
            message_type=db_message_type,
            sequence_number=sequence_number
        )
        db.add(db_message)
        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_message)
        return MessageResponse.from_orm(db_message)

    @staticmethod
    async def get_recent_queries(db: Session, firebase_uid: str, limit: int = 10):
        try:
            return db.query(QueryLog).filter(QueryLog.firebase_uid == firebase_uid).order_by(QueryLog.timestamp.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error retrieving recent queries for user {firebase_uid}: {str(e)}")
            return []