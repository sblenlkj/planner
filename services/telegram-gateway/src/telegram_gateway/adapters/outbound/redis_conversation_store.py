import json
from uuid import UUID

from redis.asyncio import Redis

from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.domain.models import ConversationMessage, ConversationMessageRole


class RedisConversationStore(ConversationStore):
    def __init__(
        self,
        *,
        redis: Redis,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def append_message(
        self,
        business_user_id: UUID,
        message: ConversationMessage,
    ) -> list[ConversationMessage]:
        key = self._key(business_user_id)

        await self._redis.rpush(
            key,
            json.dumps(
                {
                    "role": message.role.value,
                    "content": message.content,
                },
                ensure_ascii=False,
            ),
        )
        await self._redis.expire(key, self._ttl_seconds)

        return await self.get_messages(business_user_id)

    async def get_messages(
        self,
        business_user_id: UUID,
    ) -> list[ConversationMessage]:
        values = await self._redis.lrange(self._key(business_user_id), 0, -1)

        messages: list[ConversationMessage] = []
        for value in values:
            if isinstance(value, bytes):
                value = value.decode("utf-8")

            payload = json.loads(value)
            messages.append(
                ConversationMessage(
                    role=ConversationMessageRole(payload["role"]),
                    content=payload["content"],
                )
            )

        return messages

    async def clear_messages(
        self,
        business_user_id: UUID,
    ) -> None:
        await self._redis.delete(self._key(business_user_id))

    def _key(
        self,
        business_user_id: UUID,
    ) -> str:
        return f"telegram_gateway:session:{business_user_id}"
