from app.bot.telegram_bot import TelegramBot
from app.data.models import User
from app.telegram_utils.start_funcs import StartFuncs
from fastapi.responses import JSONResponse
from app.telegram_utils.utils import update_state_to_await, raise_invalid_command, send_message
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.telegram_utils.utils import update_bd
import asyncio

class StateDispatcher:
    def __init__(self, bot: TelegramBot, db: AsyncSession):
        self.bot = bot
        self.states = {
            'await_native_lang':self.handle_await_native_lang,
            'await_lang':self.handle_await_lang,
            'await_response':self.handle_await_response,
            'await_rating':self.handle_await_rating,
            'ready':self.handle_ready,
            'await_delete_word':self.handle_await_delete_word
        }
        self.db = db


    async def dispatch(self, text: str, user_states: User, chat_id: int, client: AsyncClient, msg_id: int):
        handler = self.states.get(user_states.state)

        if handler:
            return await handler(user_states, chat_id, text, self.db, client, msg_id)

        return {'success': False}

    async def handle_await_native_lang(self, user_states: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient, msg_id: int):
        await StartFuncs.choice_learning_lang(user_state=user_states, chat_id=chat_id, text=text, db=self.db, client=client)
        return JSONResponse(
            {
                'success': True, 'details': f'language {user_states.native_lang} has been successfully updated.'
            }
        )

    async def handle_await_lang(self, user_states: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient, msg_id: int):
        await StartFuncs.choice_learning_lang(user_state=user_states, chat_id=chat_id, text=text, db=db, client=client)
        return JSONResponse(
            {
                'success': True, 'details': 'the bot is ready to work'
            }
        )

    async def handle_await_response(self, user_states: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient, msg_id: int):
        await send_message(user_state=user_states, chat_id=chat_id, text='Please, wait for a response.', client=client, reply_to_message_id=msg_id)
        # await self.bot.send_message('Дождитесь ответа', chat_id, user_states)
        return JSONResponse(
            {
                'success': True, 'details': 'the bot is awaiting response'
            }
        )

    async def handle_await_rating(self, user_states: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient, msg_id: int):
        await self.bot.spaced_review(chat_id=chat_id, text=text, user_state=user_states, client=client, reply_to_id=msg_id)
        return JSONResponse(
            {
                'success': True, 'details': 'review has been successfully started'
            }
        )

    async def handle_ready(self, user_states: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient, msg_id: int):
        if text != 'invalid command':
            await update_state_to_await(user_states, db)
            asyncio.create_task(self.bot.explain_word(chat_id=chat_id, word=text, user_state=user_states, reply_to_id=msg_id))
            return JSONResponse(
                {
                    'success': True, 'details': 'explanation has been successfully done'
                }
            )

        await raise_invalid_command(chat_id, user_states, client)
        return JSONResponse(
            {
                'success': False, 'details': 'was sent invalid command'
            }
        )

    async def handle_await_delete_word(self, user_states: User, chat_id: int, text: str, db: AsyncSession, client: AsyncClient, msg_id: int):
        user_states.state = 'ready'
        await update_bd(user_states, self.db)

        await self.bot.services.word_crud.delete_word_from_list(text, chat_id, user_states, client)
        return JSONResponse(
          {
              'success': True, 'details': 'words has been successfully deleted'
          }
        )