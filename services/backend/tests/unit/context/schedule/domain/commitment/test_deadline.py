from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import dataclasses
import pytest

from backend.context.schedule.domain.commitment.entities import Deadline
from backend.context.schedule.domain.commitment.value_objects import CommitmentStatus


def make_deadline(**overrides: object) -> Deadline:
    data = {
        "user_id": uuid4(),
        "due_at": datetime(2026, 3, 27, 21, 0, tzinfo=UTC),
        "title": "Math homework",
        "description": "Homework must be finished before due time.",
    }
    data.update(overrides)
    return Deadline(**data)


def test_deadline_is_keyword_only_and_slotted() -> None:
    with pytest.raises(TypeError):
        Deadline(uuid4(), datetime(2026, 3, 27, 21, 0), "Math homework")

    deadline = make_deadline()

    assert dataclasses.is_dataclass(deadline)
    assert not hasattr(deadline, "__dict__")


def test_deadline_accepts_naive_utc_or_aware_utc_and_rejects_non_utc() -> None:
    naive = make_deadline(due_at=datetime(2026, 3, 27, 21, 0))
    aware = make_deadline(due_at=datetime(2026, 3, 27, 21, 0, tzinfo=UTC))

    assert naive.due_at.tzinfo is None
    assert aware.due_at.tzinfo is UTC

    with pytest.raises(ValueError):
        make_deadline(
            due_at=datetime(
                2026,
                3,
                27,
                21,
                0,
                tzinfo=timezone(timedelta(hours=3)),
            )
        )


def test_deadline_validates_status_title_and_course_link_consistency() -> None:
    with pytest.raises(ValueError):
        make_deadline(status="active")

    with pytest.raises(ValueError):
        make_deadline(title=" ")

    with pytest.raises(ValueError):
        make_deadline(course_task_id=uuid4(), course_id=None)


def test_deadline_lifecycle_updates_and_course_link() -> None:
    deadline = make_deadline(title="  Homework  ", description="  Finish it  ")

    assert deadline.title == "Homework"
    assert deadline.description == "Finish it"
    assert deadline.status == CommitmentStatus.ACTIVE

    deadline.cancel()
    assert deadline.status == CommitmentStatus.CANCELLED

    deadline.reactivate()
    assert deadline.status == CommitmentStatus.ACTIVE

    new_due_at = datetime(2026, 3, 28, 21, 0, tzinfo=UTC)
    deadline.reschedule(new_due_at)
    deadline.rename("  Physics homework  ")
    deadline.change_description(None)

    assert deadline.due_at == new_due_at
    assert deadline.title == "Physics homework"
    assert deadline.description is None

    course_id = uuid4()
    course_task_id = uuid4()
    deadline.link_course_task(course_id=course_id, course_task_id=course_task_id)

    assert deadline.course_id == course_id
    assert deadline.course_task_id == course_task_id

    deadline.unlink_course_task()

    assert deadline.course_id is None
    assert deadline.course_task_id is None
