from __future__ import annotations

from dataclasses import dataclass

from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind


@dataclass(frozen=True, kw_only=True)
class TimeBlockInput:
    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None = None