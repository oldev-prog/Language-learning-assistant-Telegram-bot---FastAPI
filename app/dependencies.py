import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.data.db_init import async_session_factory
from fastapi import Depends
from typing import Annotated

async def get_session():
    async with async_session_factory() as session:
        yield session

session_dep = Annotated[AsyncSession, Depends(get_session)]

async def get_httpx_client():
    async with httpx.AsyncClient() as client:
        yield client

httpx_client_dep = Annotated[httpx.AsyncClient, Depends(get_httpx_client)]
