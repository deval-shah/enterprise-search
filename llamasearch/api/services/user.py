# app/services/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from llamasearch.api.db.models import User as UserModel
from llamasearch.api.schemas.user import UserCreate, UserUpdate, User
from llamasearch.logger import logger
from sqlalchemy import select
import uuid

def user_to_pydantic(db_user: UserModel) -> User:
    user_dict = db_user.__dict__.copy()
    if 'tenant_id' not in user_dict or not user_dict['tenant_id']:
        user_dict['tenant_id'] = str(uuid.uuid4())
    return User(**user_dict)

class UserService:
    @staticmethod
    async def create_or_get_user(db: AsyncSession, user_data: UserCreate) -> User:
        try:
            async with db.begin():
                result = await db.execute(select(UserModel).filter(UserModel.firebase_uid == user_data.firebase_uid))
                logger.info(f"User service create or get user Result: {result}")
                user = result.scalar_one_or_none()
                if not user:
                    user_dict = user_data.dict(exclude_unset=True)
                    if 'tenant_id' not in user_dict or not user_dict['tenant_id']:
                        user_dict['tenant_id'] = str(uuid.uuid4())
                    user = UserModel(**user_dict)
                    db.add(user)
                    await db.flush()
                    await db.refresh(user)
                else:
                    if not user.tenant_id:
                        user.tenant_id = str(uuid.uuid4())
                        await db.flush()
                        await db.refresh(user)
                return user_to_pydantic(user)
        except Exception as e:
            logger.error(f"Error in create_or_get_user: {str(e)}")
            raise
    @staticmethod
    async def update_user(db: AsyncSession, uid: str, user_data: UserCreate) -> User:
        result = await db.execute(select(UserModel).filter(UserModel.firebase_uid == uid))
        user = result.scalar_one_or_none()
        if not user:
            return None
        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user_to_pydantic(user)

    @staticmethod
    async def get_user_by_uid(db: AsyncSession, uid: str) -> User:
        result = await db.execute(select(UserModel).filter(UserModel.firebase_uid == uid))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return user_to_pydantic(user)
