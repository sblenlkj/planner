from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class UpdateUserDTO:
    user_id: UUID
    login: str | None = None
    name: str | None = None
    language: str | None = None
    utc_offset_minutes: int | None = None
    region: str | None = None