from uuid import uuid4

import dataclasses
import pytest

from backend.context.schedule.domain.execution.entities import ScheduleDayObservation
from backend.context.schedule.domain.shared import ScheduleDate


def test_schedule_day_observation_is_keyword_only_slotted_and_description_only() -> None:
    date = ScheduleDate(year=2026, month=6, day=10)

    with pytest.raises(TypeError):
        ScheduleDayObservation(uuid4(), date, "User missed the morning.")

    observation = ScheduleDayObservation(
        user_id=uuid4(),
        date=date,
        description="  User missed the morning.  ",
    )

    assert dataclasses.is_dataclass(observation)
    assert not hasattr(observation, "__dict__")
    assert observation.description == "User missed the morning."
    assert not hasattr(observation, "title")


def test_schedule_day_observation_requires_description() -> None:
    with pytest.raises(ValueError):
        ScheduleDayObservation(
            user_id=uuid4(),
            date=ScheduleDate(year=2026, month=6, day=10),
            description=" ",
        )


def test_schedule_day_observation_can_change_description() -> None:
    observation = ScheduleDayObservation(
        user_id=uuid4(),
        date=ScheduleDate(year=2026, month=6, day=10),
        description="Initial.",
    )

    observation.change_description("  Updated.  ")

    assert observation.description == "Updated."
