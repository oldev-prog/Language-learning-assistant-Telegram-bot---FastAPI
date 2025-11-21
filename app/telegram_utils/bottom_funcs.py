from app.config import send_msg_url
from app.decorators import except_timeout
from httpx import AsyncClient
from app.telegram_utils.bottoms import explain_bottoms

# @except_timeout(3)
async def send_keyboard(chat_id: int, bottoms, client: AsyncClient, close_or_no : bool = False, text : str = None):
    keyboard = {
            'keyboard': bottoms,
            'resize_keyboard': True,
            'one_time_keyboard': close_or_no
        }

    payload = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': keyboard
        }

    await client.post(url=send_msg_url, json=payload)


async def send_inline_keyboard(chat_id: int, client: AsyncClient,  reply_to: int, text: str = None, bottoms=explain_bottoms):
    keyboard = {
        'inline_keyboard': bottoms,
    }

    payload = {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': keyboard,
        'reply_to_message_id': reply_to
    }

    await client.post(send_msg_url, json=payload)