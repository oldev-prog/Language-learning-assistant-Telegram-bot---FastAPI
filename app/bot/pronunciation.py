import asyncio
from gtts import gTTS
import aiofiles
import tempfile
import os
from app.config import send_voice_url
import logging
from app.decorators import log_calls, except_timeout, send_action
from httpx import AsyncClient

logger = logging.getLogger(__name__)

GOOGLE_TTS_URL = 'https://translate.google.com/translate_tts'


#redis_client = redis.Redis(host='localhost', port=6379, db=0)


class Pronunciation:
    def __init__(self, client: AsyncClient) -> None:
        self.send_voice_url = send_voice_url
        self.client = client


    @log_calls
    async def generate_tts(self, word: str, lang: str) -> str:
        logger.debug(f'language: {lang}')
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = tmp_file.name
        tmp_file.close()

        await asyncio.to_thread(self.synthesize, tmp_path, word, lang)

        return tmp_path

    def synthesize(self, tmp_path, word: str, lang: str) -> None:
        """Blocking TTS call, run in executor"""
        tts = gTTS(text=word, lang=lang)
        with open(tmp_path, "wb") as f:
            tts.write_to_fp(f)

    @except_timeout(5)
    @send_action(0.33, 'record_voice')
    @log_calls
    async def send_voice(self, chat_id: int, word: str, lang: str, reply_to: int) -> None:
        logger.debug(f"Type of word: {type(word)}, Value: {word}")
        tmp_filename = await self.generate_tts(word, lang)
        logger.debug(f"tmp_filename: {tmp_filename}")

        try:
            async with aiofiles.open(tmp_filename, 'rb') as f:
                voice_bytes = await f.read()

            files = {'voice': (f'{word}.mp3', voice_bytes, 'audio/mpeg')}
            data = {
                'chat_id':chat_id,
                'reply_to_message_id': reply_to
            }
            response = await self.client.post(url=send_voice_url, data=data, files=files)
            logger.info(f"response: {response}")
            json_response = response.json()
            logger.info(f"response: {json_response}")

            if not json_response:
                logger.error('file is empty')
        except Exception:
            logger.exception("voice message wasn't sent")
            raise
        finally:
            os.remove(tmp_filename)
