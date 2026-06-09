from uuid import uuid4

import dataclasses
import pytest

from backend.context.schedule.domain.execution.entities import ScheduleDateObservation
from backend.context.schedule.domain.shared import ScheduleDate


def test_schedule_date_observation_is_keyword_only_slotted_and_description_only() -> None:
    starts_on = ScheduleDate(year=2026, month=6, day=10)

    with pytest.raises(TypeError):
        ScheduleDateObservation(uuid4(), starts_on, "Future context.")

    observation = ScheduleDateObservation(
        user_id=uuid4(),
        starts_on=starts_on,
        description="  User wants to go to cinema.  ",
    )

    assert dataclasses.is_dataclass(observation)
    assert not hasattr(observation, "__dict__")
    assert observation.description == "User wants to go to cinema."
    assert not hasattr(observation, "title")


def test_schedule_date_observation_applies_to_single_date_or_inclusive_range() -> None:
    user_id = uuid4()
    single = ScheduleDateObservation(
        user_id=user_id,
        starts_on=ScheduleDate(year=2026, month=6, day=10),
        description="Single date context.",
    )

    assert single.applies_to(ScheduleDate(year=2026, month=6, day=10))
    assert not single.applies_to(ScheduleDate(year=2026, month=6, day=11))

    ranged = ScheduleDateObservation(
        user_id=user_id,
        starts_on=ScheduleDate(year=2026, month=6, day=10),
        ends_on=ScheduleDate(year=2026, month=6, day=12),
        description="Range context.",
    )

    assert ranged.applies_to(ScheduleDate(year=2026, month=6, day=10))
    assert ranged.applies_to(ScheduleDate(year=2026, month=6, day=11))
    assert ranged.applies_to(ScheduleDate(year=2026, month=6, day=12))
    assert not ranged.applies_to(ScheduleDate(year=2026, month=6, day=13))


def test_schedule_date_observation_rejects_invalid_range_and_description() -> None:
    with pytest.raises(ValueError):
        ScheduleDateObservation(
            user_id=uuid4(),
            starts_on=ScheduleDate(year=2026, month=6, day=12),
            ends_on=ScheduleDate(year=2026, month=6, day=10),
            description="Invalid.",
        )

    with pytest.raises(ValueError):
        ScheduleDateObservation(
            user_id=uuid4(),
            starts_on=ScheduleDate(year=2026, month=6, day=10),
            description=" ",
        )
