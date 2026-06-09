from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...shared import ScheduleDate


@dataclass(kw_only=True, slots=True)
class ScheduleDayObservation:
    """
    Day-local narrative observation about what actually happened.

    ScheduleDayObservation belongs to the execution subdomain. It records
    feedback, facts, and short narrative context reported by the user about a
    concrete generated day.

    This entity is different from ScheduleDay.description. The description on
    ScheduleDay is the generated plan narrative: what the system intended the
    day to be. ScheduleDayObservation.description is accumulated after
    generation: what the user actually did, missed, postponed, felt, or
    reported.

    Observations are intentionally lightweight text records. They do not update
    ScheduledActivity statuses and do not replace course progress, analytics
    signals, or graph memory. Application services may later use them as input
    for those contexts, but this entity itself remains local to schedule
    execution.

    The observation is identified by its own UUID, but it is attached to a
    concrete day through user_id and date.
    """

    user_id: UUID
    date: ScheduleDate
    description: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate_description(self.description)
        self.description = self.description.strip()

    def change_description(self, description: str) -> None:
        self._validate_description(description)
        self.description = description.strip()

    @staticmethod
    def _validate_description(description: str) -> None:
        if not description or not description.strip():
            raise ValueError("description is required")