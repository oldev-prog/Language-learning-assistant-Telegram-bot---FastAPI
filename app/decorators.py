import logging
import functools
import time
import asyncio
import inspect
from app.config import BOT_TOKEN, send_action_url
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.telegram_utils.utils import send_message, update_bd
    from app.data.user_crud import UserCRUD


def _resolve_http_client(target_obj, kwargs):
    client = kwargs.get('client')
    if client is not None:
        return client

    services = getattr(target_obj, 'services', None)
    if services is not None:
        return getattr(services, 'client', None)

    return None


def _resolve_arg(func, args, kwargs, name):
    try:
        bound = inspect.signature(func).bind_partial(*args, **kwargs)
        return bound.arguments.get(name)
    except Exception:
        return kwargs.get(name)

def log_calls(func):
    '''Async decorator signaling the start of a function and its completion.'''

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

def sync_log_calls(func):
    '''Sync decorator signaling the start of a function and its completion.'''

    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info('called %s with args: %s, %s', func.__name__, args, kwargs)
        start = time.time()
        result = func(*args, **kwargs)
        finish = time.time() - start
        logger.info('finished %s for %f seconds, with result: %s', func.__name__, finish, result)

        return result

    return wrapper

def except_timeout(timeout: float):
    '''A decorator that prevents a request from executing longer than a certain amount of time.'''

    def decorator(func):
        async def wrapper(self, *args, **kwargs):

            logger.debug('args: %s, kwargs: %s', args, kwargs)
            chat_id = _resolve_arg(func, (self, *args), kwargs, 'chat_id')
            user_state = _resolve_arg(func, (self, *args), kwargs, 'user_state')

            logger.debug('user_state is %s', user_state)

            try:
                server_response = await asyncio.wait_for(func(self, *args, **kwargs), timeout)
                #return server_response
            except asyncio.TimeoutError as e:
                from app.telegram_utils.utils import send_message
                from app.data.user_crud import UserCRUD
                client = _resolve_http_client(self, kwargs)

                if client is None:
                    logger.error('http client is not available in timeout handler for %s', func.__name__)
                    raise RuntimeError('http client is required in timeout handler')

                await send_message(chat_id=chat_id, text='The server timed out waiting for a response, please try again later.', client=client, user_state=user_state)
                if user_state is not None:
                    user_state.state = 'ready'
                    db = getattr(getattr(self, 'services', None), 'db', None)
                    if db is not None:
                        await UserCRUD.update_bd(user_state, db)
                return None

            return server_response

        return wrapper

    return decorator



def send_action(seconds: float=0, action: str='typing'):
    '''A decorator that sends a specific action animation to the user during the execution of functions.'''

    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            logger.debug('args: %s, kwargs: %s', args, kwargs)
            chat_id = _resolve_arg(func, (self, *args), kwargs, 'chat_id')
            logger.info('chat_id is %s', chat_id)

            client = _resolve_http_client(self, kwargs)
            if client is None:
                logger.error('http client is not available for send_action in %s', func.__name__)
                raise RuntimeError('http client is required for send_action')

            await client.post(url=send_action_url, json={
                'chat_id': chat_id,
                'action': action,
            })
            await asyncio.sleep(seconds)

            res = await func(self, *args, **kwargs)

            return res

        return wrapper

    return decorator
