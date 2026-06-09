from uuid import uuid4

import dataclasses
import pytest

from backend.context.schedule.domain.template.entities import WeeklyScheduleObservation


def test_weekly_schedule_observation_is_keyword_only_slotted_and_description_only() -> None:
    template_id = uuid4()

    with pytest.raises(TypeError):
        WeeklyScheduleObservation(template_id, "Gym is near work.")

    observation = WeeklyScheduleObservation(
        weekly_schedule_template_id=template_id,
        description="  Gym is near work.  ",
    )

    assert dataclasses.is_dataclass(observation)
    assert not hasattr(observation, "__dict__")
    assert observation.description == "Gym is near work."
    assert not hasattr(observation, "title")


def test_weekly_schedule_observation_requires_description() -> None:
    with pytest.raises(ValueError):
        WeeklyScheduleObservation(
            weekly_schedule_template_id=uuid4(),
            description=" ",
        )


def test_weekly_schedule_observation_can_change_description() -> None:
    observation = WeeklyScheduleObservation(
        weekly_schedule_template_id=uuid4(),
        description="Initial context.",
    )

    observation.change_description("  Updated context.  ")

    assert observation.description == "Updated context."
