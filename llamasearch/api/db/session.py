from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from llamasearch.api.core.config import settings
from sqlalchemy import MetaData

class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

class AsyncDatabaseSession:
    def __init__(self):
        self._engine = None
        self._session_factory = None

    def init(self, db_url: str):
        self._engine = create_async_engine(db_url, echo=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def close(self):
        if self._engine:
            await self._engine.dispose()

    @property
    def session_factory(self):
        return self._session_factory

    @property
    def engine(self):
        return self._engine

sessionmanager = AsyncDatabaseSession()

async def get_db():
    async with sessionmanager.session_factory() as session:
        yield session

async def init_db():
    sessionmanager.init(settings.DATABASE_URL)
    async with sessionmanager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    await sessionmanager.close()
