from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from redis.asyncio import Redis

from backend.context.runtime.application.ports.day_generation_stream_port import (
    DayGenerationRequestToPublish,
    DayGenerationStreamPort,
    PublishedDayGenerationRequest,
)

RedisScalar = bytes | bytearray | memoryview | str

class RedisDayGenerationStreamAdapter(DayGenerationStreamPort):
    def __init__(
        self,
        *,
        redis: Redis,
        day_generation_requested_stream_name: str,
    ) -> None:
        self._redis = redis
        self._stream_name = day_generation_requested_stream_name

    async def publish_day_generation_request(
        self,
        request: DayGenerationRequestToPublish,
    ) -> PublishedDayGenerationRequest:
        event_id = uuid4()

        payload = {
            "event_id": str(event_id),
            "business_user_id": str(request.user_id),
            "day": request.day.isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        }

        stream_id = await self._redis.xadd(
            name=self._stream_name,
            fields={
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )

        return PublishedDayGenerationRequest(
            stream_id=self._decode_stream_id(stream_id),
            event_id=event_id,
            user_id=request.user_id,
        )

    @staticmethod
    def _decode_stream_id(
        stream_id: RedisScalar,
    ) -> str:
        if isinstance(stream_id, str):
            return stream_id

        if isinstance(stream_id, memoryview):
            return stream_id.tobytes().decode("utf-8")

        return bytes(stream_id).decode("utf-8")