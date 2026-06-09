import dataclasses
from uuid import uuid4

import pytest

from backend.context.schedule.domain.execution.entities import ScheduledActivity
from backend.context.schedule.domain.shared import LocalTime


def make_activity(**overrides: object) -> ScheduledActivity:
    data = {
        "start_time": LocalTime(hour=20),
        "end_time": LocalTime(hour=21),
        "title": "Read Python",
        "description": "Continue current course material.",
    }
    data.update(overrides)
    return ScheduledActivity(**data)


def test_scheduled_activity_is_keyword_only_slotted_and_optional_course_task() -> None:
    with pytest.raises(TypeError):
        ScheduledActivity(LocalTime(hour=20), LocalTime(hour=21), "Read Python")

    course_task_id = uuid4()
    activity = make_activity(course_task_id=course_task_id)

    assert dataclasses.is_dataclass(activity)
    assert not hasattr(activity, "__dict__")
    assert activity.course_task_id == course_task_id


def test_scheduled_activity_validates_title_and_time_range() -> None:
    with pytest.raises(ValueError):
        make_activity(title=" ")

    with pytest.raises(ValueError):
        make_activity(start_time=LocalTime(hour=21), end_time=LocalTime(hour=20))


def test_scheduled_activity_has_no_status_or_source() -> None:
    activity = make_activity()

    assert not hasattr(activity, "status")
    assert not hasattr(activity, "source")


def test_scheduled_activity_overlaps_reschedules_and_links_course_task() -> None:
    activity = make_activity(start_time=LocalTime(hour=20), end_time=LocalTime(hour=21))
    overlapping = make_activity(start_time=LocalTime(hour=20, minute=30), end_time=LocalTime(hour=21, minute=30))
    adjacent = make_activity(start_time=LocalTime(hour=21), end_time=LocalTime(hour=22))

    assert activity.overlaps(overlapping)
    assert not activity.overlaps(adjacent)

    activity.reschedule(start_time=LocalTime(hour=18), end_time=LocalTime(hour=19))
    activity.rename("  Review Python  ")
    activity.change_description(None)

    task_id = uuid4()
    activity.link_course_task(task_id)

    assert activity.start_time == LocalTime(hour=18)
    assert activity.end_time == LocalTime(hour=19)
    assert activity.title == "Review Python"
    assert activity.description is None
    assert activity.course_task_id == task_id

    activity.unlink_course_task()

    assert activity.course_task_id is None
