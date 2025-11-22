from sqlalchemy.ext.asyncio import AsyncSession
from app.telegram_utils.utils import update_state_to_await
from app.bot.telegram_bot import TelegramBot, Services
from app.data.user_crud import UserCRUD
from app.data.models import User
from fastapi.responses import JSONResponse
from app.telegram_utils.start_funcs import StartFuncs
from app.telegram_utils.utils import raise_invalid_command
from httpx import AsyncClient
import asyncio

class CommandDispatcher:
    def __init__(self, bot: TelegramBot, services: Services, user_crud: UserCRUD, client: AsyncClient):
        self.bot = bot
        self.review_obj = services.review_obj
        self.user_crud = user_crud
        self.client = client
        self.commands = {
            '/start': self.handle_start,
            '/change_learning_lang': self.handle_change_lang,
            '/change_native_lang': self.handle_start,
            '/save_word': self.handle_save,
            '/words_list': self.handle_words_list,
            '/repeating': self.handle_review,
            '/reverse_repeating': self.handle_review,
            '/delete_word': self.handle_delete_word,
        }

    async def dispatch(self, text: str, user_states: User, chat_id: int, client: AsyncClient, db: AsyncSession, msg_id: int):
        handler = self.commands.get(text)

        if handler:
            return await handler(user_states, chat_id, text, client, db, msg_id)

        return await self.handle_invalid( user_states, chat_id, text, client)

    async def handle_start(self, user_states: User, chat_id: int, text: str, client: AsyncClient, db: AsyncSession, msg_id: int):

        await StartFuncs.choice_native_lang(user_state=user_states, chat_id=chat_id, text=text, client=self.client)
        return JSONResponse(
            {
                'success': True, 'details': f'language {user_states.native_lang} has been successfully updated.'
            }
        )

    async def handle_change_lang(self, user_states: User, chat_id: int, text: str, client: AsyncClient, db: AsyncSession, msg_id: int):
        await self.bot.change_learning_lang(user_state=user_states, chat_id=chat_id)
        return JSONResponse(
            {
                'success': True, 'details': 'language has been successfully changed.'
            }
        )

    async def handle_save(self, user_states: User, chat_id: int, text: str, client: AsyncClient, db: AsyncSession, msg_id: int):
        await self.bot.save_word(chat_id=chat_id, user_state=user_states)
        return JSONResponse(
            {
                'success': True, 'details': f'word {user_states.last_word} has been successfully saved'
            }
        )

    async def handle_delete_word(self, user_states: User, chat_id: int, text: str, client: AsyncClient, db: AsyncSession, msg_id: int):
        await self.bot.delete_word(text, chat_id, user_states)

    async def handle_words_list(self, user_states: User, chat_id: int, text: str, client: AsyncClient, db: AsyncSession, msg_id: int):
        await update_state_to_await(user_states, db)
        asyncio.create_task(self.bot.send_words_list(chat_id=chat_id, user_state=user_states))
        return JSONResponse(
            {
                'success': True, 'details': 'words_list has been successfully sent'
            }
        )

    async def handle_review(self, user_states: User, chat_id: int, text: str, client: AsyncClient, db: AsyncSession, msg_id: int):
        await self.bot.spaced_review(chat_id=chat_id, text=text, user_state=user_states, client=client, reply_to_id=msg_id)

    async def handle_invalid(self, user_states: User, chat_id: int, text: str, client: AsyncClient):
        await raise_invalid_command(chat_id, user_states, client)
        return JSONResponse(
            {
                'success': False, 'details': 'was sent invalid command'
            }
        )

