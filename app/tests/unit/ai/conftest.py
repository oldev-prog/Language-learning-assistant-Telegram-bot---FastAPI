import pytest, pytest_asyncio
import httpx
import os
from unittest.mock import patch
from app.bot.ai.open_ai import AIClient
import json
from app.data.models import User
from unittest.mock import AsyncMock, MagicMock, mock_open
from app.data.models import Word
from app.bot.pdf import PDF
from app.bot.pronunciation import Pronunciation

@pytest_asyncio.fixture(scope='session')
def fake_client():
    async def handler(request: httpx.Request):
        assert request.method == 'POST'
        assert str(request.url) == 'https://api.aitunnel.ru/v1/chat/completions'
        assert request.headers['Content-Type'] == 'application/json'
        assert request.headers['Authorization'] == 'Bearer fake-key-123'

        payload = await request.aread()
        body = json.loads(payload)

        assert body['model'] == 'gpt-4.1-nano'
        assert len(body['messages']) == 1
        assert body['messages'][0]['role'] == 'user'
        assert ('определи язык слова "hello" и напиши только двухбуквенный код языка '
                 '(например: en, ru, fr). если слово "hello" написано на языке "russian", '
                 'переведи его на язык "en". если слово написано на языке "en", переведи его '
                 'на язык "russian". дай объяснение, синонимы, примеры и советы по '
                 'запоминанию. синонимы приводи из языка en и укажи разницу. все объяснения '
                 'давай на языке russian. общий ответ должен быть не длиннее 300 символов. '
                 'ответ строго в формате json') in body['messages'][0]['content'].lower()

        fake_openai = {
            'choices': [
                {
                    'message': {
                        'content': {'explanation_synonyms': 'привет, здорова, здравствуйте'}
                    }
                }
            ]
        }

        return httpx.Response(200, json=fake_openai)

    return handler

@pytest_asyncio.fixture
async def mock_client(fake_client):
    transport = httpx.MockTransport(fake_client)
    async with httpx.AsyncClient(transport=transport) as client:
        yield client

@pytest.fixture
def ai_client(mock_client, monkeypatch):
    monkeypatch.setenv('OPENAI_KEY', 'fake-key-123')
    return AIClient(client=mock_client)

@pytest.fixture
def user_state_ru():
    state = type('User', (), {})()
    state.native_lang = 'russian'
    state.lang_code = 'en'
    state.last_word = None
    state.last_translate = None

    return state


@pytest.fixture
def mock_httpx_client():

    client = AsyncMock()

    client.post.return_value.status_code = 200
    client.post.return_value.json.return_value = {"ok": True, "result": {}}
    client.post.return_value.text = lambda: "{}"

    return client


@pytest.fixture
def mock_send_message():

    return AsyncMock()