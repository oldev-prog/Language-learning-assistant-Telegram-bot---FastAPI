from app.celery.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def tts_task(self, chat_id: int, word: str, lang: str):
    logger.info('starting tts task')
    from app.main import bot
    result = bot.services.pronunciation_obj.generate_tts(chat_id=chat_id, word=word, lang=lang)
    logger.info('result from celery task: %s', result)

@celery_app.task(bind=True)
def youtube_parsing_task(self, chat_id: int, word: str, lang_code: str, seen_videos: list):
    logger.info('starting youtube task')
    from app.main import bot
    result = bot.services.parsing_obj.run_parsing(word=word, chat_id=chat_id, lang_code=lang_code, seen_ids=seen_videos)
    logger.info('result from celery task: %s', {result})
