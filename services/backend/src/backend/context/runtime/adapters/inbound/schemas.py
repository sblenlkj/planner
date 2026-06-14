from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class RequestDayGenerationHttpStatus(StrEnum):
    QUEUED = "queued"
    SKIPPED = "skipped"


class RequestDayGenerationRequest(BaseModel):
    business_user_id: UUID
    day: date


class RequestDayGenerationResponse(BaseModel):
    business_user_id: UUID
    day: date
    status: RequestDayGenerationHttpStatus
    reason: str | None = None
    stream_id: str | None = None
    event_id: UUID | None = None