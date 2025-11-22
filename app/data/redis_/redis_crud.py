from app.data.redis_.redis_init import r
import json


def redis_get_hash(chat_id: int, field: str):
    result = r.hget(chat_id, field)
    return result if result else None


def redis_set_hash(chat_id: int, field: str, data: str|bytes):
    r.hset(chat_id, field, data)