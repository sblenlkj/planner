import dataclasses
from uuid import uuid4

import pytest

from backend.context.schedule.domain.template.entities import (
    ScheduleDayTemplate,
    WeeklyScheduleObservation,
    WeeklyScheduleTemplate,
)
from backend.context.schedule.domain.template.value_objects import Weekday


def test_weekly_schedule_template_create_empty_creates_one_day_per_weekday() -> None:
    user_id = uuid4()
    template = WeeklyScheduleTemplate.create_empty(user_id=user_id)

    assert dataclasses.is_dataclass(template)
    assert not hasattr(template, "__dict__")
    assert template.user_id == user_id
    assert [day.weekday for day in template.days] == Weekday.all()
    assert all(day.weekly_schedule_template_id == template.id for day in template.days)


def test_weekly_schedule_template_requires_exactly_seven_unique_days() -> None:
    template_id = uuid4()
    user_id = uuid4()
    six_days = [
        ScheduleDayTemplate(
            weekly_schedule_template_id=template_id,
            weekday=weekday,
        )
        for weekday in Weekday.all()[:6]
    ]

    with pytest.raises(ValueError):
        WeeklyScheduleTemplate(user_id=user_id, days=six_days, id=template_id)

    duplicate_days = [
        ScheduleDayTemplate(
            weekly_schedule_template_id=template_id,
            weekday=Weekday.MONDAY,
        )
        for _ in range(7)
    ]

    with pytest.raises(ValueError):
        WeeklyScheduleTemplate(user_id=user_id, days=duplicate_days, id=template_id)


def test_weekly_schedule_template_requires_children_to_reference_template_id() -> None:
    template_id = uuid4()
    wrong_id = uuid4()
    days = [
        ScheduleDayTemplate(
            weekly_schedule_template_id=wrong_id,
            weekday=weekday,
        )
        for weekday in Weekday.all()
    ]

    with pytest.raises(ValueError):
        WeeklyScheduleTemplate(user_id=uuid4(), days=days, id=template_id)


def test_weekly_schedule_template_get_replace_and_observations() -> None:
    template = WeeklyScheduleTemplate.create_empty(user_id=uuid4())
    monday = template.get_day(Weekday.MONDAY)

    assert monday.weekday == Weekday.MONDAY

    replacement = ScheduleDayTemplate(
        weekly_schedule_template_id=template.id,
        weekday=Weekday.MONDAY,
    )
    template.replace_day(replacement)

    assert template.get_day(Weekday.MONDAY) is replacement

    observation = WeeklyScheduleObservation(
        weekly_schedule_template_id=template.id,
        description="Gym is near work.",
    )
    template.add_observation(observation)

    assert template.observations == [observation]

    template.remove_observation(observation.id)

    assert template.observations == []


def test_weekly_schedule_template_rejects_foreign_day_and_observation() -> None:
    template = WeeklyScheduleTemplate.create_empty(user_id=uuid4())

    with pytest.raises(ValueError):
        template.replace_day(
            ScheduleDayTemplate(
                weekly_schedule_template_id=uuid4(),
                weekday=Weekday.MONDAY,
            )
        )

    with pytest.raises(ValueError):
        template.add_observation(
            WeeklyScheduleObservation(
                weekly_schedule_template_id=uuid4(),
                description="Foreign observation.",
            )
        )
