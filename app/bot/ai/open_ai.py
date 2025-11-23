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


class AIClient:

    def __init__(self,
                 client: AsyncClient,
                 base_url: str = 'https://api.aitunnel.ru/v1',
                 ):
        self.api_key = os.getenv('OPENAI_KEY')
        self.base_url = base_url
        self.client = client

    repr_cols_num = 4
    repr_cols = []

    def __repr__(self):
        attrs = list(self.__dict__.items())
        cols = []
        for idx, (key, value) in enumerate(attrs):
            if key in self.repr_cols or idx < self.repr_cols_num:
                if key == "api_key":
                    value = "***"
                cols.append(f"{key}={value!r}")
        return f"<{self.__class__.__name__} {', '.join(cols)}>"


    def get_prompt(self, word: str, user_state: User):
        prompt = prompt_template.format(
            word=word,
            learning_lang=user_state.lang_code,
            native_lang=user_state.native_lang,
        )

        return prompt


    def clean_json_block(self, string: str) -> str:
        s = string.strip()

        if s.startswith("```"):
            s = s.strip("`")
            if s.startswith("json"):
                s = s[4:]
            s = s.strip()

        return s

    def format_word_explanation(self, data: dict) -> str:
        if isinstance(data, str):
            data = json.loads(data)
        print(f'data for word explanation: {data}, {type(data)}')
        return (
            f"=== Translation ===\n"
            f"{data['translation']}\n\n"
            f"=== Explanation ===\n"
            f"{data['explanation']}\n\n"
            f"=== Synonyms ===\n"
            f"{data['synonyms']}\n\n"
            f"=== Examples ===\n"
            f"{data['examples']}\n\n"
            f"=== Mnemonic advices ===\n"
            f"{data['mnemonic']}"
        )

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
                      {"role": "user", "content": prompt},
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


    @except_timeout(6)
    @log_calls
    async def get_explanation(self, word: str, user_state: User, db: AsyncSession):

        try:
            unswear = redis_get_hash(chat_id=user_state.chat_id, word=word, lang=user_state.lang_code, field='explanation')
            logger.debug(f'redis:{unswear}') if unswear else logger.debug(f'redis: {None}')
            print(f'redis:{unswear}') if unswear else print(f'redis: {None}')

            if unswear is None:
                unswear = await self.request(word, user_state)
                logger.debug(f'unswear:{unswear}')
                unswear = self.clean_json_block(unswear)
                logger.debug(f'unswear:{unswear}')
                unswear = json.loads(unswear)
                logger.debug(f'type(unswear):{type(unswear)}')

                redis_set_hash(chat_id=user_state.chat_id, word=word, lang=user_state.lang_code,
                               field='explanation', data=unswear)

                explanation = self.format_word_explanation(unswear)

                await self.update_user_state(unswear, word, user_state, db)
            else:
                explanation = self.format_word_explanation(unswear)

                await self.update_user_state(unswear, word, user_state, db)

            return explanation

        except Exception as e:
            logger.exception(f'Error: {e}')
            return 'Error sending, please try again.'


    async def update_user_state(self, data: dict, word: str, user_state: User, db: AsyncSession):
        if isinstance(data, str):
            data = json.loads(data)

        logger.debug('lang_code: %s, native_lang: %s', data['lang_code'], LANGUAGES[user_state.native_lang])
        same_language = await detect_same_language(data['lang_code'], LANGUAGES[user_state.native_lang])

        translate = data['translation'] if not same_language else word
        logger.debug(f'Translate: {translate}')

        word_for_save = data['translation'] if same_language else word
        logger.debug(f'Word detected: {word_for_save}')

        translate_for_save = word if same_language else translate
        logger.debug(f'Translate detected: {translate_for_save}')

        user_state.last_word = word_for_save.lower()
        user_state.last_translate = translate_for_save
        logger.debug(f'user_states:{user_state.__dict__}')

        await update_bd(user_state, db)


    async def send_result(self, chat_id: int, client: AsyncClient, text: str, reply_to: int, user_state: User):

        if text != 'Error sending, please try again.':
            await  send_inline_keyboard(chat_id=chat_id, client=client, text=text, reply_to=reply_to)
        else:
            await send_message(chat_id, text, user_state, client)
