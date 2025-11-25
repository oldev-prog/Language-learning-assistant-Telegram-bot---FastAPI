import asyncio
from gtts import gTTS
import aiofiles
import tempfile
import os
from app.telegram_utils.utils import send_message
from app.config import send_voice_url
import logging
from app.decorators import log_calls, except_timeout, send_action, sync_log_calls
from httpx import AsyncClient
from app.data.cache.redis_crud import *
from app.data.models import User

logger = logging.getLogger(__name__)

GOOGLE_TTS_URL = 'https://translate.google.com/translate_tts'

class Pronunciation:
    def __init__(self, client: AsyncClient) -> None:
        self.send_voice_url = send_voice_url
        self.client = client


    @sync_log_calls
    def generate_tts(self, word: str, lang: str, chat_id: int):
        logger.debug(f'language: {lang}')
        tts_bytes = redis_get_hash(chat_id=chat_id, word=word, lang=lang, field='pronunciation')

        if tts_bytes is None or tts_bytes == 'Error':
            try:
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmp_path = tmp_file.name
                tmp_file.close()

                self.synthesize(tmp_path, word, lang)

                with open(tmp_path, 'rb') as f:
                    tts_bytes = f.read()

                os.remove(tmp_path)

            except Exception as e:
                logger.error(f'failed to synthesize: {e}')
                tts_bytes = 'Error'

            print(f'data for redis: {tts_bytes}')
            redis_set_hash(chat_id=chat_id, word=word, lang=lang, field='pronunciation', data=tts_bytes)

        return tts_bytes

    def synthesize(self, tmp_path, word: str, lang: str) -> None:
        """Blocking TTS call, run in executor"""
        tts = gTTS(text=word, lang=lang)
        with open(tmp_path, "wb") as f:
            tts.write_to_fp(f)

    @except_timeout(5)
    @send_action(0.33, 'record_voice')
    @log_calls
    async def send_voice(self, chat_id: int, word: str, lang: str, reply_to: int, user_state: User):

        tts_data = None
        count = 0

        while not tts_data and count < 15:
            tts_data_from_redis = redis_get_hash(chat_id=chat_id, word=word, lang=lang, field='pronunciation')
            logger.info(f'tts_data_from_redis: {tts_data_from_redis}') if tts_data_from_redis else None
            print(f'tts_data_from_redis: {tts_data_from_redis}') if tts_data_from_redis else None
            if tts_data_from_redis == 'Error' or tts_data_from_redis is None:
                result = await asyncio.to_thread(self.generate_tts, word=word, lang=lang, chat_id=chat_id)
                if result == 'Error':
                    await send_message(chat_id=chat_id, text='Failed to generate voice message. Please try again later.',
                                       user_state=user_state, client=self.client)
                    return {'detail': 'failed to generate voice message'}
            # elif tts_data_from_redis is None:
            #     await asyncio.sleep(0.2)
            #     count += 1
            #     continue
            else:
                tts_data = tts_data_from_redis

            count += 1

            await asyncio.sleep(0.2)

        try:

            files = {'voice': (f'{word}.mp3', tts_data, 'audio/mpeg')}
            data = {
                'chat_id':chat_id,
                'reply_to_message_id': reply_to
            }
            response = await self.client.post(url=send_voice_url, data=data, files=files)
            logger.info(f'response: {response}')
            json_response = response.json()
            logger.info(f'response: {json_response}')

            if not json_response:
                logger.error('file is empty')
        except Exception:
            logger.exception('voice message was not sent')
            raise
