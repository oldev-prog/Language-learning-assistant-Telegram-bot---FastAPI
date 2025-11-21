from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.data.config import settings
from app.data.class_base import Base

sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=True,
    pool_size=5,
    max_overflow=2,
)

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
    pool_size=5,
    max_overflow=2,
)

session_factory = sessionmaker(sync_engine, expire_on_commit=False)

async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)


async def db_setup():
    async with sync_engine.connect() as session:
        await session.run_sync(Base.metadata.create_all(sync_engine))

