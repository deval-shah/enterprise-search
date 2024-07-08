# app/services/session.py
from llamasearch.api.db.models import Session, User
from llamasearch.api.services.user import user_to_pydantic
from llamasearch.logger import logger
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql import func
import uuid
from typing import Optional

class SessionService:
    def __init__(self):
        self.redis_client = None

    def init_redis(self, redis_client):
        self.redis_client = redis_client

    async def get_user_session(self, db: DBSession, user_id: str) -> Optional[Session]:
        if self.redis_client:
            # Check if user has an active session in Redis
            session_key = self.redis_client.scan_iter(match=f"session:*")
            for key in session_key:
                if self.redis_client.get(key).decode() == str(user_id):
                    session_id = key.decode().split(':')[1]
                    return db.query(Session).filter(Session.id == session_id, Session.ended_at.is_(None)).first()
        
        # If not found in Redis or Redis is not used, check the database
        return db.query(Session).filter(Session.user_id == user_id, Session.ended_at.is_(None)).order_by(Session.created_at.desc()).first()

    async def create_session(self, db: DBSession, user_id: str) -> str:
        # End any existing session for this user
        await self.end_all_sessions(db, user_id)
        session_id = str(uuid.uuid4())
        db_session = Session(id=session_id, user_id=user_id)
        db.add(db_session)
        db.commit()
        logger.info(f"Setting session in Redis: {session_id}")
        self.redis_client.setex(f"session:{session_id}", 3600, str(user_id))  # 1 hour expiry
        return session_id

    async def validate_session(self, db: DBSession, session_id: str) -> Optional[User]:
        if self.redis_client:
            user_id = self.redis_client.get(f"session:{session_id}")
            if not user_id:
                return None
            user = db.query(User).filter(User.id == user_id.decode()).first()
        else:
            db_session = db.query(Session).filter(Session.id == session_id, Session.ended_at.is_(None)).first()
            if not db_session:
                return None
            user = db.query(User).filter(User.id == db_session.user_id).first()
        
        if user:
            # Refresh the session
            if self.redis_client:
                self.redis_client.expire(f"session:{session_id}", 3600)  # Refresh expiry
            else:
                db_session = db.query(Session).filter(Session.id == session_id).first()
                if db_session:
                    db_session.last_activity = func.now()
                    db.commit()
            logger.info(f"Session validated and refreshed: {session_id}")
            return user_to_pydantic(user)
        return None

    async def end_session(self, db: DBSession, session_id: str):
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")
        db_session = db.query(Session).filter(Session.id == session_id).first()
        if db_session:
            db_session.ended_at = func.now()
            db.commit()

    async def end_all_sessions(self, db: DBSession, user_id: str):
        db_sessions = db.query(Session).filter(Session.user_id == user_id, Session.ended_at.is_(None)).all()
        for session in db_sessions:
            session.ended_at = func.now()
            if self.redis_client:
                self.redis_client.delete(f"session:{session.id}")
        db.commit()

session_service = SessionService()
