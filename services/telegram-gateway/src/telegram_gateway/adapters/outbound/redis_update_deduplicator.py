from redis.asyncio import Redis


class RedisTelegramUpdateDeduplicator:
    def __init__(
        self,
        *,
        redis: Redis,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def mark_processing_started(
        self,
        update_id: int,
    ) -> bool:
        return bool(
            await self._redis.set(
                self._key(update_id),
                "1",
                nx=True,
                ex=self._ttl_seconds,
            )
        )

    def _key(self, update_id: int) -> str:
        return f"telegram_gateway:telegram_update:{update_id}"
