from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from direttore import SimpleAggregateRoot, Validatable

from backend.context.course.domain.value_objects import (
    CourseStatus,
    transition_course_status,
)


@dataclass(eq=False, kw_only=True)
class Course(SimpleAggregateRoot, Validatable):
    user_id: UUID
    title: str
    description: str
    status: CourseStatus = CourseStatus.ACTIVE

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        title: str,
        description: str,
        id: UUID | None = None,
    ) -> "Course":
        return cls(
            id=id or uuid4(),
            user_id=user_id,
            title=cls._normalize_required_text(title, "Course title"),
            description=cls._normalize_required_text(
                description,
                "Course description",
            ),
            status=CourseStatus.ACTIVE,
        )

    def validate_invariants(self) -> Self:
        self._validate_required_text(self.title, "Course title")
        self._validate_required_text(self.description, "Course description")
        return self

    def rename(self, title: str) -> None:
        self.title = self._normalize_required_text(title, "Course title")

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required_text(
            description,
            "Course description",
        )

    def complete(self) -> None:
        self.status = transition_course_status(
            current=self.status,
            target=CourseStatus.COMPLETED,
        )

    def archive(self) -> None:
        self.status = transition_course_status(
            current=self.status,
            target=CourseStatus.ARCHIVED,
        )

    def reactivate(self) -> None:
        self.status = transition_course_status(
            current=self.status,
            target=CourseStatus.ACTIVE,
        )

    @classmethod
    def _normalize_required_text(cls, value: str, field_name: str) -> str:
        value = value.strip()
        cls._validate_required_text(value, field_name)
        return value

    @staticmethod
    def _validate_required_text(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} is required.")