import logging
import functools
import time
import asyncio
import httpx
from app.logger_config import configure_logger
from app.config import BOT_TOKEN, send_action_url
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.telegram_utils.utils import send_message, update_bd
    from app.data.user_crud import UserCRUD

def log_calls(func):
    # configure_logger(logging.DEBUG)
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info('called %s with args: %s, %s', func.__name__, args, kwargs)
        start = time.time()
        result = await func(*args, **kwargs)
        finish = time.time() - start
        logger.info('finished %s for %f seconds, with result: %s', func.__name__, finish, result)

        return result

    return wrapper


def except_timeout(timeout: float):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):

            logger.debug('args: %s, kwargs: %s', args, kwargs)
            chat_id = kwargs.get('chat_id')
            user_state = kwargs.get('user_state')

            logger.debug('user_state is %s', user_state)

            try:
                from app.main import client
                server_response = await asyncio.wait_for(func(self, *args, **kwargs), timeout)
                #return server_response
            except asyncio.TimeoutError as e:
                from app.telegram_utils.utils import send_message
                from app.data.user_crud import UserCRUD

                await send_message(chat_id=chat_id, text='The server timed out waiting for a response, please try again later.', client=client, user_state=user_state)
                user_state.state = 'ready'
                await UserCRUD.update_bd(user_state, self.services.db)
                return None

            return server_response

        return wrapper

    return decorator


def send_action(seconds: float=0, action: str='typing'):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            logger.debug('args: %s, kwargs: %s', args, kwargs)
            chat_id = kwargs.get('chat_id')
            logger.info('chat_id is %s', chat_id)

            from app.main import client

            await client.post(url=send_action_url, json={
                'chat_id': chat_id,
                'action': action,
            })
            await asyncio.sleep(seconds)

            res = await func(self, *args, **kwargs)

            return res

        return wrapper

    return decorator

