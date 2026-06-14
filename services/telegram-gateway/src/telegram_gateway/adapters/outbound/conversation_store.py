import json

from redis.asyncio import Redis

from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.domain.models import ConversationMessage, ConversationMessageRole


class RedisConversationStore(ConversationStore):
    def __init__(
        self,
        *,
        redis: Redis,
        conversation_ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._conversation_ttl_seconds = conversation_ttl_seconds

    async def get_messages(self, telegram_chat_id: int) -> list[ConversationMessage]:
        raw_items = await self._redis.lrange(self._key(telegram_chat_id), 0, -1)
        return [self._decode_message(raw_item) for raw_item in raw_items]

    async def append_message(
        self,
        telegram_chat_id: int,
        message: ConversationMessage,
    ) -> None:
        key = self._key(telegram_chat_id)
        await self._redis.rpush(key, self._encode_message(message))
        await self._redis.expire(key, self._conversation_ttl_seconds)

    async def clear_messages(self, telegram_chat_id: int) -> None:
        await self._redis.delete(self._key(telegram_chat_id))

    def _key(self, telegram_chat_id: int) -> str:
        return f"tg:conversation:chat:{telegram_chat_id}"

    def _encode_message(self, message: ConversationMessage) -> str:
        return json.dumps(
            {"role": message.role.value, "content": message.content},
            ensure_ascii=False,
        )

    def _decode_message(self, raw_item: str | bytes) -> ConversationMessage:
        if isinstance(raw_item, bytes):
            raw_item = raw_item.decode("utf-8")
        payload = json.loads(raw_item)
        return ConversationMessage(
            role=ConversationMessageRole(payload["role"]),
            content=payload["content"],
        )
