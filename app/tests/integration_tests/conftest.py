# test/integration/conftest.py
import pytest
import httpx
from unittest.mock import AsyncMock

from app.bot.telegram_bot import Services
from app.bot.telegram_bot import TelegramBot
from app.data.models import User


@pytest.fixture(scope='function')
async def httpx_client():
    async with httpx.AsyncClient(base_url='http://localhost:8080') as client:
        yield client

@pytest.fixture
def mock_send_message(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr('app.bot.telegram_bot.send_message', mock)
    return mock

@pytest.fixture
def services(test_session, httpx_client):
    return Services(
        db=test_session,
        client=httpx_client
    )

@pytest.fixture
def bot(services, monkeypatch):
    monkeypatch.setattr('asyncio.sleep', AsyncMock())

    return TelegramBot(services=services)

@pytest.fixture
async def fake_user_state(test_session):
    user = User(
        chat_id=1234,
        id=1234,
        last_word='',
        last_translate='',
        state='',
        native_lang='ru',
        lang_code='en',
        review_index=0
    )

    test_session.add(user)

    await test_session.commit()
    await test_session.refresh(user)

    return user
