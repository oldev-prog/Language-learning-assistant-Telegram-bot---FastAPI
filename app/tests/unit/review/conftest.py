import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import httpx
from app.bot.spaced_review.review import SpacedReview
from app.data.models import Word, User


@pytest.fixture
def mock_word_crud():
    crud = AsyncMock()
    crud.get_words.return_value = []
    return crud


@pytest.fixture
def sample_words():

    return [
        Word(word="hello", translate="привет"),
        Word(word="world", translate="мир"),
        Word(word="", translate="пусто"),
    ]



@pytest.fixture
def mock_pronunciation():
    pron = AsyncMock()
    pron.send_voice = AsyncMock()
    return pron


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_client():
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def mock_now(monkeypatch):
    fixed_now = datetime(2025, 11, 9, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr('app.bot.review.datetime', MagicMock(now=lambda tz: fixed_now))
    return fixed_now


@pytest.fixture
def sample_review_words():
    word1 = Word(id=1, word='hello', translate='привет', repetitions=2, interval=5, review_time=datetime.now(timezone.utc))
    word2 = Word(id=2, word='world', translate='мир', repetitions=3, interval=10, review_time=datetime.now(timezone.utc))
    return [word1, word2]


@pytest.fixture
def user_state():
    user = User(id=1, chat_id=123, state='reviewing', review_index=0)
    return user


@pytest.fixture
def spaced_review(mock_word_crud, mock_pronunciation, mock_db, mock_client, mock_now, monkeypatch):
    fixed_now = datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr('app.bot.review.datetime.now', MagicMock(now=lambda tz: fixed_now))

    return SpacedReview(
        word_crud=mock_word_crud,
        pronunciation=mock_pronunciation,
        db=mock_db,
        client=mock_client,
    )