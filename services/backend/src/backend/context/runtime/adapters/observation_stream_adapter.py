from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from redis.asyncio import Redis

from backend.context.runtime.application.ports.observation_stream_port import (
    ExtractedObservationReadModel,
    ObservationBatchToPublish,
    ObservationStreamPort,
    PublishedObservationBatch,
)


RedisScalar = bytes | bytearray | memoryview | str
RedisFields = dict[RedisScalar, RedisScalar]


class RedisObservationStreamAdapter(ObservationStreamPort):
    def __init__(
        self,
        *,
        redis: Redis,
        extracted_observations_stream_name: str,
        observation_batch_ready_stream_name: str,
        read_offset_key: str,
        default_start_stream_id: str = "0-0",
    ) -> None:
        self._redis = redis
        self._input_stream = extracted_observations_stream_name
        self._output_stream = observation_batch_ready_stream_name
        self._read_offset_key = read_offset_key
        self._default_start_stream_id = default_start_stream_id

    async def read_new_extracted_observations(
        self,
        *,
        limit: int,
    ) -> tuple[ExtractedObservationReadModel, ...]:
        last_stream_id = await self._get_last_stream_id()

        rows = await self._redis.xrange(
            name=self._input_stream,
            min=f"({last_stream_id}",
            max="+",
            count=limit,
        )

        if not rows:
            return ()

        return tuple(
            self._decode_extracted_observation(
                stream_id=stream_id,
                fields=fields,
            )
            for stream_id, fields in rows
        )

    async def publish_observation_batch(
        self,
        batch: ObservationBatchToPublish,
    ) -> PublishedObservationBatch:
        event_id = uuid4()

        payload = {
            "event_id": str(event_id),
            "business_user_id": str(batch.business_user_id),
            "batch_date": batch.batch_date,
            "observations": list(batch.observations),
            "created_at": datetime.now(UTC).isoformat(),
        }

        stream_id = await self._redis.xadd(
            name=self._output_stream,
            fields={
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )

        return PublishedObservationBatch(
            stream_id=self._decode_stream_id(stream_id),
            business_user_id=batch.business_user_id,
            event_id=event_id,
        )

    async def commit_read_offset(
        self,
        *,
        stream_id: str,
    ) -> None:
        await self._redis.set(
            self._read_offset_key,
            stream_id,
        )

    async def _get_last_stream_id(self) -> str:
        value = await self._redis.get(self._read_offset_key)

        if value is None:
            return self._default_start_stream_id

        if isinstance(value, bytes):
            return value.decode("utf-8")

        return str(value)

    def _decode_extracted_observation(
        self,
        *,
        stream_id: RedisScalar | None,
        fields: RedisFields | None,
    ) -> ExtractedObservationReadModel:
        if stream_id is None or fields is None:
            raise ValueError(
                "Redis stream entry must have a stream ID and fields.",
            )
        decoded_stream_id = self._decode_stream_id(stream_id)
        payload = self._decode_payload(fields)

        return ExtractedObservationReadModel(
            stream_id=decoded_stream_id,
            event_id=UUID(payload["event_id"]),
            business_user_id=UUID(payload["business_user_id"]),
            source_session_event_id=(
                UUID(payload["source_session_event_id"])
                if payload.get("source_session_event_id")
                else None
            ),
            observed_at=(
                datetime.fromisoformat(payload["observed_at"])
                if payload.get("observed_at")
                else None
            ),
            observations=tuple(payload.get("observations", ())),
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

    @classmethod
    def _decode_payload(
        cls,
        fields: RedisFields,
    ) -> dict[str, Any]:
        normalized: dict[str, str] = {}

        for key, value in fields.items():
            normalized_key = cls._decode_redis_scalar(key)
            normalized_value = cls._decode_redis_scalar(value)

            normalized[normalized_key] = normalized_value

        raw_payload = normalized.get("payload")

        if raw_payload is None:
            return dict(normalized)

        decoded = json.loads(raw_payload)

        if not isinstance(decoded, dict):
            raise ValueError("Redis stream payload must be a JSON object.")

        return decoded

    @staticmethod
    def _decode_redis_scalar(
        value: RedisScalar,
    ) -> str:
        if isinstance(value, str):
            return value

        if isinstance(value, memoryview):
            return value.tobytes().decode("utf-8")

        return bytes(value).decode("utf-8")