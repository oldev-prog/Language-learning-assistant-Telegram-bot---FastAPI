from app.celery.celery_app import celery_app
import asyncio
from app.data.models import User

@celery_app.task(bind=True)
def tts_task(self, chat_id: int, word: str, lang: str):
    from app.main import bot
    asyncio.run(bot.services.pronunciation_obj.generate_tts(chat_id=chat_id, word=word,
                                                            lang=lang))


@celery_app.task(bind=True)
def youtube_parsing_task(self, chat_id: int, word: str, lang_code: str, seen_videos: list):
    from app.main import bot
    asyncio.run(bot.services.parsing_obj.run_parsing(word=word, chat_id=chat_id,
                                                     lang_code=lang_code, seen_ids=seen_videos))


#Завтра: переписать функции из celery_tasks на синхронный код; добавить вызов tasks в state_dispatcher, разобраться с ожиданием ответом tasks при нажатии кнопок раньше получения ответов