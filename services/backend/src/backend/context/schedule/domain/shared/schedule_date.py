from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, order=True)
class ScheduleDate:
    """Local calendar date in the user's calendar."""

    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        # Validates calendar correctness, including leap years.
        date(self.year, self.month, self.day)

    @classmethod
    def from_date(cls, value: date) -> ScheduleDate:
        return cls(year=value.year, month=value.month, day=value.day)

    @classmethod
    def parse(cls, value: str) -> ScheduleDate:
        parsed = date.fromisoformat(value.strip())
        return cls.from_date(parsed)

    def to_date(self) -> date:
        return date(self.year, self.month, self.day)

    def __str__(self) -> str:
        return self.to_date().isoformat()
