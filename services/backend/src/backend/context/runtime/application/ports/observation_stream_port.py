from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class ExtractedObservationReadModel:
    stream_id: str
    event_id: UUID
    business_user_id: UUID
    source_session_event_id: UUID | None = None
    observed_at: datetime | None = None
    observations: tuple[dict[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True, kw_only=True, slots=True)
class ObservationBatchToPublish:
    business_user_id: UUID
    batch_date: str
    observations: tuple[dict[str, str], ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class PublishedObservationBatch:
    stream_id: str
    business_user_id: UUID
    event_id: UUID


class ObservationStreamPort(Protocol):
    async def read_new_extracted_observations(
        self,
        *,
        limit: int,
    ) -> tuple[ExtractedObservationReadModel, ...]:
        raise NotImplementedError

    async def publish_observation_batch(
        self,
        batch: ObservationBatchToPublish,
    ) -> PublishedObservationBatch:
        raise NotImplementedError

    async def commit_read_offset(
        self,
        *,
        stream_id: str,
    ) -> None:
        raise NotImplementedError