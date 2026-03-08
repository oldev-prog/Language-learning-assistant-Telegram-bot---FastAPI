from app.celery.celery_app import celery_app
import asyncio
import httpx
import logging
from app.bot.telegram_bot import TelegramBot, Services
from app.data.db_init import async_session_factory

logger = logging.getLogger(__name__)


async def _run_tts(chat_id: int, word: str, lang: str):
    async with async_session_factory() as db:
        async with httpx.AsyncClient() as client:
            bot = TelegramBot(Services(db=db, client=client))
            result = bot.services.pronunciation_obj.generate_tts(chat_id=chat_id, word=word, lang=lang)
            logger.info('result from celery task: %s', result)


async def _run_youtube(chat_id: int, word: str, lang_code: str, seen_videos: list):
    async with async_session_factory() as db:
        async with httpx.AsyncClient() as client:
            bot = TelegramBot(Services(db=db, client=client))
            result = bot.services.parsing_obj.run_parsing(
                word=word, chat_id=chat_id, lang_code=lang_code, seen_ids=seen_videos
            )
            logger.info('result from celery task: %s', {result})


@celery_app.task(bind=True)
def tts_task(self, chat_id: int, word: str, lang: str):
    logger.info('starting tts task')
    asyncio.run(_run_tts(chat_id=chat_id, word=word, lang=lang))

@celery_app.task(bind=True)
def youtube_parsing_task(self, chat_id: int, word: str, lang_code: str, seen_videos: list):
    logger.info('starting youtube task')
    asyncio.run(_run_youtube(chat_id=chat_id, word=word, lang_code=lang_code, seen_videos=seen_videos))
