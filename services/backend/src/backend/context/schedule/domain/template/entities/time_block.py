from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...shared import LocalTime, LocalTimeRange, TimeBlockKind


@dataclass(kw_only=True, slots=True)
class TimeBlock:
    """
    Repeating weekly time-state block inside a ScheduleDayTemplate.

    TimeBlock belongs to the template subdomain. It describes what a part of
    the user's ordinary week looks like: free time, busy time, sleep, limited
    availability, or blocked time.

    This entity models the state of time, not an action. It should not be used
    for planned activities such as reading a course chapter, cooking breakfast,
    or completing a concrete task. Concrete planned actions belong to the
    execution subdomain as ScheduledActivity.

    BUSY is intentionally not split into structured subtypes. If the block
    means work, university, errands, or another kind of occupied time, that
    meaning should be expressed through title and description. TimeBlockKind
    stays small and algorithmic; title and description stay narrative and
    agent-facing.

    TimeBlock is repeated by weekday through ScheduleDayTemplate. When the
    planner generates a concrete ScheduleDay, template TimeBlock instances are
    copied into execution as ScheduledBlock snapshots. The generated day should
    not depend on the template after generation, because the template can change
    later.

    Time is stored as abstract local day time. There is no timezone conversion
    in this model. User timezone is resolved outside the domain model when
    application services convert user intent or scheduler operations.
    """

    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate()

    @property
    def time_range(self) -> LocalTimeRange:
        return LocalTimeRange(start_time=self.start_time, end_time=self.end_time)

    def overlaps(self, other: TimeBlock) -> bool:
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

    def _validate(self) -> None:
        LocalTimeRange(start_time=self.start_time, end_time=self.end_time)

        if not isinstance(self.kind, TimeBlockKind):
            raise ValueError("kind must be TimeBlockKind")

        self._validate_title(self.title)
        self.title = self.title.strip()

        if self.description is not None:
            self.description = self.description.strip()

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("title is required")