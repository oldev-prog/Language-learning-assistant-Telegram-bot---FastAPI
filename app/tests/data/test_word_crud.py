import pytest
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.data.models import Word

@pytest.mark.asyncio
class TestWordsCRUD:

    async def test_add_word(self, test_words_crud, user_for_words, test_session):

        word = 'test-word'

        response = await test_words_crud.add_word(word, user_for_words.chat_id, user_for_words)

        assert isinstance(response, JSONResponse)
        assert response.body == b'{"details":"word has been successfully added"}'

        res = await test_session.execute(select(Word).where(Word.word == word))
        word_db = res.scalar_one_or_none()

        assert word_db is not None
        assert word_db.word == word
        assert word_db.chat_id == user_for_words.chat_id

    async def test_get_words(self, test_words_crud, test_session, user_for_words, test_word):

        words = await test_words_crud.get_words(user_for_words.chat_id, user_for_words)

        assert isinstance(words, list)
        assert len(words) == 1
        assert words[0].word == test_word.word
        assert words[0].translate == user_for_words.last_translate

    async def test_check_exists(self, test_words_crud, test_session, user_for_words, test_word):

        found_word = await test_words_crud.check_exists(test_word.word, user_for_words.chat_id)

        assert found_word is not None
        assert found_word.word == test_word.word

        missing_word = await test_words_crud.check_exists('missing', user_for_words.chat_id)
        assert missing_word is None

    async def test_delete_word(self, test_words_crud, test_session, user_for_words, test_word):

        response = await test_words_crud.delete_word(test_word.word, user_for_words.chat_id, user_for_words)
        assert isinstance(response, JSONResponse)
        assert response.body == b'{"details":"word has been successfully deleted"}'

        res = await test_session.execute(select(Word).where(Word.word == test_word.word))
        deleted = res.scalar_one_or_none()
        assert deleted is None
