from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse
from app.data.models import Word, User
from datetime import datetime, timezone
from app.decorators import log_calls
import logging
from app.telegram_utils.utils import send_message, update_bd
from httpx import AsyncClient

logger = logging.getLogger(__name__)

class WordsCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def add_word(self, word: str, chat_id: int, user_states: User):
        new_word = Word(
            chat_id=chat_id,
            user_id=user_states.id,
            word=word,
            translate=user_states.last_translate,
            language=user_states.lang_code,
        )
        logger.debug('adding new word to database: %s', new_word.word)
        self.db.add(new_word)

        try:
            await self.db.commit()
            await self.db.refresh(new_word)
            logger.info(
                'database update, new word: %s, chat_id: %s',
                new_word.word, new_word.chat_id
            )
        except Exception as e:
            logger.exception('failed to add word %s (chat_id=%i)', new_word.word, new_word.chat_id)
            raise

        return JSONResponse(
            {
                'details': 'word has been successfully added'
            }
        )


    @log_calls
    async def get_words_for_pdf(self, chat_id: int, user_states: User):
        try:
            res = await self.db.execute(
                select(Word).where(
                    Word.chat_id == chat_id,
                    Word.language == user_states.lang_code,
                )
            )
            logger.debug('database access for words, chat_id=%s, lang=%s', chat_id, user_states.lang_code)
        except Exception as e:
            logger.exception('failed to get words from database')
            raise

        words = res.scalars().all()
        logger.info('words retrieved from database: %i', len(words))

        return words

    @log_calls
    async def get_words_for_review(self, chat_id: int, user_states: User):
        try:
            res = await self.db.execute(
                select(Word).where(
                    Word.chat_id == chat_id,
                    Word.language == user_states.lang_code,
                    Word.review_time <= datetime.now(timezone.utc)
                )
            )
            logger.debug('database access for words, chat_id=%s, lang=%s', chat_id, user_states.lang_code)
        except Exception as e:
            logger.exception('failed to get words from database')
            raise

        words = res.scalars().all()
        logger.info('words retrieved from database: %i', len(words))

        return words

    async def get_one_word(self, chat_id: int, user_states: User):
        try:
            res = await self.db.execute(
                select(Word).where(
                    Word.chat_id == chat_id,
                    Word.language == user_states.lang_code,
                    Word.review_time <= datetime.now(timezone.utc)
                ).limit(1)
            )
            logger.debug('database access for words, chat_id=%s, lang=%s', chat_id, user_states.lang_code)
        except Exception as e:
            logger.exception('failed to get words from database')
            raise

        word = res.scalar_one_or_none()
        logger.info('word retrieved from database: %s', word.word)

        return word


    async def delete_word(self, word: str, chat_id: int, user_states: User):
        try:
            await self.db.execute(
                delete(Word).where(
                    Word.chat_id == chat_id, Word.word == word
                )
            )
            logger.debug('database access for deleted word: %s, chat_id: %s, lang: %s', word, chat_id, user_states.lang_code)

            await self.db.commit()
        except Exception as e:
            logger.exception('failed to delete word %s', word)
            raise

        logger.info('word deleted from database: %s', word)

        return JSONResponse(
            {
                'details': 'word has been successfully deleted'
            }
        )


    @log_calls
    async def check_exists(self, word: str, chat_id: int, user_states: User):
        try:
            res = await self.db.execute(
                select(Word).where(
                    Word.chat_id == chat_id, Word.word == word, Word.language == user_states.lang_code
                )
            )
            logger.debug('database access for word: %s', word)
        except Exception as e:
            logger.exception('failed to get word from database')
            return None

        word = res.scalar_one_or_none()
        logger.info('word found: %s', word)

        return word

    async def delete_word_from_list(self, text: str, chat_id: int, user_states: User, client: AsyncClient):
        try:
            result = await self.check_exists(text, chat_id, user_states)
            word_for_delete = text if result else None

            if word_for_delete:
                await self.delete_word(word_for_delete, chat_id, user_states)
                await send_message(chat_id, f'The word {word_for_delete} has been removed.', user_states, client)
            else:
                await send_message(chat_id, 'This word is not on the list.', user_states, client)
            return {'success': True}
        except Exception as e:
            logger.exception('failed to delete word from database: %s', e)
            return {'success': False}
