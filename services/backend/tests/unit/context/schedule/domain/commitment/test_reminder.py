from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import dataclasses
import pytest

from backend.context.schedule.domain.commitment.entities import Reminder
from backend.context.schedule.domain.commitment.value_objects import CommitmentStatus


def make_reminder(**overrides: object) -> Reminder:
    data = {
        "user_id": uuid4(),
        "remind_at": datetime(2026, 3, 27, 15, 0, tzinfo=UTC),
        "title": "Call friend",
        "description": "Remind user to call their friend.",
    }
    data.update(overrides)
    return Reminder(**data)


def test_reminder_is_keyword_only_and_slotted() -> None:
    with pytest.raises(TypeError):
        Reminder(uuid4(), datetime(2026, 3, 27, 15, 0), "Call friend")

    reminder = make_reminder()

    assert dataclasses.is_dataclass(reminder)
    assert not hasattr(reminder, "__dict__")


def test_reminder_accepts_naive_utc_or_aware_utc_and_rejects_non_utc() -> None:
    naive = make_reminder(remind_at=datetime(2026, 3, 27, 15, 0))
    aware = make_reminder(remind_at=datetime(2026, 3, 27, 15, 0, tzinfo=UTC))

    assert naive.remind_at.tzinfo is None
    assert aware.remind_at.tzinfo is UTC

    with pytest.raises(ValueError):
        make_reminder(
            remind_at=datetime(
                2026,
                3,
                27,
                15,
                0,
                tzinfo=timezone(timedelta(hours=3)),
            )
        )


def test_reminder_validates_status_and_title() -> None:
    with pytest.raises(ValueError):
        make_reminder(status="active")

    with pytest.raises(ValueError):
        make_reminder(title=" ")


def test_reminder_lifecycle_and_updates() -> None:
    reminder = make_reminder(title="  Call friend  ", description="  Phone reminder  ")

    assert reminder.title == "Call friend"
    assert reminder.description == "Phone reminder"
    assert reminder.status == CommitmentStatus.ACTIVE

    reminder.cancel()
    assert reminder.status == CommitmentStatus.CANCELLED

    reminder.reactivate()
    assert reminder.status == CommitmentStatus.ACTIVE

    new_time = datetime(2026, 3, 27, 16, 0, tzinfo=UTC)
    reminder.reschedule(new_time)
    reminder.rename("  Call Alex  ")
    reminder.change_description(None)

    assert reminder.remind_at == new_time
    assert reminder.title == "Call Alex"
    assert reminder.description is None
