from typing import Set
from app.bot.youtube_parsing.key_managers import KeyManager, ProxyManager
import asyncio
from isodate import parse_duration
from app.bot.youtube_parsing.youtube_config import youtube_keys, proxies
from app.bot.youtube_parsing.youtube_config import proxy_factory, youtube_factory
import logging
from app.data.cache.redis_crud import *
from app.decorators import log_calls, except_timeout, send_action, sync_log_calls
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api.proxies import WebshareProxyConfig
from app.data.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.telegram_utils.utils import send_message, update_bd
from httpx import AsyncClient
from app.data.cache.redis_crud import *

logger = logging.getLogger(__name__)

class YouTubeParsing:
    def __init__(self):
        self.youtube_manager = KeyManager(youtube_keys, youtube_factory)
        self.proxy_manager = ProxyManager(proxies)


    @staticmethod
    def is_valid_video(video_snippet: dict, seen_ids: list[str]) -> list|None:

        rows = []

        for item in video_snippet.get('items', []):
            if item['id'] in seen_ids:
                continue

            seen_ids.append(item['id'])

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

    @sync_log_calls
    def search_video(self,
            chat_id: int,
            word: str,
            seen_ids: list[str],
            max_results: int = 20
            ) -> list[dict]:

        collected = 0
        rows = []
        token = None
        page = 0

        while len(rows) < max_results and page < 3:
            page += 1

            search_response = self.youtube_manager.execute(
                lambda service: service.search().list(
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


            logger.debug('searching response: %s', search_response)
            videos = [
                item.get('id', {}).get('videoId')
                for item in search_response.get('items', [])
                if item.get('id', {}).get('videoId')
            ]
            logger.info('found videos: %s', videos)

            if not videos:
                break

            video_response = self.youtube_manager.execute(
                lambda service: service.videos().list(
                    id=",".join(videos),
                    part="snippet,contentDetails,status,statistics"
                ).execute(),
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
            print(f'final result for videos: {rows}')

        return rows


    def fetch_transcript(self, video_id: str, lang_code: str):
        def task(proxy_url: str):
            print('fetching transcript start')

            # api = YouTubeTranscriptApi(
            #     proxy_config=GenericProxyConfig(http_url=proxy_url)
            # )

            api = YouTubeTranscriptApi()

            # api = YouTubeTranscriptApi(
            #     proxy_config=WebshareProxyConfig(
            #         proxy_username="kshvnjqs",
            #         proxy_password="vi9szjouaabo",
            #     )
            # )

            links = []

            try:
                transcript_list = api.list(video_id)

                for method in ['find_generated_transcript', 'find_manually_created_transcript']:
                    try:
                        transcript = getattr(transcript_list, method)([lang_code])
                        print(f'found transcript: {transcript}')

                        links.append(transcript)

                    except Exception as e:
                        logger.error(f'failed to fetch transcript: {e}')
                        continue

                logger.info('found transcripts: %s', links)
                print(f'found transcripts: {links}')
                return links

            except Exception as e:
                logger.error("Transcript fetch error: %s", e)
                return None

        return self.proxy_manager.execute(task)

    @sync_log_calls
    def get_link(self, chat_id: int, video_id: str, word: str, lang_code: str):

        links = self.fetch_transcript(video_id, lang_code)

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


    def run_parsing(self,
                          word: str,
                          chat_id: int,
                          lang_code: str,
                          seen_ids: list[str],
                          max_results: int = 20
                          ):
        print('run_parsing start')
        def search_link():
            print('search link start')
            try:
                videos = self.search_video(chat_id, word, seen_ids, max_results)
                logger.info('searched video: %s', videos)

                for video in videos:
                    link = self.get_link(chat_id, video['video_id'], word, lang_code)

                    if link:
                        logger.info('found link: %s', link)
                        redis_set_hash(chat_id=chat_id, word=word, lang=lang_code,
                                       field='youtube_link', data=link)
                        return link
                    else:
                        redis_set_hash(chat_id=chat_id, word=word, lang=lang_code,
                                       field='youtube_link', data='video not found')
                        return None

            except Exception as e:
                logger.exception('failed to fetch link: %s', e)
                redis_set_hash(chat_id=chat_id, word=word, lang=lang_code, field='youtube_link', data='error')
                return 'error'


        link = redis_get_hash(chat_id=chat_id, word=word, lang=lang_code, field='youtube_link')
        print(f'link from redis: {link}') if link else print(f'link from redis: {None}')

        if link is None:
            link = search_link()
            return link
        elif link.decode('utf-8') == 'error' or link.decode('utf-8') == 'video not found':
            link = search_link()
            return link
        else:
            return link


    @send_action(0, 'upload_video')
    async def send_result(self, chat_id: int, user_state: User, db: AsyncSession, client: AsyncClient):

        word = user_state.last_word
        if not word:
            await send_message(chat_id, 'First, send the word.', user_state, client)
            return {'details': 'there are not any words yet'}

        lang_code = user_state.lang_code
        user_state.state = 'await_response'
        await update_bd(user_state, db)

        try:
            result = None
            seen_videos = []
            count = 0

            while not result and count < 15:

                result_from_redis = redis_get_hash(chat_id=chat_id, word=word,
                                        lang=lang_code, field='youtube_link')
                print(f'result_from_redis: {result_from_redis}')

                if result_from_redis.decode('utf-8') == 'video not found' or result_from_redis.decode('utf-8') == 'error':
                    link = await asyncio.to_thread(self.run_parsing, word=word, chat_id=chat_id,
                                                             lang_code=lang_code, seen_ids=seen_videos)
                    if link is None:
                        result = 'video not found.'
                    elif link == 'error':
                        result = 'video search is currently unavailable, please try again later'
                    else:
                        result = link
                elif result_from_redis is None:
                    count += 1
                    await asyncio.sleep(1)
                    continue
                else:
                    result = result_from_redis.decode('utf-8')

                count += 1

                await asyncio.sleep(1)

            if count > 14:
                await send_message(chat_id, 'The server timed out waiting for a response, please try again later.', user_state, client)
            else:
                await send_message(chat_id, f'Videos found with this word: {result}', user_state, client)

        except Exception as e:
            logger.exception('Error: %s', e)
            await send_message(chat_id, 'Video search is currently unavailable. Please try again later.', user_state, client)
        finally:
            user_state.state = 'ready'

            await update_bd(user_state, db)
