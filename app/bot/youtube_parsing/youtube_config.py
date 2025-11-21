import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

youtube_keys = [
        os.getenv('YOU_TUBE_KEY'),
        os.getenv('YOU_TUBE_KEY2'),
        os.getenv('YOU_TUBE_KEY3'),
        os.getenv('YOU_TUBE_KEY4'),
        os.getenv('YOU_TUBE_KEY5')
    ]


proxies = [
    os.getenv('PROXI_CONFIG1'),
    os.getenv('PROXI_CONFIG2'),
    os.getenv('PROXI_CONFIG3'),
    os.getenv('PROXI_CONFIG4'),
    os.getenv('PROXI_CONFIG5'),
    os.getenv('PROXI_CONFIG6'),
    os.getenv('PROXI_CONFIG7'),
    os.getenv('PROXI_CONFIG8'),
    os.getenv('PROXI_CONFIG9'),
    os.getenv('PROXI_CONFIG10'),
    os.getenv('PROXI_CONFIG11'),
]


def youtube_factory(api_key: str):
    return build('youtube', 'v3', developerKey=api_key)

def proxy_factory(proxy_config):
    ytt_api = YouTubeTranscriptApi(
        proxy_config=GenericProxyConfig(
            http_url=proxy_config,
        )
    )
    return ytt_api