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


@pytest.fixture
def sample_words():

    return [
        Word(word="hello", translate="привет"),
        Word(word="world", translate="мир"),
        Word(word="", translate="пусто"),
    ]


@pytest.fixture
def pdf_instance(mock_httpx_client, mock_send_message):

    return PDF(
        client=mock_httpx_client,
        send_msg_func=mock_send_message,
        style="Normal",
        font_name="Helvetica",
        font_size=10,
    )


@pytest.fixture
def send_voice_url():
    url = "https://api.telegram.org/botTOKEN/sendVoice"
    return url
