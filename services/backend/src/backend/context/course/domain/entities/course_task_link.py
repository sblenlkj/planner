from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from direttore import Validatable


@dataclass(eq=False, kw_only=True)
class CourseTaskLink(Validatable):
    id: UUID
    task_id: UUID
    description: str
    url: str | None = None

    @classmethod
    def create(
        cls,
        *,
        task_id: UUID,
        description: str,
        url: str | None = None,
        id: UUID | None = None,
    ) -> "CourseTaskLink":
        return cls(
            id=id or uuid4(),
            task_id=task_id,
            description=cls._normalize_required_text(
                description,
                "Course task link description",
            ),
            url=cls._normalize_optional_text(url),
        )

    def validate_invariants(self) -> Self:
        self._validate_required_text(
            self.description,
            "Course task link description",
        )
        return self

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required_text(
            description,
            "Course task link description",
        )

    def change_url(self, url: str | None) -> None:
        self.url = self._normalize_optional_text(url)

    @classmethod
    def _normalize_required_text(cls, value: str, field_name: str) -> str:
        value = value.strip()
        cls._validate_required_text(value, field_name)
        return value

    @staticmethod
    def _validate_required_text(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} is required.")

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None