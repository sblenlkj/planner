from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class DayGenerationRequestToPublish:
    user_id: UUID
    day: date


@dataclass(frozen=True, kw_only=True, slots=True)
class PublishedDayGenerationRequest:
    stream_id: str
    event_id: UUID
    user_id: UUID


class DayGenerationStreamPort(Protocol):
    async def publish_day_generation_request(
        self,
        request: DayGenerationRequestToPublish,
    ) -> PublishedDayGenerationRequest:
        raise NotImplementedError