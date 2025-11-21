import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from app.bot.youtube_parsing.key_managers import KeyManager, ProxyManager
from googleapiclient.errors import HttpError
from httpx import HTTPError, RequestError
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Set
from app.bot.youtube_parsing.youtube_parsing import YouTubeParsing


@pytest.fixture
async def some_method():
    return 'success'


class MockService:
    def test_execute(self):
        return 'success'

    def test_exception(self):
        resp = Mock()
        resp.status = 403
        content = b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        raise HttpError(resp, content)

@pytest.fixture
def service_factory():
    def factory(key):
        service = MockService()
        service.key = key
        return service
    return factory

@pytest.fixture
def http_error():
    return HTTPError("Test HTTP error")

@pytest.fixture
def key_manager(service_factory):
    keys = ["key1", "key2", "key3"]
    return KeyManager(keys, service_factory)

@pytest.fixture
def proxy_manager():
    proxies = ["http://proxy1", "http://proxy2", "http://proxy3"]
    return ProxyManager(proxies)




@pytest.fixture
def seen_ids() -> Set[str]:
    return set()


@pytest.fixture
def mock_key_manager():
    with patch('app.bot.youtube_parsing.youtube_parsing.KeyManager') as mock:
        manager = mock.return_value
        manager.execute = AsyncMock()
        yield manager


@pytest.fixture
def mock_proxy_manager():
    with patch('app.bot.youtube_parsing.youtube_parsing.ProxyManager') as mock:
        manager = mock.return_value
        manager.execute = AsyncMock()
        yield manager


@pytest.fixture
def mock_ytt_api():
    with patch('app.bot.youtube_parsing.youtube_parsing.proxy_factory') as mock_factory:
        api = MagicMock()
        api.list.return_value.find_generated_transcript = MagicMock(return_value=None)
        api.list.return_value.find_manually_created_transcript = MagicMock(return_value=None)
        mock_factory.return_value = api
        yield api


@pytest.fixture
def youtube_parsing(mock_key_manager, mock_proxy_manager, mock_ytt_api):
    return YouTubeParsing()