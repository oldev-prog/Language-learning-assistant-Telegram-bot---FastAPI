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
def send_voice_url():
    url = "https://api.telegram.org/botTOKEN/sendVoice"
    return url


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
def pronunciation(mock_httpx_client, monkeypatch, send_voice_url):
    monkeypatch.setattr('app.bot.pronunciation.send_voice_url', send_voice_url)

    return Pronunciation(client=mock_httpx_client)

@pytest.fixture
def mock_gtts(monkeypatch):

    mock_factory = MagicMock()
    monkeypatch.setattr('app.bot.pronunciation.gTTS', mock_factory)

    return mock_factory

@pytest.fixture()
def mock_file_ops(monkeypatch):
    counter = 0

    def fake_tempfile(*args, **kwargs):
        nonlocal counter
        counter += 1
        name = f"/tmp/fake_voice_{counter}.mp3"
        mock_file = MagicMock()
        mock_file.name = name
        mock_file.close = MagicMock()
        return mock_file

    monkeypatch.setattr('tempfile.NamedTemporaryFile', fake_tempfile)

    monkeypatch.setattr('builtins.open', mock_open())

    mock_aio_file = AsyncMock()
    mock_aio_file.read = AsyncMock(return_value=b"fake audio data")
    mock_aio_file.__aenter__ = AsyncMock(return_value=mock_aio_file)
    mock_aio_file.__aexit__ = AsyncMock(return_value=None)

    def fake_aiofiles_open(path, mode):
        return mock_aio_file

    monkeypatch.setattr('aiofiles.open', fake_aiofiles_open)

    removed_files = []

    def fake_remove(path):
        removed_files.append(path)

    monkeypatch.setattr('os.remove', fake_remove)

    yield removed_files