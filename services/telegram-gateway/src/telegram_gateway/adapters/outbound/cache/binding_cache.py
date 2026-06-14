import json
from uuid import UUID

from redis.asyncio import Redis

from telegram_gateway.application.ports.binding_cache import BindingCache
from telegram_gateway.domain.models import TelegramBinding


class RedisBindingCache(BindingCache):
    def __init__(
        self,
        *,
        redis: Redis,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> TelegramBinding | None:
        return await self._get(self._telegram_user_key(telegram_user_id))

    async def get_by_business_user_id(
        self,
        business_user_id: UUID,
    ) -> TelegramBinding | None:
        return await self._get(self._business_user_key(business_user_id))

    async def get_by_telegram_chat_id(
        self,
        telegram_chat_id: int,
    ) -> TelegramBinding | None:
        return await self._get(self._telegram_chat_key(telegram_chat_id))

    async def set_binding(self, binding: TelegramBinding) -> None:
        payload = json.dumps(
            {
                "business_user_id": str(binding.business_user_id),
                "telegram_user_id": binding.telegram_user_id,
                "telegram_chat_id": binding.telegram_chat_id,
            }
        )
        await self._redis.set(
            self._telegram_user_key(binding.telegram_user_id),
            payload,
            ex=self._ttl_seconds,
        )
        await self._redis.set(
            self._business_user_key(binding.business_user_id),
            payload,
            ex=self._ttl_seconds,
        )
        await self._redis.set(
            self._telegram_chat_key(binding.telegram_chat_id),
            payload,
            ex=self._ttl_seconds,
        )

    async def _get(self, key: str) -> TelegramBinding | None:
        raw_value = await self._redis.get(key)

        if raw_value is None:
            return None

        payload = json.loads(raw_value)
        return TelegramBinding(
            business_user_id=UUID(payload["business_user_id"]),
            telegram_user_id=int(payload["telegram_user_id"]),
            telegram_chat_id=int(payload["telegram_chat_id"]),
        )

    def _telegram_user_key(self, telegram_user_id: int) -> str:
        return f"tg:cache:binding:telegram_user:{telegram_user_id}"

    def _business_user_key(self, business_user_id: UUID) -> str:
        return f"tg:cache:binding:business_user:{business_user_id}"

    def _telegram_chat_key(self, telegram_chat_id: int) -> str:
        return f"tg:cache:binding:chat:{telegram_chat_id}"
