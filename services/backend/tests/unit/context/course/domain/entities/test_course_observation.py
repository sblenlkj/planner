from uuid import UUID, uuid4

import pytest

from backend.context.course.domain.entities.course_observation import CourseObservation


def test_create_course_observation() -> None:
    course_id = uuid4()

    observation = CourseObservation.create(
        course_id=course_id,
        title="  Motivation  ",
        description="  User learns Python to become a backend developer.  ",
    )

    assert isinstance(observation.id, UUID)
    assert observation.course_id == course_id
    assert observation.title == "Motivation"
    assert observation.description == "User learns Python to become a backend developer."


def test_create_course_observation_requires_title() -> None:
    with pytest.raises(ValueError):
        CourseObservation.create(
            course_id=uuid4(),
            title="   ",
            description="User learns Python to become a backend developer.",
        )


def test_create_course_observation_requires_description() -> None:
    with pytest.raises(ValueError):
        CourseObservation.create(
            course_id=uuid4(),
            title="Motivation",
            description="   ",
        )


def test_change_course_observation_description() -> None:
    observation = CourseObservation.create(
        course_id=uuid4(),
        title="Motivation",
        description="User learns Python.",
    )

    observation.change_description("  User learns Python for backend work.  ")

    assert observation.description == "User learns Python for backend work."
