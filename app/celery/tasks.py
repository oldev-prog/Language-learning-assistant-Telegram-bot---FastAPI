from app.celery.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def tts_task(self, chat_id: int, word: str, lang: str):
    print('starting tts task')
    logger.debug('starting tts task')
    from app.main import bot
    result = bot.services.pronunciation_obj.generate_tts(chat_id=chat_id, word=word, lang=lang)
    print(f'result from celery task: {result}')

@celery_app.task(bind=True)
def youtube_parsing_task(self, chat_id: int, word: str, lang_code: str, seen_videos: list):
    print('starting youtube parsing task')
    logger.debug('starting youtube task')
    from app.main import bot
    result = bot.services.parsing_obj.run_parsing(word=word, chat_id=chat_id, lang_code=lang_code, seen_ids=seen_videos)
    print(f'result from celery task: {result}')


#Завтра: переписать функции из celery_tasks на синхронный код; добавить вызов tasks в state_dispatcher, разобраться с ожиданием ответом tasks при нажатии кнопок раньше получения ответов