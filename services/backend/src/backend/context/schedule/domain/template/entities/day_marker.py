from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...shared import LocalTime, LocalTimeRange
from ..value_objects import DayMarkerKind


@dataclass(kw_only=True, slots=True)
class DayMarker:
    """
    Repeating weekly soft marker inside a ScheduleDayTemplate.

    DayMarker belongs to the template subdomain. It represents a preferred,
    approximate, or habitual activity window inside an ordinary weekday.

    A marker is not the same thing as a TimeBlock. TimeBlock describes the
    state of time: free, busy, sleep, limited, blocked. DayMarker describes
    something the user usually wants to fit into the day: meal, exercise,
    family time, personal time, or another soft intention.

    Markers may overlap with TimeBlock instances and with other markers. This
    is intentional. A user may want lunch during work, exercise near office
    time, or family time around a busy evening. Whether the marker is realistic
    is planner reasoning, not a structural invariant of the template model.

    preferred_start_time and preferred_end_time are local abstract day times.
    The marker does not own timezone conversion and does not represent a
    concrete dated activity.
    """

    preferred_start_time: LocalTime
    preferred_end_time: LocalTime
    kind: DayMarkerKind
    title: str
    description: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate()

    @property
    def preferred_range(self) -> LocalTimeRange:
        return LocalTimeRange(
            start_time=self.preferred_start_time,
            end_time=self.preferred_end_time,
        )

    def rename(self, title: str) -> None:
        self._validate_title(title)
        self.title = title.strip()

    def change_description(self, description: str | None) -> None:
        self.description = description.strip() if description is not None else None

    def reschedule(
        self,
        preferred_start_time: LocalTime,
        preferred_end_time: LocalTime,
    ) -> None:
        LocalTimeRange(
            start_time=preferred_start_time,
            end_time=preferred_end_time,
        )
        self.preferred_start_time = preferred_start_time
        self.preferred_end_time = preferred_end_time

    def _validate(self) -> None:
        LocalTimeRange(
            start_time=self.preferred_start_time,
            end_time=self.preferred_end_time,
        )

        if not isinstance(self.kind, DayMarkerKind):
            raise ValueError("kind must be DayMarkerKind")

        self._validate_title(self.title)
        self.title = self.title.strip()

        if self.description is not None:
            self.description = self.description.strip()

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("title is required")