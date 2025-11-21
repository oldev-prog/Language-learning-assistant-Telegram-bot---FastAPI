import pytest, pytest_asyncio
from app.data.models import User, Word
from sqlalchemy import select
import random
from app.data.user_crud import UserCRUD

@pytest.mark.asyncio
class TestUserCRUD:

    async def test_add_get_user(self, test_user_crud, user):
        await test_user_crud.create_user(user.chat_id)

        db_user = await test_user_crud.get_user(user.chat_id)

        for field in ['chat_id', 'state', 'native_lang']:
            assert getattr(user, field) or '' == getattr(db_user, field) or ''

    async def test_check_exists_creates_user_if_missing(self, test_session, test_user_crud, user):
        chat_id = 123456

        res = await test_session.execute(select(User).where(User.chat_id == chat_id))
        assert res.scalar_one_or_none() is None

        user = await test_user_crud.check_exists(chat_id)

        assert isinstance(user, User)
        assert user.chat_id == chat_id

        res = await test_session.execute(select(User).where(User.chat_id == chat_id))
        db_user = res.scalar_one_or_none()
        assert db_user is not None
        assert db_user.id == user.id

    async def test_get_all_words_returns_words_for_user(self, test_session, test_user_crud):
        chat_id = 111222

        user = User(chat_id=chat_id)
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        words = [
            Word(chat_id=chat_id, user_id=user.id, word=f"word{i}", translate="test", language="en")
            for i in range(3)
        ]
        test_session.add_all(words)
        await test_session.commit()

        users_with_words = await test_user_crud.get_all_words(chat_id)

        assert isinstance(users_with_words, list)
        assert len(users_with_words) == 1
        user_from_db = users_with_words[0]
        assert user_from_db.id == user.id
        assert len(user_from_db.words) == 3
        assert set(w.word for w in user_from_db.words) == {"word0", "word1", "word2"}
