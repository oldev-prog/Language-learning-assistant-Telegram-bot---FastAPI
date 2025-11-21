from app.data.user_crud import UserCRUD
from app.decorators import except_timeout, send_action
from app.telegram_utils.utils import send_message
from app.data.models import User, Word
from app.bot.review import SpacedReview
from app.data.word_crud import WordsCRUD
from app.bot.pronunciation import Pronunciation
from app.schemas.bot_schemas import ReviewState
from app.bot.ai.open_ai import AIClient
from app.telegram_utils.utils import update_bd
from app.dependencies import session_dep
from app.bot.pdf import PDF
from io import BytesIO
from app.bot.youtube_parsing.youtube_parsing import YouTubeParsing
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
import asyncio
from app.config import send_action_url
from app.telegram_utils.bottom_funcs import send_inline_keyboard, send_keyboard
from app.telegram_utils.bottoms import lang_bottoms

logger = logging.getLogger(__name__)

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:

            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


class Services:
    """Dependencies for TelegramBot"""

    def __init__(self, db: AsyncSession, client: AsyncClient):
        self.db = db
        self.client = client
        self.word_crud = WordsCRUD(self.db)
        self.ai_client = AIClient(self.client)
        self.pronunciation_obj = Pronunciation(self.client)
        self.review_obj = SpacedReview(
            self.word_crud, self.pronunciation_obj,
            self.db, self.client,
        )
        self.pdf_obj = PDF(self.client, send_message)
        self.parsing_obj = YouTubeParsing()


class TelegramBot:
    """General object coordinates the work of services"""

    def __init__(self,services: Services) -> None:
        self.services = services


    @send_action()
    async def send_message(self, text: str, chat_id: int, user_state: User):
        await send_message(chat_id=chat_id, text=text, user_state=user_state, client=self.services.client)


    async def update_user_state(self, user_state: User):
        user_state.state = 'ready'
        await update_bd(user_state, self.services.db)


    @except_timeout(7)
    @send_action()
    async def explain_word(self, *, chat_id: int, word: str, user_state: User, reply_to_id: int):

        result = await self.services.ai_client.get_explanation(word=word, user_state=user_state, db=self.services.db)

        await self.services.ai_client.send_result(chat_id, self.services.client, result, reply_to_id, user_state)

        await self.update_user_state(user_state)


    async def send_pronunciation(self, chat_id: int, user_state: User, reply_to_id: int):
        word = user_state.last_word
        await self.services.pronunciation_obj.send_voice(chat_id=chat_id, word=word, lang=user_state.lang_code, reply_to=reply_to_id)

        await self.update_user_state(user_state)

    @except_timeout(30)
    async def send_youtube_video(self, chat_id: int, user_state: User):
        await self.send_message('It may take some time to search for videos.', chat_id, user_state)

        await self.services.parsing_obj.send_result(chat_id=chat_id, user_state=user_state, db=self.services.db, client=self.services.client)

        await self.update_user_state(user_state)


    @except_timeout(7)
    async def save_word(self, chat_id: int, user_state: User):
        word = user_state.last_word

        if await self.services.word_crud.check_exists(word, chat_id, user_state) is not None:
            await  self.send_message('This word is already on the list', chat_id, user_state)
            return {'details':f'word {word} already exists'}

        await self.services.word_crud.add_word(word, chat_id, user_state)

        await self.send_message(text=f'The word {word} has been saved.', chat_id=chat_id, user_state=user_state)


    @except_timeout(5)
    async def delete_word(self, msg: str, chat_id: int, user_state: User):
        await self.send_message(chat_id=chat_id, text='Enter the word you want to delete.', user_state=user_state)

        user_state.state = 'await_delete_word'
        await update_bd(user_state, self.services.db)


    @send_action()
    @except_timeout(3)
    async def change_lang(self, chat_id: int, user_state: User):
        user_state.state = 'await_lang'
        await update_bd(user_state, self.services.db)

        await send_keyboard(chat_id, lang_bottoms, self.services.client, True, 'What language do you want to learn?')



    @except_timeout(5)
    @send_action(1, 'upload_document')
    async def send_words_list(self, chat_id: int, user_state: User):
        words = await self.services.word_crud.get_words_for_pdf(chat_id=chat_id, user_states=user_state)
        print(f'words: {words}')

        if not words:
            await self.send_message(chat_id=chat_id, text='Your list is empty.', user_state=user_state)
            return {'details':'no words in list'}

        pdf_file = await self.services.pdf_obj.generate_pdf(words)

        await self.services.pdf_obj.send_pdf(chat_id, pdf_file['buffer'])

        await self.update_user_state(user_state)


    async def spaced_review(self, chat_id: int, text: str, user_state: User, client: AsyncClient, reply_to_id: int):
        if user_state.state == 'ready':
            await self.services.review_obj.start_review(chat_id=chat_id, user_state=user_state, text=text, client=client)
        else:
            await self.services.review_obj.continue_review(chat_id=chat_id, user_state=user_state, text=text, client=client, reply_to_id=reply_to_id)
