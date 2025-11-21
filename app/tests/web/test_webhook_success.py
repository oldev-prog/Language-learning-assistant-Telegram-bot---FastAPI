import pytest
from app.data.models import User, Word

@pytest.mark.asyncio
async def test_webhook_command_start(test_session, mock_bot, mock_start_funcs, monkeypatch, fake_user, mock_user_crud,  mock_client):

    monkeypatch.setattr('app.main.bot', mock_bot)
    monkeypatch.setattr('app.main.user_crud', mock_user_crud)
    monkeypatch.setattr('app.main.command_dispatcher', mock_bot.services.command_dispatcher)
    monkeypatch.setattr('app.main.state_dispatcher', mock_bot.services.state_dispatcher)

    update = {
        'update_id': 1,
        'message': {
            'chat': {'id': 999},
            'text': '/start',
            'message_id': 1
        }
    }

    response = await mock_client.post('/telegram/webhook', json=update)

    assert response.status_code == 200
    json_resp = response.json()
    print(f'json_resp: {json_resp}')
    assert json_resp['success'] is True
    assert 'language' in json_resp['details']


@pytest.mark.asyncio
async def test_webhook_callback(test_session, mock_bot, monkeypatch, mock_client):
    monkeypatch.setattr("app.main.bot", mock_bot)

    user = User(chat_id=999, last_word="apple", native_lang="ru", lang_code="en")
    test_session.add(user)
    await test_session.commit()

    update = {
        "update_id": 12,
        "callback_query": {
            "id": "1",
            "data": "pronounce",
            "message": {"chat": {"id": 999}, "message_id": 12}
        }
    }

    response = await mock_client.post("/telegram/webhook", json=update)

    assert response.status_code == 200
    assert "pronunciation" in response.json()["details"]


