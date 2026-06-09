from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(kw_only=True, slots=True)
class WeeklyScheduleObservation:
    """
    Stable narrative context attached to a WeeklyScheduleTemplate.

    WeeklyScheduleObservation belongs to the template subdomain. It stores
    long-lived context that helps the planner interpret the user's ordinary
    weekly schedule.

    This entity is intentionally text-only. It is not a marker, not a time
    block, not a constraint, and not a structured rule. It exists for facts
    that are useful for agent reasoning but do not deserve their own domain
    model yet.

    The observation is attached to the whole weekly template instead of a
    specific day. This is useful for general schedule context: habitual
    preferences, location assumptions, interpretation notes, and stable
    planning facts.

    The model keeps only description because observations are consumed as
    narrative context. A separate title would usually duplicate the same idea
    and make user-facing/agent-facing text noisier.
    """

    weekly_schedule_template_id: UUID
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