from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...shared import LocalTime, LocalTimeRange, TimeBlockKind


@dataclass(kw_only=True, slots=True)
class ScheduledBlock:
    """
    Snapshot of a user's concrete day time context.

    ScheduledBlock belongs to the execution subdomain. It is usually produced
    by expanding a WeeklyScheduleTemplate into a concrete ScheduleDay. Unlike
    template TimeBlock, this entity is a historical/planning snapshot: after a
    ScheduleDay is generated, it should not depend on the template anymore.

    Blocks describe the structure of the day: sleep, free time, busy time,
    limited availability, blocked time, and similar time context. They are not
    planned actions. Planned actions are represented by ScheduledActivity.

    BUSY is intentionally not split into structured subtypes. If the block
    means work, university, errands, or another kind of occupied time, that
    meaning should be expressed through title and description. TimeBlockKind
    stays small and algorithmic; title and description stay narrative and
    agent-facing.

    The purpose of copying blocks into ScheduleDay is to make generated days
    stable. If the user later changes the weekly template, previously generated
    days still preserve the day context that was used when the plan was built.

    Time is stored as local abstract day time. The date is owned by the parent
    ScheduleDay. Timezone conversion is not performed here.
    """

    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        LocalTimeRange(start_time=self.start_time, end_time=self.end_time)

        if not isinstance(self.kind, TimeBlockKind):
            raise ValueError("kind must be TimeBlockKind")

        self._validate_title(self.title)
        self.title = self.title.strip()

        if self.description is not None:
            self.description = self.description.strip()

    @property
    def time_range(self) -> LocalTimeRange:
        return LocalTimeRange(start_time=self.start_time, end_time=self.end_time)

    def overlaps(self, other: ScheduledBlock) -> bool:
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

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("title is required")