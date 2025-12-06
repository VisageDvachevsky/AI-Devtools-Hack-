import logging
from typing import Optional

import redis.asyncio as redis

from backend.core.config import settings

logger = logging.getLogger(__name__)


_redis_client: Optional[redis.Redis] = None
_redis_disabled: bool = False


def get_redis() -> Optional[redis.Redis]:
    """Возвращает лениво инициализированный Redis client. При ошибке вернёт None."""
    global _redis_client, _redis_disabled  # noqa: PLW0603
    if _redis_disabled:
        return None
    if _redis_client:
        return _redis_client
    try:
        _redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        return _redis_client
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable, caching disabled: %s", exc)
        _redis_disabled = True
        return None


async def cache_get(key: str) -> Optional[dict]:
    client = get_redis()
    if not client:
        return None
    try:
        raw = await client.get(key)
        if raw:
            import json

            return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis get failed for %s: %s; disabling cache", key, exc)
        global _redis_disabled  # noqa: PLW0603
        _redis_disabled = True
    return None


async def cache_set(key: str, value: dict, ttl_seconds: int = 600) -> None:
    client = get_redis()
    if not client:
        return
    try:
        import json

        await client.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis set failed for %s: %s; disabling cache", key, exc)
        global _redis_disabled  # noqa: PLW0603
        _redis_disabled = True
