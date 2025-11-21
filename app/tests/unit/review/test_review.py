import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from app.bot.review import SpacedReview
from app.data.models import User, Word
from datetime import timedelta, datetime, timezone

from app.tests.unit.review.conftest import sample_review_words


class TestSpacedReview:

    def test_calculate_interval_first_repetition(self):
        review = SpacedReview(Mock(), Mock(), Mock(), Mock())
        assert review.calculate_interval(repetitions=1, quality=5, last_interval=1) == 1

    def test_calculate_interval_second_repetition(self):
        review = SpacedReview(Mock(), Mock(), Mock(), Mock())
        assert review.calculate_interval(repetitions=2, quality=4, last_interval=1) == 5

    def test_calculate_interval_third_repetition(self):
        review = SpacedReview(Mock(), Mock(), Mock(), Mock())
        assert review.calculate_interval(repetitions=3, quality=5, last_interval=1) == 10

    def test_calculate_interval_quality_4(self):
        review = SpacedReview(Mock(), Mock(), Mock(), Mock())
        interval = review.calculate_interval(repetitions=4, quality=4, last_interval=10)
        assert interval == int(10 * review.EASINESS_4)  # 17

    def test_calculate_interval_quality_5(self):
        review = SpacedReview(Mock(), Mock(), Mock(), Mock())
        interval = review.calculate_interval(repetitions=5, quality=5, last_interval=10)
        assert interval == int(10 * review.EASINESS_5)  # 25

    def test_calculate_interval_default(self):
        review = SpacedReview(Mock(), Mock(), Mock(), Mock())
        assert review.calculate_interval(repetitions=4, quality=3, last_interval=10) == 10

    @pytest.mark.asyncio
    async def test_update_word_states_quality_below_3(self, spaced_review, sample_review_words, mock_now):
        word = sample_review_words[0]
        word.repetitions = 5
        word.interval = 100

        await spaced_review.update_word_states(quality=0, word=word)

        assert word.repetitions == 0
        assert word.interval == 1

    @pytest.mark.asyncio
    async def test_update_word_states_quality_above_3(self, spaced_review, sample_words, mock_now):
        word = sample_words[0]
        word.repetitions = 2
        word.interval = 5

        await spaced_review.update_word_states(quality=4, word=word)

        assert word.repetitions == 3

        assert word.interval == 10

    @pytest.mark.asyncio
    async def test_update_word_states_quality_above_3_2(self, spaced_review, sample_words, mock_now):
        word = sample_words[0]
        word.repetitions = 3
        word.interval = 5

        await spaced_review.update_word_states(quality=4, word=word)

        assert word.repetitions == 4

        assert word.interval == int(5 * spaced_review.EASINESS_4)

    @pytest.mark.asyncio
    async def test_get_review_words_no_words(self, spaced_review, mock_client, user_state, monkeypatch):
        mock_send_message = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)

        result = await spaced_review.get_review_words(chat_id=123, user_state=user_state)

        assert result is None

        mock_send_message.assert_called_once_with(123, 'На данный момент слов на повторение нет.', mock_client)

        assert user_state.state == 'ready'

    @pytest.mark.asyncio
    async def test_get_review_words_has_words(self, spaced_review, sample_words, monkeypatch):
        spaced_review.word_crud.get_words.return_value = sample_words
        mock_send_message = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)

        result = await spaced_review.get_review_words(chat_id=123, user_state=MagicMock())

        assert result == sample_words

        mock_send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_word_quality_forgets_word(self, spaced_review, monkeypatch):
        word = Word(word='test', translate='тест')
        mock_send_message = AsyncMock()
        mock_send_voice = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)
        spaced_review.pronunciation.send_voice = mock_send_voice

        await spaced_review.check_word_quality(chat_id=123, word=word, quality=0)

        mock_send_message.assert_called_once_with(123, 'Перевод забытого слова: тест', spaced_review.client)

        mock_send_voice.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_word_quality_remembers(self, spaced_review, monkeypatch):
        mock_send_message = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)

        await spaced_review.check_word_quality(chat_id=123, word=Mock(), quality=4)

        mock_send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_valid_answer_valid(self, spaced_review, monkeypatch):
        mock_send_message = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)

        result = await spaced_review.check_valid_answer(chat_id=123, msg='отлично')

        assert result is True

        mock_send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_valid_answer_invalid(self, spaced_review, monkeypatch):
        mock_send_message = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)

        result = await spaced_review.check_valid_answer(chat_id=123, msg='не знаю')

        assert result is False
        mock_send_message.assert_called_once_with(123, 'Недопустимый ответ.', spaced_review.client)

    @pytest.mark.asyncio
    async def test_check_if_finish_last_word(self, spaced_review, monkeypatch):
        user_state = User(review_index=1)
        words = [Mock(), Mock()]
        mock_finish = AsyncMock()
        monkeypatch.setattr(spaced_review, 'finish_review', mock_finish)

        await spaced_review.check_if_finish(
            chat_id=123, word=words[1], words=words, user_state=user_state, msg='хорошо', quality=4
        )

        mock_finish.assert_called_once_with(123, words[1], user_state, 4)

    @pytest.mark.asyncio
    async def test_check_if_finish_manual_stop(self, spaced_review, monkeypatch):
        user_state = User(review_index=0)
        words = [Mock(), Mock()]
        mock_finish = AsyncMock()
        monkeypatch.setattr(spaced_review, 'finish_review', mock_finish)

        await spaced_review.check_if_finish(
            chat_id=123, word=words[0], words=words, user_state=user_state, msg='завершить повторение', quality=0
        )

        mock_finish.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_review_no_words(self, spaced_review, user_state, monkeypatch):
        mock_get_words = AsyncMock(return_value=None)
        monkeypatch.setattr(spaced_review, 'get_review_words', mock_get_words)
        mock_send_message = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)

        result = await spaced_review.start_review(chat_id=123, user_state=user_state)

        assert result is None
        mock_get_words.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_review_with_words(self, spaced_review, sample_words, user_state, monkeypatch):
        mock_get_words = AsyncMock(return_value=sample_words)
        monkeypatch.setattr(spaced_review, 'get_review_words', mock_get_words)

        mock_send_message = AsyncMock()
        mock_send_keyboard = AsyncMock()
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)
        monkeypatch.setattr('app.bot.review.send_keyboard', mock_send_keyboard)

        result = await spaced_review.start_review(chat_id=123, user_state=user_state)

        assert result == sample_words
        assert user_state.review_index == 0

        mock_send_message.assert_called_once_with(
            123, 'Начинаeм повторение, оцените насколько хорошо вы помните слово.', spaced_review.client
        )

    @pytest.mark.asyncio
    async def test_finish_review(self, spaced_review, sample_words, user_state, monkeypatch):
        word = sample_words[0]
        user_state.review_index = 0
        mock_check_quality = AsyncMock()
        mock_send_message = AsyncMock()
        mock_update_bd = AsyncMock()
        monkeypatch.setattr(spaced_review, 'check_word_quality', mock_check_quality)
        monkeypatch.setattr('app.bot.review.send_message', mock_send_message)
        monkeypatch.setattr('app.bot.review.update_bd', mock_update_bd)

        await spaced_review.finish_review(chat_id=123, word=word, user_state=user_state, quality=5)

        mock_check_quality.assert_called_once_with(123, word, 5)
        mock_send_message.assert_called_once_with(123, 'Повторение завершено.', spaced_review.client)

        assert user_state.state == 'ready'
        assert user_state.review_index == 0

        mock_update_bd.assert_called_once_with([user_state, word], spaced_review.db)