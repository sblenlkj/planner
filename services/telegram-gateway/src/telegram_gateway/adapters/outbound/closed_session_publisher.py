import json

from redis.asyncio import Redis

from telegram_gateway.application.ports.closed_session_publisher import (
    ClosedSessionPublisher,
)
from telegram_gateway.domain.events import ClosedSessionEvent, RedisStreamName


class RedisClosedSessionPublisher(ClosedSessionPublisher):
    def __init__(
        self,
        *,
        redis: Redis,
        maxlen: int | None = None,
    ) -> None:
        self._redis = redis
        self._maxlen = maxlen

    async def publish_closed_session(self, event: ClosedSessionEvent) -> None:
        payload = {
            "event_id": str(event.event_id),
            "business_user_id": str(event.business_user_id),
            "telegram_chat_id": event.telegram_chat_id,
            "closed_at": event.closed_at.isoformat(),
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in event.messages
            ],
        }

        await self._redis.xadd(
            RedisStreamName.TELEGRAM_SESSION_CLOSED.value,
            fields={"payload": json.dumps(payload, ensure_ascii=False)},
            maxlen=self._maxlen,
            approximate=True if self._maxlen is not None else False,
        )
