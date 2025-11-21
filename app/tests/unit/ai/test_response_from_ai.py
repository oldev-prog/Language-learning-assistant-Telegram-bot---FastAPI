import pytest

@pytest.mark.asyncio
class TestAIClient:

    async def test_request_returns_correct_string(self, ai_client, user_state_ru):

        result = await ai_client.request(word="hello", user_state=user_state_ru)

        assert isinstance(result, dict)
        assert 'привет' in result['explanation_synonyms'].lower()
        assert 'здорова' in result['explanation_synonyms'].lower()
        assert 'здравствуйте' in result['explanation_synonyms'].lower()

    async def test_get_explanation_on_valid_resp(self, ai_client, user_state_ru):

        explanation, unswear = await ai_client.get_explanation(
            word="hello",
            user_state=user_state_ru
        )

        assert explanation == 'привет, здорова, здравствуйте'
        assert isinstance(unswear, dict)
        assert unswear['explanation_synonyms'] == 'привет, здорова, здравствуйте'

    async def test_if_same_language_true(self, mocker, user_state_ru, ai_client):

        data = {
            "lang_code": "ru",
            "translation": "hello"
        }

        word = "привет"

        mocker.patch(
            "app.bot.ai.open_ai.detect_same_language",
            return_value=True

        )

        mock_update_bd = mocker.patch("app.bot.ai.open_ai.update_bd")

        await ai_client.update_user_state(data, word, user_state_ru)

        assert user_state_ru.last_word == "hello"
        assert user_state_ru.last_translate == "привет"
        mock_update_bd.assert_called_once_with(user_state_ru)

    async def test_if_same_language_false(self, mocker, user_state_ru, ai_client):

        data = {
            "lang_code": "en",
            "translation": "привет"
        }

        word = "hello"

        mocker.patch(
            "app.bot.ai.open_ai.detect_same_language",
            return_value=False
        )

        mock_update_bd = mocker.patch("app.bot.ai.open_ai.update_bd")

        await ai_client.update_user_state(data, word, user_state_ru)

        assert user_state_ru.last_word == "hello"
        assert user_state_ru.last_translate == "привет"
        mock_update_bd.assert_called_once_with(user_state_ru)