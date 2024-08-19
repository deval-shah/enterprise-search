# app/services/session.py
from llamasearch.api.db.models import Session, User
from llamasearch.api.services.user import user_to_pydantic, UserService
from llamasearch.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy.sql import func
from sqlalchemy import select
import uuid
from typing import Optional

class SessionService:
    def __init__(self):
        self.redis_client = None

    def init_redis(self, redis_client):
        self.redis_client = redis_client

    async def create_session(self, db: DBSession, user_id: int) -> str:
        session_id = str(uuid.uuid4())
        session = Session(id=session_id, user_id=user_id)
        db.add(session)
        await db.commit()
        if self.redis_client:
            self.redis_client.setex(f"session:{session_id}", 3600, str(user_id))  # 1 hour expiry
        return session_id

    async def get_user_session(self, db: DBSession, session_id: str) -> Optional[User]:
        session = await db.execute(select(Session).filter(Session.id == session_id, Session.ended_at.is_(None)))
        session = session.scalar_one_or_none()
        if session:
            user = await db.execute(select(User).filter(User.id == session.user_id))
            user = user.scalar_one_or_none()
            if user:
                return user_to_pydantic(user)
        return None

    async def validate_session(self, db: DBSession, session_id: str) -> Optional[User]:
        if self.redis_client:
            user_id = self.redis_client.get(f"session:{session_id}")
            if not user_id:
                return None
            user = await db.execute(select(User).filter(User.id == user_id.decode()))
            user = user.scalar_one_or_none()
            #user = db.query(User).filter(User.id == user_id.decode()).first()
        else:
            result = await db.execute(select(Session).filter(Session.id == session_id, Session.ended_at.is_(None)))
            db_session = result.scalar_one_or_none()
            if not db_session:
                return None
            result = await db.execute(select(User).filter(User.id == db_session.user_id))
            user = result.scalar_one_or_none()
        
        if user:
            if not self.redis_client:
                db_session.last_activity = func.now()
                await db.commit()
            logger.info(f"Session validated and refreshed: {session_id}")
            return user_to_pydantic(user)
        return None

    async def end_session(self, db: DBSession, session_id: str):
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")
        result = await db.execute(select(Session).filter(Session.id == session_id))
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.ended_at = func.now()
            await db.commit()

    async def end_all_sessions(self, db: DBSession, user_id: str):
        result = await db.execute(select(Session).filter(Session.user_id == user_id, Session.ended_at.is_(None)))
        db_sessions = result.scalars().all()
        for session in db_sessions:
            session.ended_at = func.now()
            if self.redis_client:
                self.redis_client.delete(f"session:{session.id}")
        await db.commit()

session_service = SessionService()
