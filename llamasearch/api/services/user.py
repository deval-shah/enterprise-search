# app/services/user.py
from sqlalchemy.orm import Session
from llamasearch.api.db.models import User as UserModel
from llamasearch.api.schemas.user import UserCreate, UserUpdate, User
from llamasearch.logger import logger

def user_to_pydantic(db_user: UserModel) -> User:
    return User(
        id=db_user.id,
        firebase_uid=db_user.firebase_uid,
        email=db_user.email,
        display_name=db_user.display_name,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

class UserService:
    @staticmethod
    async def create_or_get_user(db: Session, user_data: UserCreate) -> User:
        logger.info(f"Attempting to create or get user with firebase_uid: {user_data.firebase_uid}")
        user = db.query(UserModel).filter(UserModel.firebase_uid == user_data.firebase_uid).first()
        logger.info(f"Existing user found: {user}")
        if not user:
            logger.info("User not found, creating new user")
            user = UserModel(**user_data.dict())
            db.add(user)
            db.commit()
            db.refresh(user)
        return user_to_pydantic(user)

    @staticmethod
    async def update_user(db: Session, uid: str, user_data: UserCreate) -> User:
        user = db.query(UserModel).filter(UserModel.firebase_uid == uid).first()
        if not user:
            return None
        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user_to_pydantic(user)

    @staticmethod
    async def get_user_by_uid(db: Session, uid: str) -> User:
        user = db.query(UserModel).filter(UserModel.firebase_uid == uid).first()
        if not user:
            return None
        return user_to_pydantic(user)
