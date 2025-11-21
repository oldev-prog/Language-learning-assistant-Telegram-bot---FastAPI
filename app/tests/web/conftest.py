import pytest
from httpx import AsyncClient, ASGITransport
from respx import Router
from unittest.mock import AsyncMock, patch
from fastapi.responses import JSONResponse
from app.main import app
from app.data.models import User
from app.bot.telegram_bot import TelegramBot

pytestmark = pytest.mark.web


@pytest.fixture
async def mock_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client

@pytest.fixture
async def mock_bot(monkeypatch, test_session):
    bot = TelegramBot(services=None)
    bot.services = AsyncMock()
    bot.services.user_crud = AsyncMock()
    bot.services.user_crud.check_exists.return_value = None  # будет переопределён

    for method in ["save_word", "delete_word", "send_words_list", "spaced_review",
                   "explain_word", "send_pronunciation", "send_youtube_video", "send_message"]:
        monkeypatch.setattr(bot, method, AsyncMock())

    return bot

@pytest.fixture
async def mock_user_crud(monkeypatch):

    user_crud = AsyncMock()

    user_crud.check_exists.return_value = {
        "chat_id": 999,
        "state": "",
        "native_lang": "ru",
        "lang_code": "en",
        "last_word": "",
        "last_translate": "",
        "review_index": 0,
    }

    return user_crud


@pytest.fixture
async def mock_start_funcs(monkeypatch):
    mocks = {
        "choice_native_lang": AsyncMock(),
        "choice_learning_lang": AsyncMock(),
        "change_lang": AsyncMock(),
        "update_state_to_await": AsyncMock(),
        "raise_invalid_command": AsyncMock(),
    }

    for name in ["choice_native_lang", "choice_learning_lang", "change_lang"]:
        monkeypatch.setattr(f"app.telegram_utils.start_funcs.{name}", mocks[name])

    for name in ["update_state_to_await", "raise_invalid_command"]:
        monkeypatch.setattr(f"app.telegram_utils.utils.{name}", mocks[name])

    return mocks

@pytest.fixture
async def fake_user(test_session):
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

    return user