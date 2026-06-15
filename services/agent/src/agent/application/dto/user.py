from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserProfileDto:
    """Compact user context consumed by agents and workflows."""

    user_id: UUID
    login: str | None
    name: str | None
    language: str | None
    utc_offset_minutes: int | None
    region: str | None
    runtime_status: str | None
