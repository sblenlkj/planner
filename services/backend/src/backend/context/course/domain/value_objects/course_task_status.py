from __future__ import annotations

from enum import StrEnum, auto

from direttore import StateMachine


class CourseTaskStatus(StrEnum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    SKIPPED = auto()


CourseTaskStatusStateMachine: StateMachine[CourseTaskStatus] = StateMachine(
    transitions={
        CourseTaskStatus.PENDING: {
            CourseTaskStatus.IN_PROGRESS,
            CourseTaskStatus.COMPLETED,
            CourseTaskStatus.SKIPPED,
        },
        CourseTaskStatus.IN_PROGRESS: {
            CourseTaskStatus.COMPLETED,
            CourseTaskStatus.SKIPPED,
        },
        CourseTaskStatus.COMPLETED: {
            CourseTaskStatus.IN_PROGRESS,
        },
        CourseTaskStatus.SKIPPED: {
            CourseTaskStatus.PENDING,
            CourseTaskStatus.IN_PROGRESS,
        },
    }
)


def transition_course_task_status(
    *,
    current: CourseTaskStatus,
    target: CourseTaskStatus,
) -> CourseTaskStatus:
    return CourseTaskStatusStateMachine.transition(
        current=current,
        target=target,
    )