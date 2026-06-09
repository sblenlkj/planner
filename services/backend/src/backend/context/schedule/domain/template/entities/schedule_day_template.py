from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ..value_objects import Weekday
from .day_marker import DayMarker
from .time_block import TimeBlock


@dataclass(kw_only=True, slots=True)
class ScheduleDayTemplate:
    """
    Template entity for one weekday inside a WeeklyScheduleTemplate.

    ScheduleDayTemplate belongs to the template subdomain. It represents the
    ordinary structure of one weekday in the user's repeating weekly schedule.

    The entity identity is composite: weekly_schedule_template_id + weekday.
    It does not need its own UUID because the same weekly template can have
    exactly one Monday, one Tuesday, and so on.

    The day template owns two different collections:

    - time_blocks: hard or semi-hard time-state blocks such as sleep, free,
      busy, limited, and blocked time. These blocks must not overlap inside
      one day template.

    - markers: soft preferred windows such as meal, exercise, family, personal
      time, or custom intentions. Markers may overlap with time blocks and with
      other markers because they are interpreted later by the planner.

    This model describes the ordinary recurring week. It does not contain
    concrete dates, generated activities, future date-specific exceptions, or
    reminders/deadlines.
    """

    weekly_schedule_template_id: UUID
    weekday: Weekday
    time_blocks: list[TimeBlock] = field(default_factory=list)
    markers: list[DayMarker] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.weekday, Weekday):
            raise ValueError("weekday must be Weekday")

        self._validate_time_blocks(self.time_blocks)

        self.time_blocks = sorted(self.time_blocks, key=lambda item: item.start_time)
        self.markers = sorted(self.markers, key=lambda item: item.preferred_start_time)

    @property
    def identity(self) -> tuple[UUID, Weekday]:
        return self.weekly_schedule_template_id, self.weekday

    def add_time_block(self, block: TimeBlock) -> None:
        self._validate_new_time_block(block)
        self.time_blocks.append(block)
        self.time_blocks.sort(key=lambda item: item.start_time)

    def remove_time_block(self, block_id: UUID) -> None:
        self.time_blocks = [block for block in self.time_blocks if block.id != block_id]

    def replace_time_blocks(self, blocks: list[TimeBlock]) -> None:
        self._validate_time_blocks(blocks)
        self.time_blocks = sorted(blocks, key=lambda item: item.start_time)

    def add_marker(self, marker: DayMarker) -> None:
        self.markers.append(marker)
        self.markers.sort(key=lambda item: item.preferred_start_time)

    def remove_marker(self, marker_id: UUID) -> None:
        self.markers = [marker for marker in self.markers if marker.id != marker_id]

    def replace_markers(self, markers: list[DayMarker]) -> None:
        self.markers = sorted(markers, key=lambda item: item.preferred_start_time)

    def _validate_new_time_block(self, block: TimeBlock) -> None:
        for existing in self.time_blocks:
            if existing.id != block.id and existing.overlaps(block):
                raise ValueError("time blocks must not overlap inside one day template")

    def _validate_time_blocks(self, blocks: list[TimeBlock]) -> None:
        sorted_blocks = sorted(blocks, key=lambda item: item.start_time)

        for previous, current in zip(sorted_blocks, sorted_blocks[1:]):
            if previous.overlaps(current):
                raise ValueError("time blocks must not overlap inside one day template")