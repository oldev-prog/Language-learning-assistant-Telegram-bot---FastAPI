import httpx
import pytest_asyncio
from app.data.models import User, Word
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.data.config import settings

engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    poolclass=NullPool,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture(scope='function')
async def test_session():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Word))
        await session.execute(delete(User))
        yield session

@pytest_asyncio.fixture(scope='function')
async def httpx_client():
    async with httpx.AsyncClient() as client:
        yield client

