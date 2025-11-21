import pytest
import httpx
from unittest.mock import MagicMock, call
from app.bot.youtube_parsing.youtube_parsing import YouTubeParsing
from unittest.mock import AsyncMock


class TestYouTubeParsing:

    def test_is_valid_video_filters_correctly(self):
        parsing = YouTubeParsing()

        video_snippet = {
            'items': [
                {
                    'id': 'valid1',
                    'snippet': {'title': 'Python Tutorial', 'description': '', 'liveBroadcastContent': 'none', 'categoryId': '27'},
                    'contentDetails': {'duration': 'PT15M'}
                },
                {
                    'id': 'live',
                    'snippet': {'liveBroadcastContent': 'live'}
                },
                {
                    'id': 'music',
                    'snippet': {'title': 'Official Music Video'}
                },
                {
                    'id': 'short',
                    'snippet': {'title': 'Quick Tip'},
                    'contentDetails': {'duration': 'PT30S'}
                },
                {
                    'id': 'category10',
                    'snippet': {'categoryId': '10'}
                }
            ]
        }

        seen_ids = set()
        rows = parsing.is_valid_video(video_snippet, seen_ids)

        assert len(rows) == 1
        assert rows[0]['video_id'] == 'valid1'
        assert rows[0]['title'] == 'Python Tutorial'
        assert 'valid1' in seen_ids


    @pytest.mark.asyncio
    async def test_search_video_returns_valid_videos(self, youtube_parsing, mock_key_manager, seen_ids):

        search_response = {
            'items': [{'id': {'videoId': 'vid1'}}, {'id': {'videoId': 'vid2'}}],
            'nextPageToken': None
        }
        video_response = {
            'items': [
                {
                    'id': 'vid1',
                    'snippet': {
                        'title': 'Valid Video',
                        'description': '',
                        'liveBroadcastContent': 'none',
                        'categoryId': '27'
                    },
                    'contentDetails': {'duration': 'PT2M'}
                }
            ]
        }

        mock_key_manager.execute.side_effect = [
            search_response,
            video_response
        ]

        result = await youtube_parsing.search_video('python', seen_ids, max_results=5)

        assert len(result) == 1
        assert result[0]['video_id'] == 'vid1'
        assert result[0]['title'] == 'Valid Video'


        assert mock_key_manager.execute.call_count == 2


    @pytest.mark.asyncio
    async def test_search_video_no_results(self, youtube_parsing, mock_key_manager, seen_ids):
        mock_key_manager.execute.return_value = {'items': []}

        result = await youtube_parsing.search_video('nonexistentword123', seen_ids)

        assert result == []
        mock_key_manager.execute.assert_called_once()



    @pytest.mark.asyncio
    async def test_fetch_transcript_success(self, youtube_parsing, mock_proxy_manager):
        transcript = MagicMock()
        transcript.language_code = 'en'
        transcript.fetch.return_value = [
            MagicMock(text='hello world', start=10.5)
        ]

        api_mock = youtube_parsing.ytt_api
        api_mock.list.return_value.find_generated_transcript.return_value = transcript

        mock_proxy_manager.execute.return_value = [transcript]

        result = await youtube_parsing.fetch_transcript('vid123', 'en')

        assert len(result) == 1
        assert result[0] == transcript



    @pytest.mark.asyncio
    async def test_fetch_transcript_no_transcript(self, youtube_parsing, mock_proxy_manager):
        api_mock = youtube_parsing.ytt_api
        api_mock.list.return_value.find_generated_transcript.side_effect = Exception()
        api_mock.list.return_value.find_manually_created_transcript.side_effect = Exception()

        mock_proxy_manager.execute.return_value = None

        result = await youtube_parsing.fetch_transcript('vid123', 'en')

        assert result is None



    @pytest.mark.asyncio
    async def test_get_link_word_found(self, youtube_parsing, mock_proxy_manager):
        transcript = MagicMock()
        transcript.language_code = 'en'
        transcript.fetch.return_value = [
            MagicMock(text='This is python tutorial', start=15.0)
        ]

        mock_proxy_manager.execute.return_value = [transcript]

        result = await youtube_parsing.get_link('vid123', 'python', 'en')

        assert result == 'https://youtu.be/vid123?t=15'



    @pytest.mark.asyncio
    async def test_get_link_wrong_language(self, youtube_parsing, mock_proxy_manager):
        transcript = MagicMock()
        transcript.language_code = 'ru'
        transcript.fetch.return_value = []

        mock_proxy_manager.execute.return_value = [transcript]

        result = await youtube_parsing.get_link('vid123', 'python', 'en')

        assert result is None



    @pytest.mark.asyncio
    async def test_get_link_word_not_found(self, youtube_parsing, mock_proxy_manager):
        transcript = MagicMock()
        transcript.language_code = 'en'
        transcript.fetch.return_value = [
            MagicMock(text='java tutorial', start=10.0)
        ]

        mock_proxy_manager.execute.return_value = [transcript]

        result = await youtube_parsing.get_link('vid123', 'python', 'en')

        assert result is None



    @pytest.mark.asyncio
    async def test_run_parsing_finds_link(self, youtube_parsing, mock_key_manager, mock_proxy_manager, seen_ids, monkeypatch):

        youtube_parsing.search_video = AsyncMock(return_value=[
            {'video_id': 'vid123', 'title': 'Python'}
        ])

        youtube_parsing.get_link = AsyncMock(return_value='https://youtu.be/vid123?t=30')

        result = await youtube_parsing.run_parsing('python', 'en', seen_ids)

        assert result == 'https://youtu.be/vid123?t=30'



    @pytest.mark.asyncio
    async def test_run_parsing_no_link_found(self, youtube_parsing, seen_ids):
        youtube_parsing.search_video = AsyncMock(return_value=[
            {'video_id': 'vid123', 'title': 'Python'}
        ])
        youtube_parsing.get_link = AsyncMock(return_value=None)

        result = await youtube_parsing.run_parsing('python', 'en', seen_ids)

        assert result is None