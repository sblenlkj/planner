from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class CourseTaskProgress:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0 or self.value > 100:
            raise ValueError("Course task progress must be between 0 and 100.")

    @classmethod
    def zero(cls) -> "CourseTaskProgress":
        return cls(value=0)

    @classmethod
    def complete(cls) -> "CourseTaskProgress":
        return cls(value=100)

    @classmethod
    def percent(cls, value: int) -> "CourseTaskProgress":
        return cls(value=value)

    @property
    def is_zero(self) -> bool:
        return self.value == 0

    @property
    def is_started(self) -> bool:
        return self.value > 0

    @property
    def is_complete(self) -> bool:
        return self.value == 100