# app/tests/web/test_webhook_errors.py
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_webhook_no_message(mock_client: AsyncClient):

    update = {"update_id": 4}

    response = await mock_client.post("/telegram/webhook", json=update)
    data = response.json()
    assert response.status_code == 200
    assert data["success"] is False
    assert data["details"] == "no data"


@pytest.mark.asyncio
async def test_webhook_unknown_command(monkeypatch, mock_client: AsyncClient):

    async def mock_dispatch(text, user_states, chat_id):
        return {"success": True, "details": f"unknown state processed for {chat_id}"}

    monkeypatch.setattr("app.main.state_dispatcher.dispatch", mock_dispatch)
    monkeypatch.setattr("app.main.user_crud", type("MockUserCrud", (), {
        "check_exists": staticmethod(lambda chat_id: None)
    })())

    update = {
        "update_id": 5,
        "message": {"chat": {"id": 555}, "text": "word", "message_id": 1},
    }

    response = await mock_client.post("/telegram/webhook", json=update)

    data = response.json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "unknown state" in data["details"]
