from pydantic import BaseModel, Field
from enum import Enum
from app.schemas.word_schemas import Language, WordGET
from typing import List


class States(Enum):
    await_native_lang = 'await_native_lang'
    await_lang = 'await_lang'
    ready = 'ready'
    await_response = 'await_response'
    await_delete_word = 'await_delete_word'
    await_rating = 'await_rating'
    empty = ''


class UserPOST(BaseModel):
    state: States
    native_lang: Language
    last_word: str = Field(..., max_length=100)
    last_translate: str = Field(..., max_length=100)
    review_index: int = Field(..., le=0)

class UserGET(UserPOST):
    chat_id: int
    words: List[WordGET]