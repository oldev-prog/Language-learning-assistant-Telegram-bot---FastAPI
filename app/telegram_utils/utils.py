import httpx
from app.config import send_msg_url
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.telegram_utils.bottoms import LANGUAGES
from app.data.models import User, Word
from app.schemas.bot_schemas import Commands
#from app.decorators import except_timeout
from app.config import answer_callback_url

logger = logging.getLogger(__name__)

#@except_timeout(3)
async def send_message(chat_id: int, text: str, user_state: User, client: httpx.AsyncClient,
                       remove_keyboard: bool = False, reply_to_message_id: int = None):
    try:
        payload = {
            'chat_id':chat_id,
            'text':text,
            'reply_markup': {
                'remove_keyboard': remove_keyboard
            }
        }

        if reply_to_message_id is not None:
            payload['reply_to_message_id'] = reply_to_message_id

        resp = await client.post(url=send_msg_url, json=payload)

        if not resp.json():
            print('Error')
        else:
            data = resp.json()

    except Exception:
        logger.exception('error sending message')
        raise


async def detect_same_language(word1: str, word2: str) -> bool:
    logger.debug(f'lang1:{word1}, lang2:{word2}')
    return word1.lower().strip() == word2.lower().strip()


async def update_bd(obj: list[User|Word]|User, bd: AsyncSession):
    bd.add(obj)
    await bd.commit()
    await bd.refresh(obj)
    return {'details':'database has been successfully updated'}


async def valid_answer(chat_id: int, text: str, user_state: User, client: httpx.AsyncClient) -> bool:
    if text not in LANGUAGES or text == user_state.native_lang:
        if text == user_state.native_lang:
            await send_message(chat_id, 'This language has already been chosen as the native language.', user_state, client)
        else:
            await send_message(chat_id, f'Invalid language: {text}', user_state, client)
        return False
    return True


async def update_state_to_await(user_state: User, bd: AsyncSession):
    user_state.state = 'await_response'
    await update_bd(user_state, bd)


async def raise_invalid_command(chat_id: int, user_state: User, client: httpx.AsyncClient):
        await send_message(chat_id, 'Invalid command.', user_state, client)
        user_state.state = 'ready'


async def answer_callback(callback_id, client: httpx.AsyncClient):
    payload = {
        'callback_query_id': callback_id,
    }
    await client.post(answer_callback_url, json=payload)