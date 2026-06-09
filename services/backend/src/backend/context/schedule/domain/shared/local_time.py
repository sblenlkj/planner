from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class LocalTime:
    """Abstract local time without date and timezone."""

    hour: int
    minute: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.hour <= 23:
            raise ValueError("hour must be between 0 and 23")
        if not 0 <= self.minute <= 59:
            raise ValueError("minute must be between 0 and 59")

    @classmethod
    def parse(cls, value: str) -> LocalTime:
        parts = value.strip().split(":")
        if len(parts) != 2:
            raise ValueError("local time must have HH:MM format")
        return cls(hour=int(parts[0]), minute=int(parts[1]))

    def to_minutes(self) -> int:
        return self.hour * 60 + self.minute

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"
