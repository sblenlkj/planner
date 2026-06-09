import pytest

from backend.context.course.domain.value_objects import (
    CourseTaskStatus,
    transition_course_task_status,
)


def test_transition_pending_task_to_in_progress() -> None:
    assert (
        transition_course_task_status(
            current=CourseTaskStatus.PENDING,
            target=CourseTaskStatus.IN_PROGRESS,
        )
        == CourseTaskStatus.IN_PROGRESS
    )


def test_transition_completed_task_to_skipped_is_not_allowed() -> None:
    with pytest.raises(ValueError):
        transition_course_task_status(
            current=CourseTaskStatus.COMPLETED,
            target=CourseTaskStatus.SKIPPED,
        )
