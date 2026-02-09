from __future__ import annotations

import json
import redis
from app.core.config import settings

def get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)

def cache_get_json(key: str):
    val = get_redis().get(key)
    return None if val is None else json.loads(val)

def cache_set_json(key: str, obj, ttl_seconds: int = 60):
    get_redis().setex(key, ttl_seconds, json.dumps(obj))
