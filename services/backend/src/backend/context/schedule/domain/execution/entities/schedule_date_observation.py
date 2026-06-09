from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...shared import ScheduleDate


@dataclass(kw_only=True, slots=True)
class ScheduleDateObservation:
    """
    Future or date-specific schedule context.

    ScheduleDateObservation belongs to the execution subdomain, but it can
    exist before a ScheduleDay is generated. It stores concrete-date or
    date-range context that should be considered when the system later builds
    a generated day.

    This entity is used for user statements such as future plans, exceptions,
    one-off constraints, or date-specific intentions. It is not part of the
    weekly template because it does not describe a recurring ordinary week. It
    is also not a ScheduledActivity because the final generated activity may
    be decided later by the planner.

    The important distinction is:

    - ScheduleDateObservation stores future context before generation.
    - ScheduleDay.description stores the generated plan narrative.
    - ScheduleDayObservation stores what actually happened after generation.

    starts_on is required. ends_on is optional. When ends_on is absent, the
    observation applies only to starts_on. When ends_on is present, the
    observation applies to the inclusive date range from starts_on to ends_on.
    """

    user_id: UUID
    starts_on: ScheduleDate
    description: str
    ends_on: ScheduleDate | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise ValueError("ends_on cannot be earlier than starts_on")

        self._validate_description(self.description)
        self.description = self.description.strip()

    def applies_to(self, date: ScheduleDate) -> bool:
        if self.ends_on is None:
            return self.starts_on == date

        return self.starts_on <= date <= self.ends_on

    def change_description(self, description: str) -> None:
        self._validate_description(description)
        self.description = description.strip()

    @staticmethod
    def _validate_description(description: str) -> None:
        if not description or not description.strip():
            raise ValueError("description is required")