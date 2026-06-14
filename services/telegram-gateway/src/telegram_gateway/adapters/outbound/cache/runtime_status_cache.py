from uuid import UUID

from redis.asyncio import Redis

from telegram_gateway.application.ports.backend_client import UserRuntimeStatus
from telegram_gateway.application.ports.runtime_status_cache import RuntimeStatusCache


class RedisRuntimeStatusCache(RuntimeStatusCache):
    def __init__(
        self,
        *,
        redis: Redis,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def get_status(
        self,
        business_user_id: UUID,
    ) -> UserRuntimeStatus | None:
        raw_value = await self._redis.get(self._key(business_user_id))

        if raw_value is None:
            return None

        return UserRuntimeStatus(raw_value)

    async def set_status(
        self,
        business_user_id: UUID,
        status: UserRuntimeStatus,
    ) -> None:
        await self._redis.set(
            self._key(business_user_id),
            status.value,
            ex=self._ttl_seconds,
        )

    async def clear_status(self, business_user_id: UUID) -> None:
        await self._redis.delete(self._key(business_user_id))

    def _key(self, business_user_id: UUID) -> str:
        return f"tg:cache:user_status:{business_user_id}"
