import pytest
from unittest.mock import call
from unittest.mock import mock_open, Mock


class TestPronunciation:
    @pytest.mark.asyncio
    async def test_generate_tts_creates_file(self, pronunciation, mock_gtts, mock_file_ops):

        tmp_path = await pronunciation.generate_tts(word='hello', lang='en')

        assert tmp_path.startswith('/tmp/fake_voice_')
        assert tmp_path.endswith('.mp3')

        mock_gtts.assert_called_once_with(text='hello', lang='en')

        mock_gtts.return_value.write_to_fp.assert_called_once()

    def test_synthesize_writes_to_file(self, pronunciation, mock_gtts, monkeypatch):

        m = mock_open()
        monkeypatch.setattr('builtins.open', m)
        pronunciation.synthesize(tmp_path='/tmp/test.mp3', word='hello', lang='en')
        mock_gtts.assert_called_once_with(text='hello', lang='en')
        m.assert_called_once_with('/tmp/test.mp3', 'wb')

        tts_instance = mock_gtts.return_value
        handle = m()

        tts_instance.write_to_fp.assert_called_once_with(handle)

    @pytest.mark.asyncio
    async def test_send_voice_success(self, pronunciation, mock_httpx_client, mock_file_ops, send_voice_url):

        mock_httpx_client.post.return_value.json.return_value = {'ok': True}

        await pronunciation.send_voice(chat_id=123, word='hello', lang='en')

        mock_httpx_client.post.assert_called_once()
        args, kwargs = mock_httpx_client.post.call_args

        assert kwargs['url'] == 'https://api.telegram.org/botTOKEN/sendVoice'
        assert kwargs['data'] == {'chat_id': 123}

        files = kwargs['files']

        assert files['voice'][0] == 'hello.mp3'
        assert files['voice'][2] == 'audio/mpeg'
        assert len(mock_file_ops) == 1
        assert mock_file_ops[0].endswith('.mp3')

    @pytest.mark.asyncio
    async def test_send_voice_network_error(self, pronunciation, mock_httpx_client, mock_file_ops, caplog):

        mock_httpx_client.post.side_effect = Exception('Network error')

        with pytest.raises(Exception):
            await pronunciation.send_voice(chat_id=123, word='hello', lang='en')

        assert "voice message wasn't sent" in caplog.text
        assert len(mock_file_ops) == 1

    @pytest.mark.asyncio
    async def test_send_voice_filename_uses_word(self, pronunciation, mock_httpx_client):

        await pronunciation.send_voice(chat_id=123, word='привет', lang='en')

        files = mock_httpx_client.post.call_args[1]['files']

        assert files['voice'][0] == 'привет.mp3'