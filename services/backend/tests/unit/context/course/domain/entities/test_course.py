from uuid import UUID, uuid4

import pytest

from backend.context.course.domain.entities.course import Course
from backend.context.course.domain.value_objects import CourseStatus


def test_create_course() -> None:
    course = Course.create(
        user_id=uuid4(),
        title="  Learn Python  ",
        description="  Backend development course  ",
    )

    assert isinstance(course.id, UUID)
    assert course.title == "Learn Python"
    assert course.description == "Backend development course"
    assert course.status == CourseStatus.ACTIVE


def test_create_course_requires_title() -> None:
    with pytest.raises(ValueError):
        Course.create(
            user_id=uuid4(),
            title="   ",
            description="Backend development course",
        )


def test_create_course_requires_description() -> None:
    with pytest.raises(ValueError):
        Course.create(
            user_id=uuid4(),
            title="Learn Python",
            description="   ",
        )


def test_rename_course() -> None:
    course = Course.create(
        user_id=uuid4(),
        title="Learn Python",
        description="Backend development course",
    )

    course.rename("  Learn FastAPI  ")

    assert course.title == "Learn FastAPI"


def test_course_lifecycle_transitions() -> None:
    course = Course.create(
        user_id=uuid4(),
        title="Learn Python",
        description="Backend development course",
    )

    course.complete()
    assert course.status == CourseStatus.COMPLETED

    course.archive()
    assert course.status == CourseStatus.ARCHIVED

    course.reactivate()
    assert course.status == CourseStatus.ACTIVE
