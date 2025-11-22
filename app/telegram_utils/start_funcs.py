from app.data.models import User
import logging
from app.telegram_utils.utils import update_bd, valid_answer, send_message
from app.telegram_utils.bottom_funcs import send_keyboard
from app.telegram_utils.bottoms import lang_bottoms, LANGUAGES
from app.dependencies import db
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.decorators import send_action

logger = logging.getLogger(__name__)


class StartFuncs:

    @classmethod
    @send_action()
    async def choice_native_lang(cls, user_state: User, chat_id: int, text: str, client: AsyncClient):

        user_state.state = 'await_native_lang'
        user_state.native_lang = ''
        user_state.lang_code = ''
        user_state.last_word = ''
        user_state.last_translate = ''
        logger.debug('state: %s', user_state.state)

        await update_bd(user_state, db)

        await send_keyboard(chat_id, lang_bottoms, client, True, 'Chose your native language.')

        logger.debug('state: %s', user_state.state)


    @classmethod
    @send_action()
    async def choice_learning_lang(cls, user_state: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient):

        print(f'state: {user_state}')
        logger.debug('text: %s', text)
        if user_state.state == 'await_native_lang':

            if await valid_answer(chat_id, text, user_state, client):
                native_lang = text
                user_state.native_lang = native_lang
                user_state.state = 'await_lang'
                await update_bd(user_state, db)

                await send_keyboard(chat_id, lang_bottoms, client, True, 'What language do you want to learn?')

            else:
                await send_keyboard(chat_id, lang_bottoms, client, True, 'Select your native language.')

        elif user_state.state == 'await_lang':

            if await valid_answer(chat_id, text, user_state, client):

                lang_code = LANGUAGES[text]
                user_state.lang_code = lang_code
                logger.debug('lang_code: %s', user_state.lang_code)

                user_state.state = 'ready'
                await update_bd(user_state, db)

                print(f'states before send msg: {user_state}')
                await send_message(chat_id=chat_id, text=f'Selected language: {text}. The bot is ready to work, you can send words.',
                                   user_state=user_state, client=client, remove_keyboard=True)

            else:
                await send_keyboard(chat_id, lang_bottoms, client, True, 'What language do you want to learn?')


    @classmethod
    @send_action()
    async def change_lang(cls, user_state: User, chat_id: int, db: AsyncSession, client: AsyncClient):
        user_state.state = 'await_lang'

        await update_bd(user_state, db)

        await send_keyboard(chat_id, lang_bottoms, client, True, 'What language do you want to learn?')