from app.data.models import Word, User
from datetime import datetime, timedelta, timezone
from app.telegram_utils.utils import send_message
from app.data.word_crud import WordsCRUD
from app.schemas. bot_schemas import ReviewState
from app.bot.pronunciation import Pronunciation
from app.telegram_utils.bottom_funcs import send_keyboard
from app.telegram_utils.bottoms import review_bottoms
from app.telegram_utils.utils import update_bd
from app.dependencies import session_dep
from typing import List
import logging
from httpx import AsyncClient
from app.bot.spaced_review.review_states import review_states
from app.decorators import send_action, except_timeout

logger = logging.getLogger(__name__)



class SpacedReview:
    EASINESS_4 = 1.75
    EASINESS_5 = 2.5
    quality_map = {
        'forgot': 0,
        'hard': 3,
        'easy': 4,
        'perfect': 5
    }

    def __init__(self, word_crud: WordsCRUD, pronunciation: Pronunciation,
                 db: session_dep, client: AsyncClient):
        self.word_crud = word_crud
        self.pronunciation = pronunciation
        self.db = db
        self.client = client


    def calculate_interval(self, repetitions: int, quality: int, last_interval: int) -> int:
        match repetitions:
            case 1:
                return 1
            case 2:
                return 5
            case 3:
                return 10
            case _:
                match quality:
                    case 4:
                        return int(last_interval * self.EASINESS_4)
                    case 5:
                        return int(last_interval * self.EASINESS_5)
                return last_interval


    async def update_word_states(self, quality: int, word: Word):
        logger.debug('data before update: rep: %s, interval: %s', word.repetitions, word.interval)
        if quality < 3:
            word.repetitions = 0
            word.interval = 1
        elif quality > 3:
            word.repetitions += 1
            word.interval = self.calculate_interval(
                word.repetitions,
                quality,
                word.interval
            )

        logger.info('data after update: rep: %s, interval: %s', word.repetitions, word.interval)

        word.review_time = datetime.now(timezone.utc) + timedelta(minutes=word.interval)
        logger.debug('review_time: %s', word.review_time)


    # async def send_review_message(self, remove_keyboard: bool = True):
    #     await send_message(self.chat_id, self.word.word, remove_keyboard)


    async def get_review_words(self, chat_id: int, user_state: User) -> List[Word]|None:
        words = await self.word_crud.get_words_for_review(chat_id, user_state)
        if not words:
            await send_message(chat_id, 'At the moment there are no words to repeat.', user_state, self.client)
            user_state.state = 'ready'
            return None

        return words


    async def check_word_quality(self, chat_id: int, word: Word, quality: int, user_state: User):
        if quality == 0:

            if user_state.curr_command == '/repeating':
                word_param = 'word'
            else:
                word_param = 'translate'

            word_for_voice_msg = getattr(word, word_param)

            await send_message(chat_id, f'Translation of a forgotten word: {word.translate}', user_state, self.client, reply_to_message_id=user_state.message_id - 1)

            await self.pronunciation.send_voice(chat_id=chat_id, word=word_for_voice_msg, lang=user_state.lang_code,
                                                reply_to=user_state.message_id - 1, user_state=user_state)

            # await  send_inline_keyboard(chat_id=chat_id, client=client, text=text, reply_to=reply_to)


    async def check_valid_answer(self, chat_id: int, msg: str, user_state: User, reply_to: int):
        try:
            ReviewState(msg.lower())
        except ValueError:
            await send_message(chat_id, 'Invalid answer', user_state, self.client, reply_to_message_id=reply_to)
            return False

        user_state.invalid_reply_count = 1
        await update_bd(user_state, self.db)
        return True


    async def check_if_finish(self, chat_id: int, word: Word, words: list[Word], user_state: User, text: str, quality: int, reply_to_id: int, model_param: str):
        if user_state.review_index == len(words) - 1 or text == 'finish repeating':
            await self.finish_review(chat_id, word, user_state, quality, reply_to_id, model_param)
            return True


    @send_action()
    @except_timeout(5)
    async def start_review(self, chat_id: int, user_state: User, text: str, client: AsyncClient, model_param: str):
        if user_state.curr_command == '/repeating':
            words = await self.word_crud.get_words_for_review(chat_id, user_state)
        else:
            words = await self.word_crud.get_words_for_reverse_review(chat_id, user_state)

        user_state.state = 'await_rating'

        review_states[chat_id] = words

        user_state.review_index = 0

        await send_message(chat_id=chat_id, user_state=user_state, text="Let's start repeating, evaluate how well you remember this word.", client=self.client)

        word = getattr(words[user_state.review_index], model_param)

        await send_keyboard(chat_id, review_bottoms, client, False, words[user_state.review_index].word)


    @send_action()
    @except_timeout(5)
    async def continue_review(self, chat_id: int, user_state: User, text: str, client: AsyncClient, reply_to_id: int, model_param: str):
        words = review_states[chat_id]

        if user_state.review_index == len(words):
            user_state.review_index = 0

        word = words[user_state.review_index]
        logger.debug('review word: %s', word)

        quality = self.quality_map.get(text)

        if await self.check_if_finish(chat_id, word, words, user_state, text, quality, reply_to_id, model_param):
            return {'details':'review has been finished'}


        if not await self.check_valid_answer(chat_id, text, user_state, reply_to_id):
            return {'details': 'invalid answer'}

        await self.check_word_quality(chat_id, word, quality, user_state)

        await self.update_word_states(quality, word)

        # await update_bd(word, self.db)

        user_state.review_index += 1

        next_word = words[user_state.review_index]
        logger.debug('next word: %s', next_word)

        word = getattr(next_word, model_param)

        user_state.message_id = await send_message(text=next_word.word, chat_id=chat_id, user_state=user_state, client=client)

        # await send_keyboard(chat_id, review_bottoms, client, True, words[user_state.review_index].word)

    async def finish_review(self, chat_id: int, word: Word, user_state: User, quality: int, reply_to_id: int, model_param: str):
        await self.check_word_quality(chat_id, word, quality, user_state)

        await send_message(chat_id=chat_id, user_state=user_state, text='Repeating has been finished.', client=self.client, remove_keyboard=True)

        user_state.state = 'ready'
        user_state.review_index = 0

        await update_bd(user_state, self.db)

        del review_states[chat_id]


