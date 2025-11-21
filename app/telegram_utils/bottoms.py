import httpx

from app.config import send_msg_url

LANGUAGES = {
    'english': 'en',
    'french': 'fr',
    'japanese': 'ja',
    'korean': 'ko',
    'russian': 'ru',
    'spanish': 'es',
    'italian': 'it',
    'german': 'de',
    'portuguese': 'pt',
    'chinese': 'zh',
    'arabic': 'ar',
    'hindi': 'hi',
    'bengali': 'bn',
    'turkish': 'tr',
    'vietnamese': 'vi',
    'thai': 'th',
    'polish': 'pl',
    'ukrainian': 'uk',
    'malay': 'ms',
    'swahili': 'sw',
    'greek': 'el',
    'romanian': 'ro',
    'latin': 'la',
    'norwegian': 'no'
}


lang_bottoms = [
    [{'text': 'english'}, {'text': 'french'}, {'text': 'japanese'}, {'text': 'korean'}],
    [{'text': 'russian'}, {'text': 'spanish'}, {'text': 'italian'}, {'text': 'german'}],
    [{'text': 'portuguese'}, {'text': 'chinese'}, {'text': 'arabic'}, {'text': 'hindi'}],
    [{'text': 'bengali'}, {'text': 'turkish'}, {'text': 'vietnamese'}, {'text': 'thai'}],
    [{'text': 'polish'}, {'text': 'ukrainian'}, {'text': 'malay'}, {'text': 'swahili'}],
    [{'text': 'greek'}, {'text': 'romanian'}, {'text': 'latin'}, {'text': 'norwegian'}]
]

review_bottoms = [
                [{'text': 'forgot'}, {'text': 'hard'}],
                [{'text':'easy'}, {'text': 'perfect'}],
                [{'text':'finish repeating'}]
            ]

explain_bottoms = [
                [{'text': 'Pronunciation', 'callback_data': 'pronounce'}, {'text': 'Video YouTube', 'callback_data': 'youtube'}],
]


async def send_keyboard(chat_id: int, bottoms, close_or_no : bool = False, text : str = None):
    keyboard = {
            'keyboard': bottoms,
            'resize_keyboard': True,
            'one_time_keyboard': close_or_no
        }

    payload = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': keyboard
        }

    async with httpx.AsyncClient() as client:
        await client.post(send_msg_url, json=payload)

async def send_inline_keyboard(chat_id: int, bottoms, close_or_no: bool = False, text: str = None):
    keyboard = {
        'inline_keyboard': bottoms,
    }

    payload = {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': keyboard
    }

    async with httpx.AsyncClient() as client:
        await client.post(send_msg_url, json=payload)