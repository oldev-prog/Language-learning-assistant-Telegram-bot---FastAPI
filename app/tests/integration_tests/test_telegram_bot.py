import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock
from sqlalchemy import select
from app.data.models import Word


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_message(bot, mock_send_message, fake_user_state, monkeypatch):

    await bot.send_message('Привет!', chat_id=123, user_state=fake_user_state)
    mock_send_message.assert_awaited_once_with(123, 'Привет!', fake_user_state, bot.services.client)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_explain_word(bot, fake_user_state, mock_send_message, monkeypatch):
    monkeypatch.setattr(
        'app.bot.ai.open_ai.AIClient.get_explanation',
        AsyncMock(return_value='Explanation: hello = привет')
    )

    await bot.explain_word(chat_id=999, word='hello', user_state=fake_user_state)

    mock_send_message.assert_awaited_with(999, 'Explanation: hello = привет', bot.services.client)

    assert fake_user_state.state == 'ready'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_pronunciation(bot, fake_user_state, mock_send_message, monkeypatch):
    mock_pron = AsyncMock()
    monkeypatch.setattr('app.bot.pronunciation.Pronunciation.send_voice', mock_pron)

    await bot.send_pronunciation(chat_id=999, word='hello', user_state=fake_user_state)

    mock_pron.assert_awaited_once_with(999, 'hello', 'en')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_youtube_video_found(bot, fake_user_state, mock_send_message, monkeypatch):
    fake_user_state.last_word = 'hello'
    fake_user_state.state = 'ready'

    mock_parsing = AsyncMock(return_value='https://youtube.com/abc123')

    monkeypatch.setattr(bot.services.parsing_obj, 'run_parsing', mock_parsing)

    print("run_parsing patched:", bot.services.parsing_obj.run_parsing)

    await bot.send_youtube_video(chat_id=999, user_state=fake_user_state)

    mock_send_message.assert_any_await(999, 'Найдено видео с данным словом:https://youtube.com/abc123', fake_user_state,
    bot.services.client)
    assert fake_user_state.state == 'ready'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_youtube_video_not_found(bot, fake_user_state, mock_send_message, monkeypatch):
    fake_user_state.last_word = 'rareword'
    fake_user_state.state = 'ready'

    mock_parsing = AsyncMock(return_value=None)
    monkeypatch.setattr(bot.services.parsing_obj, 'run_parsing', mock_parsing)

    await bot.send_youtube_video(chat_id=999, user_state=fake_user_state)

    mock_send_message.assert_any_await(999, 'Видео не найдено.', fake_user_state, bot.services.client)
    assert fake_user_state.state == 'ready'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_word_new(bot, fake_user_state, mock_send_message, test_session):
    fake_user_state.last_word = 'newword'

    result = await bot.save_word(chat_id=123, user_state=fake_user_state)

    assert result is None

    res = await test_session.execute(select(Word).filter_by(word='newword', chat_id=123))
    word_in_db = res.scalar_one_or_none()

    assert word_in_db is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_word_exists(bot, fake_user_state, mock_send_message, test_session):

    test_session.add(Word(word='exists',
                          chat_id=999,
                          user_id=fake_user_state.id,
                          translate='',
                          language='en'
                          ))
    test_session.commit()

    fake_user_state.last_word = 'exists'

    result = await bot.save_word(chat_id=999, user_state=fake_user_state)

    assert result == {'details': 'word exists already exists'}

    mock_send_message.assert_awaited_with(999, 'Данное слово уже в списке', fake_user_state, bot.services.client)


@pytest.mark.integration
@pytest.mark.asyncio    #DONE!
async def test_delete_word(bot, fake_user_state, mock_send_message, test_session, monkeypatch):

    word = Word(word='todelete', chat_id=999)
    test_session.add(word)
    test_session.commit()

    mock_delete = AsyncMock()
    monkeypatch.setattr(bot.services.word_crud, 'delete_word', mock_delete)

    await bot.delete_word(msg='todelete', chat_id=999, user_state=fake_user_state)

    mock_delete.assert_awaited_once_with('todelete', 999, fake_user_state)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_words_list(bot, mock_send_message, test_session, monkeypatch, fake_user_state):

    test_session.add_all([
        Word(word='one',
             chat_id=999,
             user_id=fake_user_state.id,
             translate='',
             language='en'),

        Word(word='two',
             chat_id=999,
             user_id=fake_user_state.id,
             translate='',
             language='en'
             ),
    ])

    await test_session.commit()

    mock_pdf = AsyncMock(return_value={'buffer': b'PDF_DATA'})
    monkeypatch.setattr(bot.services.pdf_obj, 'generate_pdf', mock_pdf)
    mock_send_pdf = AsyncMock()
    monkeypatch.setattr(bot.services.pdf_obj, 'send_pdf', mock_send_pdf)

    await bot.send_words_list(chat_id=999, user_state=fake_user_state)

    mock_pdf.assert_awaited_once()
    mock_send_pdf.assert_awaited_once_with(999, b'PDF_DATA')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_spaced_review_flow(bot, fake_user_state, mock_send_message, test_session, monkeypatch):

    test_session.add_all([
        Word(word='apple', chat_id=999, interval=1, repetitions=1,
             user_id=fake_user_state.id, translate='', language='en'
             ),
        Word(word='banana', chat_id=999, interval=1, repetitions=1,
             user_id=fake_user_state.id, translate='', language='en'
             ),
    ])

    await test_session.commit()

    fake_user_state.review_index = 0

    mock_start = AsyncMock(return_value=[
        {'word': 'apple', 'quality': 4},
        {'word': 'banana', 'quality': 3}
    ])
    monkeypatch.setattr(bot.services.review_obj, 'start_review', mock_start)

    monkeypatch.setattr(bot.services.review_obj, 'check_valid_answer', lambda *_, **__: True)
    monkeypatch.setattr(bot.services.review_obj, 'check_word_quality', AsyncMock())
    monkeypatch.setattr(bot.services.review_obj, 'update_word_states', AsyncMock())
    monkeypatch.setattr(bot.services.review_obj, 'check_if_finish', AsyncMock())

    await bot.spaced_review(chat_id=999, msg='яблоко', user_state=fake_user_state)

    mock_send_message.assert_awaited_with(999, 'banana', fake_user_state, bot.services.client)
    assert fake_user_state.review_index == 1