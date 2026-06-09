import dataclasses
from uuid import uuid4

import pytest

from backend.context.schedule.domain.execution.entities import (
    ScheduleDay,
    ScheduleDayObservation,
    ScheduledActivity,
    ScheduledBlock,
)
from backend.context.schedule.domain.shared import LocalTime, ScheduleDate, TimeBlockKind


def make_activity(start_hour: int, end_hour: int, *, title: str = "Activity") -> ScheduledActivity:
    return ScheduledActivity(
        start_time=LocalTime(hour=start_hour),
        end_time=LocalTime(hour=end_hour),
        title=title,
    )


def make_block(start_hour: int, end_hour: int, *, title: str = "Block") -> ScheduledBlock:
    return ScheduledBlock(
        start_time=LocalTime(hour=start_hour),
        end_time=LocalTime(hour=end_hour),
        kind=TimeBlockKind.BUSY,
        title=title,
    )


def make_day(**overrides: object) -> ScheduleDay:
    data = {
        "user_id": uuid4(),
        "date": ScheduleDate(year=2026, month=6, day=10),
        "title": "Python day",
        "description": "Morning Python, evening review.",
    }
    data.update(overrides)
    return ScheduleDay(**data)


def test_schedule_day_is_keyword_only_slotted_and_identity_is_user_date() -> None:
    user_id = uuid4()
    date = ScheduleDate(year=2026, month=6, day=10)

    with pytest.raises(TypeError):
        ScheduleDay(user_id, date, "Python day", "Plan description")

    day = make_day(user_id=user_id, date=date)

    assert dataclasses.is_dataclass(day)
    assert not hasattr(day, "__dict__")
    assert day.identity == (user_id, date)


def test_schedule_day_requires_title_and_description() -> None:
    with pytest.raises(ValueError):
        make_day(title=" ")

    with pytest.raises(ValueError):
        make_day(description=" ")


def test_schedule_day_sorts_blocks_and_activities() -> None:
    late_block = make_block(18, 20, title="Evening")
    early_block = make_block(8, 12, title="Morning")
    late_activity = make_activity(20, 21, title="Review")
    early_activity = make_activity(9, 10, title="Read")

    day = make_day(
        blocks=[late_block, early_block],
        activities=[late_activity, early_activity],
    )

    assert day.blocks == [early_block, late_block]
    assert day.activities == [early_activity, late_activity]


def test_schedule_day_rejects_overlapping_activities_but_not_overlapping_blocks() -> None:
    with pytest.raises(ValueError):
        make_day(
            activities=[
                make_activity(9, 12, title="Read"),
                make_activity(11, 13, title="Practice"),
            ]
        )

    day = make_day(
        blocks=[
            make_block(8, 18, title="Work"),
            make_block(12, 13, title="Lunch-like block"),
        ]
    )

    assert len(day.blocks) == 2


def test_schedule_day_add_remove_and_replace_activities() -> None:
    day = make_day()
    morning = make_activity(9, 10, title="Read")
    evening = make_activity(20, 21, title="Review")

    day.add_activity(evening)
    day.add_activity(morning)

    assert day.activities == [morning, evening]

    with pytest.raises(ValueError):
        day.add_activity(make_activity(9, 11, title="Overlap"))

    day.remove_activity(morning.id)

    assert day.activities == [evening]

    day.replace_activities([morning])

    assert day.activities == [morning]


def test_schedule_day_add_remove_and_replace_blocks() -> None:
    day = make_day()
    morning = make_block(8, 12, title="Morning")
    evening = make_block(18, 22, title="Evening")

    day.add_block(evening)
    day.add_block(morning)

    assert day.blocks == [morning, evening]

    day.remove_block(morning.id)

    assert day.blocks == [evening]

    day.replace_blocks([morning])

    assert day.blocks == [morning]


def test_schedule_day_observations_must_belong_to_day() -> None:
    user_id = uuid4()
    date = ScheduleDate(year=2026, month=6, day=10)
    day = make_day(user_id=user_id, date=date)
    observation = ScheduleDayObservation(
        user_id=user_id,
        date=date,
        description="User missed the morning plan.",
    )

    day.add_observation(observation)

    assert day.observations == [observation]

    with pytest.raises(ValueError):
        day.add_observation(
            ScheduleDayObservation(
                user_id=uuid4(),
                date=date,
                description="Foreign observation.",
            )
        )

    day.remove_observation(observation.id)

    assert day.observations == []


def test_schedule_day_renames_and_changes_description() -> None:
    day = make_day(title="  Python day  ", description="  Plan details  ")

    assert day.title == "Python day"
    assert day.description == "Plan details"

    day.rename("  Backend day  ")
    day.change_description("  Updated narrative  ")

    assert day.title == "Backend day"
    assert day.description == "Updated narrative"
