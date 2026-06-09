from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class CourseTaskPriority:
    value: int

    def __post_init__(self) -> None:
        if self.value not in {1, 2, 3}:
            raise ValueError("Course task priority must be 1, 2, or 3.")

    @classmethod
    def low(cls) -> "CourseTaskPriority":
        return cls(value=1)

    @classmethod
    def normal(cls) -> "CourseTaskPriority":
        return cls(value=2)

    @classmethod
    def high(cls) -> "CourseTaskPriority":
        return cls(value=3)