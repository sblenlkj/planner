import pytest

from backend.context.course.domain.value_objects import (
    CourseStatus,
    transition_course_status,
)


def test_transition_active_course_to_completed() -> None:
    assert (
        transition_course_status(
            current=CourseStatus.ACTIVE,
            target=CourseStatus.COMPLETED,
        )
        == CourseStatus.COMPLETED
    )


def test_transition_archived_course_to_completed_is_not_allowed() -> None:
    with pytest.raises(ValueError):
        transition_course_status(
            current=CourseStatus.ARCHIVED,
            target=CourseStatus.COMPLETED,
        )
