import pytest

from backend.context.course.domain.value_objects import CourseTaskProgress


def test_course_task_progress_factories() -> None:
    assert CourseTaskProgress.zero().value == 0
    assert CourseTaskProgress.complete().value == 100
    assert CourseTaskProgress.percent(50).value == 50


def test_course_task_progress_properties() -> None:
    assert CourseTaskProgress.zero().is_zero
    assert CourseTaskProgress.percent(1).is_started
    assert CourseTaskProgress.complete().is_complete


def test_course_task_progress_rejects_value_below_zero() -> None:
    with pytest.raises(ValueError):
        CourseTaskProgress.percent(-1)


def test_course_task_progress_rejects_value_above_100() -> None:
    with pytest.raises(ValueError):
        CourseTaskProgress.percent(101)
