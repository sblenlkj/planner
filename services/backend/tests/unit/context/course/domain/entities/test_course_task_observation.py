from uuid import UUID, uuid4

import pytest

from backend.context.course.domain.entities.course_task_observation import (
    CourseTaskObservation,
)
from backend.context.course.domain.value_objects import CourseTaskProgress


def test_create_course_task_observation() -> None:
    task_id = uuid4()

    observation = CourseTaskObservation.create(
        task_id=task_id,
        title="  Important idea  ",
        description="  Decorators wrap functions and preserve behavior.  ",
        progress=CourseTaskProgress.percent(40),
    )

    assert isinstance(observation.id, UUID)
    assert observation.task_id == task_id
    assert observation.title == "Important idea"
    assert observation.description == "Decorators wrap functions and preserve behavior."
    assert observation.progress == CourseTaskProgress.percent(40)


def test_create_course_task_observation_requires_title() -> None:
    with pytest.raises(ValueError):
        CourseTaskObservation.create(
            task_id=uuid4(),
            title="   ",
            description="Decorators wrap functions and preserve behavior.",
        )


def test_create_course_task_observation_requires_description() -> None:
    with pytest.raises(ValueError):
        CourseTaskObservation.create(
            task_id=uuid4(),
            title="Important idea",
            description="   ",
        )


def test_change_course_task_observation_progress() -> None:
    observation = CourseTaskObservation.create(
        task_id=uuid4(),
        title="Important idea",
        description="Decorators wrap functions and preserve behavior.",
    )

    observation.change_progress(CourseTaskProgress.percent(60))

    assert observation.progress == CourseTaskProgress.percent(60)
