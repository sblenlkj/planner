from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from direttore import Validatable

from backend.context.course.domain.value_objects import CourseTaskProgress


@dataclass(eq=False, kw_only=True)
class CourseTaskObservation(Validatable):
    id: UUID
    task_id: UUID
    title: str
    description: str
    progress: CourseTaskProgress | None = None

    @classmethod
    def create(
        cls,
        *,
        task_id: UUID,
        title: str,
        description: str,
        progress: CourseTaskProgress | None = None,
        id: UUID | None = None,
    ) -> "CourseTaskObservation":
        return cls(
            id=id or uuid4(),
            task_id=task_id,
            title=cls._normalize_required_text(
                title,
                "Course task observation title",
            ),
            description=cls._normalize_required_text(
                description,
                "Course task observation description",
            ),
            progress=progress,
        )

    def validate_invariants(self) -> Self:
        self._validate_required_text(
            self.title,
            "Course task observation title",
        )
        self._validate_required_text(
            self.description,
            "Course task observation description",
        )
        return self

    def rename(self, title: str) -> None:
        self.title = self._normalize_required_text(
            title,
            "Course task observation title",
        )

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required_text(
            description,
            "Course task observation description",
        )

    def change_progress(self, progress: CourseTaskProgress | None) -> None:
        self.progress = progress

    @classmethod
    def _normalize_required_text(cls, value: str, field_name: str) -> str:
        value = value.strip()
        cls._validate_required_text(value, field_name)
        return value

    @staticmethod
    def _validate_required_text(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} is required.")