from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ...shared import ScheduleDate
from .schedule_day_observation import ScheduleDayObservation
from .scheduled_activity import ScheduledActivity
from .scheduled_block import ScheduledBlock


@dataclass(kw_only=True, slots=True)
class ScheduleDay:
    """
    Aggregate root for one concrete generated user day.

    ScheduleDay belongs to the execution subdomain. It represents the generated
    plan for one user on one concrete date. Its identity is the pair
    (user_id, date), not a standalone UUID.

    The aggregate contains three main parts:

    - blocks: snapshot of the user's day structure copied from the template or
      other planning inputs. Blocks describe sleep, work, free time, limited
      availability, blocked time, and similar time context.

    - activities: concrete planned actions for the day. Activities may be linked
      to CourseTask through course_task_id, but they may also be standalone user
      actions with no course relation.

    - observations: day-local narrative facts about what actually happened.
      These are accumulated after generation and are used as compact context
      for future day planning.

    ScheduleDay.description is the generated day narrative. It summarizes the
    planning intention of the day in text form, so future planning does not have
    to send the full detailed day structure back to the agent every time.

    ScheduleDay intentionally does not reference WeeklyScheduleTemplate after
    generation. The template is an input used to produce the day, but the
    generated day must remain stable even if the template changes later.
    """

    user_id: UUID
    date: ScheduleDate
    title: str
    description: str
    blocks: list[ScheduledBlock] = field(default_factory=list)
    activities: list[ScheduledActivity] = field(default_factory=list)
    observations: list[ScheduleDayObservation] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate_text(self.title, "title")
        self._validate_text(self.description, "description")

        self.title = self.title.strip()
        self.description = self.description.strip()

        self._validate_activities(self.activities)
        self._validate_observations(self.observations)

        self.blocks = sorted(self.blocks, key=lambda item: item.start_time)
        self.activities = sorted(self.activities, key=lambda item: item.start_time)

    @property
    def identity(self) -> tuple[UUID, ScheduleDate]:
        return self.user_id, self.date

    def add_block(self, block: ScheduledBlock) -> None:
        self.blocks.append(block)
        self.blocks.sort(key=lambda item: item.start_time)

    def remove_block(self, block_id: UUID) -> None:
        self.blocks = [block for block in self.blocks if block.id != block_id]

    def replace_blocks(self, blocks: list[ScheduledBlock]) -> None:
        self.blocks = sorted(blocks, key=lambda item: item.start_time)

    def add_activity(self, activity: ScheduledActivity) -> None:
        self._validate_new_activity(activity)
        self.activities.append(activity)
        self.activities.sort(key=lambda item: item.start_time)

    def remove_activity(self, activity_id: UUID) -> None:
        self.activities = [
            activity for activity in self.activities if activity.id != activity_id
        ]

    def replace_activities(self, activities: list[ScheduledActivity]) -> None:
        self._validate_activities(activities)
        self.activities = sorted(activities, key=lambda item: item.start_time)

    def add_observation(self, observation: ScheduleDayObservation) -> None:
        if observation.user_id != self.user_id or observation.date != self.date:
            raise ValueError("observation must belong to this schedule day")

        self.observations.append(observation)

    def remove_observation(self, observation_id: UUID) -> None:
        self.observations = [
            observation
            for observation in self.observations
            if observation.id != observation_id
        ]

    def rename(self, title: str) -> None:
        self._validate_text(title, "title")
        self.title = title.strip()

    def change_description(self, description: str) -> None:
        self._validate_text(description, "description")
        self.description = description.strip()

    def _validate_new_activity(self, activity: ScheduledActivity) -> None:
        for existing in self.activities:
            if existing.id != activity.id and existing.overlaps(activity):
                raise ValueError(
                    "scheduled activities must not overlap inside one schedule day"
                )

    def _validate_activities(self, activities: list[ScheduledActivity]) -> None:
        sorted_activities = sorted(activities, key=lambda item: item.start_time)

        for previous, current in zip(sorted_activities, sorted_activities[1:]):
            if previous.overlaps(current):
                raise ValueError(
                    "scheduled activities must not overlap inside one schedule day"
                )

    def _validate_observations(
        self,
        observations: list[ScheduleDayObservation],
    ) -> None:
        for observation in observations:
            if observation.user_id != self.user_id or observation.date != self.date:
                raise ValueError("all observations must belong to this schedule day")

    @staticmethod
    def _validate_text(value: str, field_name: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{field_name} is required")