from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self
from uuid import UUID, uuid4

from direttore import Validatable

from backend.context.course.domain.entities.course_task_link import CourseTaskLink
from backend.context.course.domain.value_objects import (
    CourseTaskLink,
    CourseTaskPriority,
    CourseTaskProgress,
    CourseTaskStatus,
    transition_course_task_status,
)


@dataclass(eq=False, kw_only=True)
class CourseTask(Validatable):
    id: UUID
    course_id: UUID
    title: str
    description: str
    priority: CourseTaskPriority
    status: CourseTaskStatus
    progress: CourseTaskProgress
    next_task_id: UUID | None = None
    links: list[CourseTaskLink] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        course_id: UUID,
        title: str,
        description: str,
        priority: CourseTaskPriority | None = None,
        next_task_id: UUID | None = None,
        links: list[CourseTaskLink] | None = None,
        id: UUID | None = None,
    ) -> "CourseTask":
        return cls(
            id=id or uuid4(),
            course_id=course_id,
            title=cls._normalize_required_text(title, "Course task title"),
            description=cls._normalize_required_text(
                description,
                "Course task description",
            ),
            priority=priority or CourseTaskPriority.normal(),
            status=CourseTaskStatus.PENDING,
            progress=CourseTaskProgress.zero(),
            next_task_id=next_task_id,
            links=links or [],
        )

    def validate_invariants(self) -> Self:
        self._validate_required_text(self.title, "Course task title")
        self._validate_required_text(
            self.description,
            "Course task description",
        )

        if self.next_task_id == self.id:
            raise ValueError("Course task cannot reference itself as next task.")

        return self

    def rename(self, title: str) -> None:
        self.title = self._normalize_required_text(title, "Course task title")

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required_text(
            description,
            "Course task description",
        )

    def change_priority(self, priority: CourseTaskPriority) -> None:
        self.priority = priority

    def set_next_task(self, task_id: UUID | None) -> None:
        if task_id == self.id:
            raise ValueError("Course task cannot reference itself as next task.")

        self.next_task_id = task_id

    def add_link(
        self,
        *,
        description: str,
        url: str | None = None,
    ) -> CourseTaskLink:
        link = CourseTaskLink(
            description=description,
            url=url,
        )
        self.links.append(link)
        return link

    def remove_link(self, link: CourseTaskLink) -> None:
        self.links = [existing_link for existing_link in self.links if existing_link != link]

    def start(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.IN_PROGRESS,
        )

    def skip(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.SKIPPED,
        )

    def complete(self) -> None:
        self.progress = CourseTaskProgress.complete()
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.COMPLETED,
        )

    def reopen(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.IN_PROGRESS,
        )

    def change_progress(self, progress: CourseTaskProgress) -> None:
        self.progress = progress

        if progress.is_complete:
            self.status = transition_course_task_status(
                current=self.status,
                target=CourseTaskStatus.COMPLETED,
            )
            return

        if progress.is_started and self.status == CourseTaskStatus.PENDING:
            self.status = transition_course_task_status(
                current=self.status,
                target=CourseTaskStatus.IN_PROGRESS,
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