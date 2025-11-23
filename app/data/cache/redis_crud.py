from app.data.cache.redis_init import r
import json


def redis_get_hash(chat_id: int, word: str, lang: str, field: str):
    key = f'{chat_id}:{word}:{lang}'
    result = r.hget(key, field)

    if field == 'explanation' and result:
        result = json.loads(result)

    return result if result else None


def redis_set_hash(chat_id: int, word: str, lang: str, field: str, data: str|bytes|dict):
    key = f'{chat_id}:{word}:{lang}'
    if field == 'explanation':
        data = json.dumps(data)
    r.hset(key, field, data)
