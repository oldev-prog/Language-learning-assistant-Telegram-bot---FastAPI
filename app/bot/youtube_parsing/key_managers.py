from typing import Callable, Any, Union, Awaitable
from googleapiclient.errors import HttpError
import inspect
from time import time
import asyncio
import socket
import logging
import httpx
from httpx import HTTPError

logger = logging.getLogger(__name__)

class Key:
    def __init__(self, key: str, service_factory: Callable[[str], Any]):
        self.key = key
        self.service = service_factory(key)
        self.used_units = 0
        self.active = True

# class KeyManager:
#     def __init__(self, keys: list[str], service_factory: Callable[[str], Any]):
#         self.keys = [Key(key, service_factory) for key in keys if key]
#         self.index = 0
#
#     def get_key(self) -> Key:
#         number_of_keys = len(self.keys)
#
#         for _ in range(number_of_keys):
#             api = self.keys[self.index]
#             self.index = (self.index +1) % number_of_keys
#             if api.active:
#                 return api
#
#         raise RuntimeError('all keys have reached their quota')
#
#     def deactivate_key(self, api: Key):
#         api.active = False
#         logger.info('key: %s has been deactivated', api.key)
#
#     def record(self, api: Key, units: int):
#         api.used_units += units
#         logger.info('key %s, unit: %f, used_units: %f', api.key, units, api.used_units)
#
#     async def calculate_delay(self, attempt: int, backoff_max: int, api: Key):
#         if attempt < backoff_max:
#             delay = 2 ** attempt
#             await asyncio.sleep(delay)
#             return attempt + 1
#         else:
#             self.deactivate_key(api)
#
#
#     async def execute(
#             self,
#             fn: Callable[[Any], Any|Awaitable[Any]],
#             units: int|Callable[[Any], int] = 0,
#             backoff_max: int = 3
#     ):
#         attempt = 0
#
#         while True:
#             if self.keys[len(self.keys) - 1].active == False:
#                 logger.error('all key are deactivated')
#                 break
#             api = self.get_key()
#             logger.debug('started executing %s', fn.__name__)
#             result = fn(api.service)
#
#             try:
#                 response = await result if hasattr(result, '__await__') else result
#
#                 self.record(api, units(response) if callable(units) else units)
#
#                 return response
#
#             except HttpError as e:
#                 err_msg = e.content.decode('utf-8')
#                 logger.error(err_msg)
#
#                 if 'quotaExceeded' in err_msg or 'dailyLimitExceeded' in err_msg:
#                     self.deactivate_key(api)
#                     continue
#
#                 if 'rateLimitExceeded' in err_msg:
#                     attempt = await self.calculate_delay(attempt, backoff_max, api)
#                     continue
#
#                 raise
#
#             except (ConnectionResetError, socket.error) as e:
#                 err_msg = str(e)
#                 logger.error(err_msg)
#
#                 attempt = await self.calculate_delay(attempt, backoff_max, api)
#                 continue

class KeyManager:
    def __init__(self, keys: list[str], service_factory: Callable[[str], Any]):
        self.keys = [Key(key, service_factory) for key in keys if key]
        self.index = 0

    def get_active_keys(self):
        return [k for k in self.keys if k.active]

    def get_key(self) -> Key:
        active_keys = self.get_active_keys()

        if not active_keys:
            raise RuntimeError("all keys have reached their quota")

        number_of_keys = len(self.keys)

        for _ in range(number_of_keys):
            api = self.keys[self.index]
            self.index = (self.index + 1) % number_of_keys

            if api.active:
                return api

        raise RuntimeError("all keys have reached their quota")

    def deactivate_key(self, api: Key):
        api.active = False
        logger.warning('⛔ key deactivated: %s', api.key)

    def record(self, api: Key, units: int):
        api.used_units += units
        logger.info('key %s, unit: %f, used_units: %f', api.key, units, api.used_units)

    async def calculate_delay(self, attempt: int, backoff_max: int, api: Key):
        if attempt < backoff_max:
            delay = 2 ** attempt
            logger.info("⏳ rate limit, retry in %s seconds", delay)
            await asyncio.sleep(delay)
            return attempt + 1
        else:
            self.deactivate_key(api)
            return attempt

    async def execute(
            self,
            fn: Callable[[Any], Any | Awaitable[Any]],
            units: int | Callable[[Any], int] = 0,
            backoff_max: int = 3
    ):
        attempt = 0

        while True:

            active_keys = self.get_active_keys()
            if not active_keys:  # <── правильная проверка
                logger.error('❌ all keys are deactivated')
                return None

            api = self.get_key()

            logger.debug('▶ executing %s with key %s', fn.__name__, api.key)

            try:
                result = fn(api.service)
                response = await result if hasattr(result, '__await__') else result

                # units calc
                self.record(api, units(response) if callable(units) else units)

                return response

            except HttpError as e:
                err_msg = e.content.decode('utf-8')
                logger.error('❗ HttpError: %s', err_msg)

                if 'quotaExceeded' in err_msg or 'dailyLimitExceeded' in err_msg:
                    self.deactivate_key(api)
                    continue

                if 'rateLimitExceeded' in err_msg:
                    attempt = await self.calculate_delay(attempt, backoff_max, api)
                    continue

                raise

            except (ConnectionResetError, socket.error) as e:
                logger.error("⚠ Connection error: %s", str(e))
                attempt = await self.calculate_delay(attempt, backoff_max, api)
                continue



class ProxyManager:
    def __init__(self, proxies: list[str]):
        self.proxies = proxies
        self.active = [True]*len(proxies)
        self.index = 0
        self.number_of_proxies = len(self.proxies)

    def deactivate_proxy(self):
        idx = (self.index - 1) % self.number_of_proxies
        self.active[idx] = False
        logger.info('proxies %s has been deactivated', self.proxies[self.index])
        self.index = (self.index+1) % self.number_of_proxies

    def get_proxy(self):
        for _ in range(self.number_of_proxies):
            idx = self.index
            self.index = (self.index + 1) % self.number_of_proxies
            if self.active[idx]:
                return self.proxies[idx]

        return None

    async def execute(self, fn: Callable[[str], Awaitable[Any]]):
        while True:
            proxy = self.get_proxy()
            if proxy is None:
                raise RuntimeError('all proxies failed.')
            try:
                return await fn(proxy)
            except (httpx.RequestError, ConnectionResetError, socket.error):
                self.deactivate_proxy()
                logger.info('proxy: %s has been changed', self.proxies[self.index-1])
                continue

