from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID

from backend.context.runtime.application.ports.day_generation_stream_port import (
    DayGenerationRequestToPublish,
    DayGenerationStreamPort,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    ScheduleRuntimePort,
)


class DayGenerationRequestStatus(StrEnum):
    PUBLISHED = "published"
    SKIPPED_ALREADY_EXISTS = "skipped_already_exists"


@dataclass(frozen=True, kw_only=True, slots=True)
class DayGenerationRequestResult:
    user_id: UUID
    day: date
    status: DayGenerationRequestStatus
    stream_id: str | None = None
    event_id: UUID | None = None


class DayGenerationRequestService:
    def __init__(
        self,
        *,
        schedule_runtime_port: ScheduleRuntimePort,
        day_generation_stream_port: DayGenerationStreamPort,
    ) -> None:
        self._schedule_runtime_port = schedule_runtime_port
        self._day_generation_stream_port = day_generation_stream_port

    async def request_generation_if_missing(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> DayGenerationRequestResult:
        exists = await self._schedule_runtime_port.schedule_day_exists(
            user_id=user_id,
            day=day,
        )

        if exists:
            return DayGenerationRequestResult(
                user_id=user_id,
                day=day,
                status=DayGenerationRequestStatus.SKIPPED_ALREADY_EXISTS,
            )

        published = await self._day_generation_stream_port.publish_day_generation_request(
            DayGenerationRequestToPublish(
                user_id=user_id,
                day=day,
            )
        )

        return DayGenerationRequestResult(
            user_id=user_id,
            day=day,
            status=DayGenerationRequestStatus.PUBLISHED,
            stream_id=published.stream_id,
            event_id=published.event_id,
        )