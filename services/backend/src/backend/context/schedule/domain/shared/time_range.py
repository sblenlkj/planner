from __future__ import annotations

from dataclasses import dataclass

from .local_time import LocalTime


@dataclass(frozen=True)
class LocalTimeRange:
    start_time: LocalTime
    end_time: LocalTime

    def __post_init__(self) -> None:
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time")

    def overlaps(self, other: LocalTimeRange) -> bool:
        return self.start_time < other.end_time and other.start_time < self.end_time

    def contains(self, value: LocalTime) -> bool:
        return self.start_time <= value < self.end_time
