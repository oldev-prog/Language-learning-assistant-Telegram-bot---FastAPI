import pytest
from unittest.mock import Mock, AsyncMock, call
from app.bot.youtube_parsing.key_managers import Key, KeyManager, ProxyManager
from httpx import RequestError

def test_key_initialization(service_factory):
    key = Key("api-key-123", service_factory)

    assert key.key == "api-key-123"
    assert key.service.key == "api-key-123"
    assert key.used_units == 0
    assert key.active is True


class TestKeyManager:

    def test_get_key_rotates_correctly(self, key_manager):
        key1 = key_manager.get_key()
        key2 = key_manager.get_key()
        key3 = key_manager.get_key()
        key4 = key_manager.get_key()

        assert key1.key == "key1"
        assert key2.key == "key2"
        assert key3.key == "key3"
        assert key4.key == "key1"

    def test_deactivate_key(self, key_manager):

        key = key_manager.get_key()
        key_manager.deactivate_key(key)

        assert key.active is False

    def test_skips_deactivated_keys(self, key_manager):

        key_manager.deactivate_key(key_manager.keys[0])

        key = key_manager.get_key()

        assert key.key == "key2"

    def test_record_increments_used_units(self, key_manager):

        key = key_manager.get_key()

        key_manager.record(key, 10)
        assert key.used_units == 10

        key_manager.record(key, 5)
        assert key.used_units == 15

    def test_raises_if_all_deactivated(self, key_manager):

        for key in key_manager.keys:
            key_manager.deactivate_key(key)

        with pytest.raises(RuntimeError, match="all keys have reached their quota"):
            key_manager.get_key()

    @pytest.mark.asyncio
    async def test_calculate_delay_sleeps_and_increments(self, key_manager, mocker):

        sleep_mock = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
        key = key_manager.get_key()

        attempt = await key_manager.calculate_delay(attempt=1, backoff_max=5, api=key)
        assert attempt == 2
        sleep_mock.assert_called_once_with(2)

        attempt = await key_manager.calculate_delay(attempt=2, backoff_max=5, api=key)
        assert attempt == 3
        sleep_mock.assert_called_with(4)

    @pytest.mark.asyncio
    async def test_calculate_delay_deactivates_on_max(self, key_manager):

        key = key_manager.get_key()
        await key_manager.calculate_delay(attempt=3, backoff_max=3, api=key)

        assert key.active is False

    @pytest.mark.asyncio
    async def test_execute_success(self, key_manager):
        api = key_manager.get_key()
        service = api.service

        async def fn(s):
            res = s.test_execute()
            return res

        result = await key_manager.execute(fn, units=10)

        assert result == 'success'

    @pytest.mark.asyncio
    async def test_execute_quota_exceeded_deactivates(self, key_manager, mocker):
        key_manager.index = 0
        async def fn(s):
            return s.test_exception()

        result = await key_manager.execute(fn)

        assert result != "success"
        assert key_manager.keys[0].active is False



class TestProxyManager:

    def test_get_proxy_rotates(self, proxy_manager):
        p1 = proxy_manager.get_proxy()
        p2 = proxy_manager.get_proxy()
        p3 = proxy_manager.get_proxy()
        p4 = proxy_manager.get_proxy()

        assert p1 == "http://proxy1"
        assert p2 == "http://proxy2"
        assert p3 == "http://proxy3"
        assert p4 == "http://proxy1"

    def test_deactivate_proxy_skips_inactive(self, proxy_manager):
        proxy_manager.deactivate_proxy()
        proxy = proxy_manager.get_proxy()
        assert proxy == "http://proxy2"

    def test_get_proxy_returns_none_if_all_dead(self, proxy_manager):
        for _ in range(len(proxy_manager.proxies)):
            proxy_manager.deactivate_proxy()
        assert proxy_manager.get_proxy() is None

    @pytest.mark.asyncio
    async def test_execute_success(self, proxy_manager, mocker):
        mock_fn = AsyncMock(return_value="ok")
        result = await proxy_manager.execute(mock_fn)
        assert result == "ok"
        mock_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_if_all_proxies_fail(self, proxy_manager):

        async def fn(proxy='12345'):
            raise RequestError(f'error:{proxy}')

        with pytest.raises(RuntimeError, match="all proxies failed"):
            await proxy_manager.execute(fn)