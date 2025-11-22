from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.data.models import User, Word
import logging
from app.decorators import log_calls
from app.dependencies import session_dep

logger = logging.getLogger(__name__)


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    @log_calls
    async def get_user(self, chat_id: int):
        try:
            # query = select(User).where(User.chat_id == chat_id)
            res = await self.db.execute(statement=select(User).where(User.chat_id == chat_id))
        except Exception:
            logger.exception('failed to get user from database')
            raise

        user = res.scalar_one_or_none()
        if not user:
            return None
        logger.info('user found: %i', user.chat_id)

        return user


    async def check_exists(self, chat_id):
        user = await self.get_user(chat_id)

        if user is None:
            user = await self.create_user(chat_id)

        await self.db.refresh(user)

        return user


    async def create_user(self, chat_id: int):
        new_user = User(
            chat_id=chat_id,
            state='',
            native_lang='',
            lang_code='',
            last_word='',
            last_translate='',
            review_index=0,
        )

        logger.debug('session: %s', self.db)
        self.db.add(new_user)
        logger.debug('database update, new user: %s', new_user.chat_id)

        try:
            await self.db.commit()
            await self.db.refresh(new_user)
        except Exception as e:
            logger.exception('failed to create new user')
            raise

        logger.info('new user created: %s', new_user.chat_id)

        return new_user

        # return JSONResponse(
        #     {
        #         'details': 'user has been successfully added'
        #     }
        # )

    @log_calls
    async def get_all_words(self, chat_id: int):
        try:
            res = await self.db.execute(
                select(User).where(User.chat_id == chat_id).options(
                    selectinload(User.words)
                )
            )
        except Exception as e:
            logger.exception('failed to get words from database')
            raise

        words_list = res.scalars().all()
        logger.info('words retrieved from database: %i', len(words_list))

        return words_list

    @classmethod
    async def update_bd(cls, obj: list[User | Word] | User, bd=session_dep):
        bd.add(obj)
        await bd.commit()
        await bd.refresh(obj)
        return {'details': 'database has been successfully updated'}