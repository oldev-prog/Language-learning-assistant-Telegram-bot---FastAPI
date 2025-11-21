import pytest_asyncio
import random
from app.data.models import User, Word
from app.data.user_crud import UserCRUD
from app.data.word_crud import WordsCRUD


@pytest_asyncio.fixture(scope='function')
def chat_id() -> int:
    return random.randint(100000000, 1000000000)

@pytest_asyncio.fixture(scope='function')
def user(chat_id: int) -> User:
    return User(chat_id=chat_id)

@pytest_asyncio.fixture(scope='function')
async def test_user_crud(test_session):
    user_crud = UserCRUD(test_session)
    yield user_crud

@pytest_asyncio.fixture(scope='function')
async def user_for_words(test_session) -> User:
    user = User(
        chat_id=random.randint(100000000, 1000000000),
        id=1,
        lang_code='en',
        last_translate='test-translation'
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    return user

@pytest_asyncio.fixture(scope='function')
async def test_word(user_for_words, test_session) -> Word:
    word = Word(
        chat_id=user_for_words.chat_id,
        user_id=user_for_words.id,
        word='hello world',
        translate=user_for_words.last_translate,
        language=user_for_words.lang_code
    )

    test_session.add(word)
    await test_session.commit()
    await test_session.refresh(word)

    return word


@pytest_asyncio.fixture(scope='function')
async def test_words_crud(test_session):
    words_crud = WordsCRUD(test_session)
    yield words_crud
