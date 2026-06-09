from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...shared import LocalTime, LocalTimeRange


@dataclass(kw_only=True, slots=True)
class ScheduledActivity:
    """
    Concrete planned user action inside a generated ScheduleDay.

    ScheduledActivity belongs to the execution subdomain. It represents an
    action that the user is expected to do during a concrete generated day:
    read something, cook breakfast, work on a course task, go for a walk,
    prepare food, review material, or perform another concrete action.

    This entity is intentionally not a task tracker. It has no status and
    does not try to record whether the user completed, skipped, or missed the
    activity. If the user later reports meaningful progress, that information
    should be routed to the appropriate context: course for course progress,
    analytics for behavioral signals, or ScheduleDayObservation for day-level
    narrative feedback.

    course_task_id is optional. When present, it means that this scheduled
    activity is connected to a CourseTask from the course context. The schedule
    context stores only the foreign UUID reference and does not own or mutate
    the course task itself.

    Time is stored as local abstract day time. The date is owned by the parent
    ScheduleDay. Timezone conversion is not performed here.
    """

    start_time: LocalTime
    end_time: LocalTime
    title: str
    description: str | None = None
    course_task_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        LocalTimeRange(start_time=self.start_time, end_time=self.end_time)
        self._validate_title(self.title)
        self.title = self.title.strip()

        if self.description is not None:
            self.description = self.description.strip()

    @property
    def time_range(self) -> LocalTimeRange:
        return LocalTimeRange(start_time=self.start_time, end_time=self.end_time)

    def overlaps(self, other: ScheduledActivity) -> bool:
        return self.time_range.overlaps(other.time_range)

    def rename(self, title: str) -> None:
        self._validate_title(title)
        self.title = title.strip()

    def change_description(self, description: str | None) -> None:
        self.description = description.strip() if description is not None else None

    def reschedule(self, start_time: LocalTime, end_time: LocalTime) -> None:
        LocalTimeRange(start_time=start_time, end_time=end_time)
        self.start_time = start_time
        self.end_time = end_time

    def link_course_task(self, course_task_id: UUID) -> None:
        self.course_task_id = course_task_id

    def unlink_course_task(self) -> None:
        self.course_task_id = None

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("title is required")