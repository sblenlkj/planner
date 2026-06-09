from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..value_objects import Weekday
from .schedule_day_template import ScheduleDayTemplate
from .weekly_schedule_observation import WeeklyScheduleObservation


@dataclass(kw_only=True, slots=True)
class WeeklyScheduleTemplate:
    """
    Aggregate root for a user's ordinary weekly schedule template.

    WeeklyScheduleTemplate belongs to the template subdomain. It describes the
    user's repeating weekly time structure: what each weekday usually looks
    like, which time blocks exist, which soft markers should be considered,
    and which stable observations help the planner interpret the week.

    At the current product stage, each user is expected to have one active
    weekly template. The model still has its own UUID and child references by
    weekly_schedule_template_id, so the architecture can later support multiple
    templates per user without changing the core entity shape.

    The aggregate owns exactly seven ScheduleDayTemplate entities, one per
    Weekday. A day template is identified by the pair
    (weekly_schedule_template_id, weekday), not by a standalone UUID.

    WeeklyScheduleTemplate is not a concrete calendar and not a generated
    schedule. It has no real dates and no concrete planned activities. The
    execution subdomain expands this template into ScheduleDay snapshots when
    the system plans a concrete day.

    Observations attached to this aggregate are stable narrative context for
    the whole weekly template. They are useful for planner reasoning but are
    intentionally not modeled as structured rules at this stage.
    """

    user_id: UUID
    days: list[ScheduleDayTemplate]
    observations: list[WeeklyScheduleObservation] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate_days(self.days)
        self._ensure_children_reference_this_template()

        self.days = sorted(self.days, key=lambda item: Weekday.all().index(item.weekday))

    @classmethod
    def create_empty(
        cls,
        *,
        user_id: UUID,
        template_id: UUID | None = None,
    ) -> WeeklyScheduleTemplate:
        actual_id = template_id or uuid4()
        days = [
            ScheduleDayTemplate(
                weekly_schedule_template_id=actual_id,
                weekday=weekday,
            )
            for weekday in Weekday.all()
        ]
        return cls(user_id=user_id, days=days, id=actual_id)

    def get_day(self, weekday: Weekday) -> ScheduleDayTemplate:
        for day in self.days:
            if day.weekday == weekday:
                return day

        raise KeyError(f"day template does not exist for {weekday.value}")

    def replace_day(self, day: ScheduleDayTemplate) -> None:
        if day.weekly_schedule_template_id != self.id:
            raise ValueError("day belongs to another weekly schedule template")

        new_days = [existing for existing in self.days if existing.weekday != day.weekday]
        new_days.append(day)

        self._validate_days(new_days)
        self.days = sorted(new_days, key=lambda item: Weekday.all().index(item.weekday))

    def add_observation(self, observation: WeeklyScheduleObservation) -> None:
        if observation.weekly_schedule_template_id != self.id:
            raise ValueError("observation belongs to another weekly schedule template")

        self.observations.append(observation)

    def remove_observation(self, observation_id: UUID) -> None:
        self.observations = [
            observation
            for observation in self.observations
            if observation.id != observation_id
        ]

    def _ensure_children_reference_this_template(self) -> None:
        for day in self.days:
            if day.weekly_schedule_template_id != self.id:
                raise ValueError("all day templates must reference WeeklyScheduleTemplate.id")

        for observation in self.observations:
            if observation.weekly_schedule_template_id != self.id:
                raise ValueError("all observations must reference WeeklyScheduleTemplate.id")

    @staticmethod
    def _validate_days(days: list[ScheduleDayTemplate]) -> None:
        weekdays = [day.weekday for day in days]
        expected = set(Weekday.all())

        if len(days) != 7:
            raise ValueError("weekly schedule template must have exactly 7 days")

        if set(weekdays) != expected:
            raise ValueError("weekly schedule template must have one day per weekday")

        if len(weekdays) != len(set(weekdays)):
            raise ValueError("weekly schedule template cannot contain duplicate weekdays")