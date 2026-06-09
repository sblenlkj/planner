import pytest

from backend.context.course.domain.value_objects import CourseTaskPriority


def test_course_task_priority_factories() -> None:
    assert CourseTaskPriority.low().value == 1
    assert CourseTaskPriority.normal().value == 2
    assert CourseTaskPriority.high().value == 3


def test_course_task_priority_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        CourseTaskPriority(value=4)
