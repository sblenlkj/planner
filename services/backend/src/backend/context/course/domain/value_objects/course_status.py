from __future__ import annotations

from enum import StrEnum, auto

from direttore import StateMachine


class CourseStatus(StrEnum):
    ACTIVE = auto()
    COMPLETED = auto()
    ARCHIVED = auto()


CourseStatusStateMachine: StateMachine[CourseStatus] = StateMachine(
    transitions={
        CourseStatus.ACTIVE: {
            CourseStatus.COMPLETED,
            CourseStatus.ARCHIVED,
        },
        CourseStatus.COMPLETED: {
            CourseStatus.ACTIVE,
            CourseStatus.ARCHIVED,
        },
        CourseStatus.ARCHIVED: {
            CourseStatus.ACTIVE,
        },
    }
)


def transition_course_status(
    *,
    current: CourseStatus,
    target: CourseStatus,
) -> CourseStatus:
    return CourseStatusStateMachine.transition(
        current=current,
        target=target,
    )