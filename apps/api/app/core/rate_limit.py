import time
from typing import Tuple
import redis

from app.core.config import get_settings

_settings = get_settings()

_client = redis.from_url(_settings.redis_url, decode_responses=True)


def _bucket_key(user_id: str) -> str:
    now = int(time.time()) // 60
    return f"rl:{user_id}:{now}"


def check_rate_limit(user_id: str) -> Tuple[bool, int]:
    key = _bucket_key(user_id)
    try:
        with _client.pipeline() as p:
            p.incr(key)
            p.expire(key, 90)
            count, _ = p.execute()
        allowed = int(count) <= _settings.rate_limit_requests_per_minute
        remaining = max(0, _settings.rate_limit_requests_per_minute - int(count))
        return allowed, remaining
    except Exception:
        return True, _settings.rate_limit_requests_per_minute