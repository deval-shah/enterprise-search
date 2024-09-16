#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from llamasearch.api.db.models import Chat, Message, User, QueryLog
from llamasearch.api.schemas.chat import ChatCreate, ChatResponse, ChatListResponse, MessageCreate, MessageResponse, MessageType
from llamasearch.logger import logger
from datetime import datetime
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from pydantic import parse_obj_as
from sqlalchemy import select, desc

class ChatService:
    @staticmethod
    async def create_chat(db: DBSession, uid: str, chat_create: ChatCreate) -> ChatResponse:
        try:
            user = await db.query(User).filter(User.id == uid).first()
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")

            chat = Chat(user_id=user.id)
            db.add(chat)
            await db.flush()  # This assigns an ID to the chat

            for idx, message in enumerate(chat_create.messages):
                db_message = Message(
                    chat_id=chat.id,
                    content=message.content,
                    message_type=MessageType[message.message_type.upper()],
                    sequence_number=idx
                )
                db.add(db_message)

            await db.commit()
            await db.refresh(chat)
            return parse_obj_as(ChatResponse, chat.__dict__)
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Database error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while creating the chat")
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    @staticmethod
    async def get_user_chats(db: DBSession, uid: str, skip: int = 0, limit: int = 10) -> List[ChatListResponse]:
        result = await db.execute(select(User).filter(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        result = await db.execute(
            select(Chat)
            .filter(Chat.user_id == user.id)
            .order_by(desc(Chat.updated_at))
            .offset(skip)
            .limit(limit)
        )
        chats = result.scalars().all()
        chat_responses = []
        for chat in chats:
            result = await db.execute(
                select(Message)
                .filter(Message.chat_id == chat.id)
                .order_by(desc(Message.sequence_number))
                .limit(1)
            )
            last_message = result.scalar_one_or_none()
            chat_responses.append(ChatListResponse(
                id=chat.id,
                user_id=chat.user_id,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
                last_message=MessageResponse.from_orm(last_message) if last_message else None
            ))
        return chat_responses

    @staticmethod
    async def get_chat(db: DBSession, chat_id: str) -> ChatResponse:
        result = await db.execute(select(Chat).filter(Chat.id == chat_id))
        chat = result.scalar_one_or_none()
        if not chat:
            raise ValueError("Chat not found")
        return parse_obj_as(ChatResponse, chat.__dict__)

    @staticmethod
    async def add_message_to_chat(db: DBSession, chat_id: str, message_create: MessageCreate) -> MessageResponse:
        result = await db.execute(select(Chat).filter(Chat.id == chat_id))
        chat = result.scalar_one_or_none()
        if not chat:
            raise ValueError("Chat not found")

        try:
            db_message_type = MessageType[message_create.message_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid message type: {message_create.message_type}")

        result = await db.execute(
            select(func.count()).select_from(Message).filter(Message.chat_id == chat_id)
        )
        sequence_number = result.scalar_one()
        db_message = Message(
            chat_id=chat_id,
            content=message_create.content,
            message_type=db_message_type,
            sequence_number=sequence_number
        )
        db.add(db_message)
        chat.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_message)
        return parse_obj_as(MessageResponse, db_message.__dict__)

    @staticmethod
    async def get_recent_queries(db: DBSession, firebase_uid: str, limit: int = 10):
        try:
            result = await db.execute(
                select(QueryLog)
                .filter(QueryLog.firebase_uid == firebase_uid)
                .order_by(desc(QueryLog.timestamp))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving recent queries for user {firebase_uid}: {str(e)}")
            return []