# app/services/user.py
from sqlalchemy.orm import Session
from llamasearch.api.db.models import User as UserModel
from llamasearch.api.schemas.user import UserCreate, UserUpdate, User

class UserService:
    @staticmethod
    async def create_or_get_user(db: Session, user_data: UserCreate) -> User:
        user = db.query(UserModel).filter(UserModel.firebase_uid == user_data.firebase_uid).first()
        if not user:
            user = UserModel(**user_data.dict())
            db.add(user)
            db.commit()
            db.refresh(user)
        return User.from_orm(user)

    @staticmethod
    async def update_user(db: Session, firebase_uid: str, user_update: UserUpdate) -> User:
        user = db.query(UserModel).filter(UserModel.firebase_uid == firebase_uid).first()
        if not user:
            raise ValueError("User not found")
        
        update_data = user_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return User.from_orm(user)

    @staticmethod
    async def get_user_by_uid(db: Session, uid: str) -> User:
        user = db.query(UserModel).filter(UserModel.firebase_uid == uid).first()
        return User.from_orm(user) if user else None
