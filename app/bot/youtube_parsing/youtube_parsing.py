from typing import Set
from app.bot.youtube_parsing.key_managers import KeyManager, ProxyManager
import asyncio
from isodate import parse_duration
from app.bot.youtube_parsing.youtube_config import youtube_keys, proxies
from app.bot.youtube_parsing.youtube_config import proxy_factory, youtube_factory
import logging
from app.data.redis_.redis_crud import set_hash, get_hash
from app.decorators import log_calls, except_timeout, send_action
from youtube_transcript_api import YouTubeTranscriptApi
from app.data.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.telegram_utils.utils import send_message, update_bd
from httpx import AsyncClient

logger = logging.getLogger(__name__)

class YouTubeParsing:
    def __init__(self):
        self.youtube_manager = KeyManager(youtube_keys, youtube_factory)
        self.proxy_manager = ProxyManager(proxies)


    @staticmethod
    def is_valid_video(video_snippet: dict, seen_ids: Set[str]) -> list|None:

        rows = []

        for item in video_snippet.get('items', []):
            if item['id'] in seen_ids:
                continue

            seen_ids.add(item['id'])

            snippet = item.get('snippet', {})
            content = item.get('contentDetails', {})
            title = snippet.get('title', '').lower()
            description = snippet.get('description', '').lower()
            live_status = snippet.get('liveBroadcastContent', 'none')
            category_id = snippet.get('categoryId', '')
            duration = parse_duration(content.get('duration', 'PT0S')).total_seconds()

            if live_status in {'live', 'upcoming'}:
                continue
            if category_id == '10':
                continue
            if any(word in title or word in description for word in
                   ['music video', 'lyrics', 'feat', 'official video', 'audio']):
                continue
            if duration < 60:
                continue

            rows.append({
                'video_id': item['id'],
                'title': snippet.get('title', '')
            })

        return rows

    @log_calls
    async def search_video(self,
            chat_id: int,
            word: str,
            seen_ids: Set[str],
            max_results: int = 20
            ) -> list[dict]:

        collected = 0
        rows = []
        token = None
        page = 0

        while len(rows) < max_results and page < 3:
            page += 1

            search_response = await self.youtube_manager.execute(
                lambda service: asyncio.to_thread(
                    lambda s=service: s.search().list(
                    q=word,
                    part="id",
                    type="video",
                    order="relevance",
                    videoCaption="closedCaption",
                    maxResults=min(50, max_results - collected),
                    pageToken=token or "",
                    safeSearch="none",
                    #units=100
                ).execute())
            )

            logger.debug('searching response: %s', search_response)
            videos = [
                item.get('id', {}).get('videoId')
                for item in search_response.get('items', [])
                if item.get('id', {}).get('videoId')
            ]
            logger.info('found videos: %s', videos)

            if not videos:
                break

            video_response = await self.youtube_manager.execute(
                lambda service: asyncio.to_thread(
                    lambda s=service: s.videos().list(
                        id=",".join(videos),
                        part="snippet,contentDetails,status,statistics"
                    ).execute()
                ),
                units=lambda response: len(response.get('items', []))
            )
            logger.debug('video response: %s', video_response)

            valid_videos = self.is_valid_video(video_response, seen_ids)
            rows.extend(valid_videos)

            collected = len(rows)

            if len(rows) >= max_results:
                rows = rows[:max_results]
                break

            token = search_response.get('nextPageToken') or None
            if not token:
                break

            logger.info('final result for videos: %s', rows)

        return rows


    async def fetch_transcript(self, video_id: str, lang_code: str):
        async def task(proxy_url: str):

            # api = YouTubeTranscriptApi(
            #     proxy_config=GenericProxyConfig(http_url=proxy_url)
            # )

            api = YouTubeTranscriptApi()

            links = []

            try:
                transcript_list = api.list(video_id)

                for method in ['find_generated_transcript', 'find_manually_created_transcript']:
                    try:
                        transcript = getattr(transcript_list, method)([lang_code])

                        links.append(transcript)

                    except Exception:
                       continue

                logger.info('found transcripts: %s', links)
                return links

            except Exception as e:
                logger.error("Transcript fetch error: %s", e)
                return None

        return await self.proxy_manager.execute(task)

    @log_calls
    async def get_link(self, chat_id: int, video_id: str, word: str, lang_code: str):

        links = await self.fetch_transcript(video_id, lang_code)

        if len(links) == 0:
            logger.error('empty links_list')
            return None

        data = links[0].fetch()

        if links[0].language_code != lang_code:
            return None
        else:
            for entry in data:
                if word.lower() in entry.text.lower():
                    start = int(entry.start)
                    return {
                        'url': f'https://youtu.be/{video_id}?t={start}'
                    }.get('url')


    async def run_parsing(self,
                          word: str,
                          chat_id: int,
                          lang_code: str,
                          seen_ids: Set[str],
                          max_results: int = 20
                          ):
        videos = await self.search_video(chat_id, word, seen_ids, max_results)
        logger.info('searched video: %s', videos)

        for video in videos:
            link = await self.get_link(chat_id, video['video_id'], word, lang_code)
            logger.info('found link: %s', link)

            if link:
                set_hash()

                return link

        return None

    @send_action(6, 'upload_video')
    async def send_result(self, chat_id: int, user_state: User, db: AsyncSession, client: AsyncClient):
        seen_videos = set()

        word = user_state.last_word
        if not word:
            await send_message(chat_id, 'First, send the word.', user_state, client)
            return {'details': "there aren't any words yet"}

        lang_code = user_state.lang_code
        user_state.state = 'await_response'
        await update_bd(user_state, db)

        try:
            logger.debug('calling run_parsing')
            link = await self.run_parsing(word, chat_id, lang_code, seen_videos, 10)
            logger.debug('run parsing result: %s', link)
            if not link:
                await send_message(chat_id, 'Video not found.', user_state, client)
            else:
                await send_message(chat_id, f'Videos found with this word:{link}', user_state, client)
        except Exception as e:
            logger.exception('Error: %s', e)
            await send_message(chat_id, f'Error searching for video.', user_state, client)
        finally:
            user_state.state = 'ready'

            await update_bd(user_state, db)


    #         if not success:
    #             await except_timeout(3, chat_id, user_state, send_message, chat_id, 'Видео не найдено.')
    #         else:
    #             await except_timeout(3, chat_id, user_state, send_message, chat_id,
    #                                  f'Найдено видео с данным словом:{link}')
    #     finally:
    #         user_state.state = 'ready'
    #         await update_bd(user_state)
    #
    # asyncio.create_task(run_video())
    # else:
    # await except_timeout(3, chat_id, user_state, send_message, chat_id, f'Найдено видео с данным словом:{link}')