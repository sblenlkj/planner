from redis.asyncio import Redis


class TelegramUpdateDeduplicator:
    def __init__(self, *, redis: Redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def is_duplicate(self, update_id: int) -> bool:
        key = f"tg:idempotency:update:{update_id}"
        was_set = await self._redis.set(key, "1", ex=self._ttl_seconds, nx=True)
        return not bool(was_set)
