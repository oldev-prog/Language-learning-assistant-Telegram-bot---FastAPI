import os
from dotenv import load_dotenv
from app.data.cache.redis_crud import *
from app.decorators import log_calls, except_timeout
from app.telegram_utils.utils import detect_same_language
from app.telegram_utils.bottoms import LANGUAGES
import logging
from app.bot.ai.prompt import json_schema, prompt_template
import json
from app.data.models import User
from app.telegram_utils.utils import update_bd
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.telegram_utils.bottom_funcs import send_inline_keyboard
from app.telegram_utils.utils import send_message

logger = logging.getLogger(__name__)

load_dotenv()

@log_calls
async def request(self, word: str, user_state: User):
    try:
        prompt = self.get_prompt(word, user_state)
        logger.debug(f'requesting "{prompt}"')

        response = await self.client.post(
            "https://api.aitunnel.ru/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json ={
                # "model": "gpt-4.1-nano",
                "model": "gemini-2.5-flash-lite",
                # "model": "qwen3-coder-30b-a3b-instruct",
                # "model": "mistral-small-3.2-24b-instruct",
                # "model": "devstral-small",
                # "model": "mistral-nemo",

                "messages": [
                  {"role": "user", "content": f"Определи языковой код данного слова: {word}"},
                ],
                "response_format": json_schema
            },
            timeout=30
        )

        data = response.json()
        logger.debug('response: %s', data)

        result = data["choices"][0]["message"]["content"]

        return result

    except Exception as e:
        logger.exception('error, no response from chatgpt received')
        raise