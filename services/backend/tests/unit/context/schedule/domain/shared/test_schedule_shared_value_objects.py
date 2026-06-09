import pytest

from backend.context.schedule.domain.shared import LocalTime, LocalTimeRange, ScheduleDate, TimeBlockKind


def test_local_time_validates_hour_and_minute() -> None:
    assert str(LocalTime(hour=9, minute=5)) == "09:05"
    assert LocalTime.parse("23:59") == LocalTime(hour=23, minute=59)

    with pytest.raises(ValueError):
        LocalTime(hour=24, minute=0)

    with pytest.raises(ValueError):
        LocalTime(hour=10, minute=60)

    with pytest.raises(ValueError):
        LocalTime.parse("10")


def test_local_time_range_requires_start_before_end() -> None:
    with pytest.raises(ValueError):
        LocalTimeRange(
            start_time=LocalTime(hour=10),
            end_time=LocalTime(hour=10),
        )

    with pytest.raises(ValueError):
        LocalTimeRange(
            start_time=LocalTime(hour=11),
            end_time=LocalTime(hour=10),
        )


def test_local_time_range_overlap_and_contains() -> None:
    morning = LocalTimeRange(start_time=LocalTime(hour=9), end_time=LocalTime(hour=12))
    late_morning = LocalTimeRange(start_time=LocalTime(hour=11), end_time=LocalTime(hour=13))
    afternoon = LocalTimeRange(start_time=LocalTime(hour=12), end_time=LocalTime(hour=14))

    assert morning.overlaps(late_morning)
    assert not morning.overlaps(afternoon)
    assert morning.contains(LocalTime(hour=9))
    assert morning.contains(LocalTime(hour=11, minute=59))
    assert not morning.contains(LocalTime(hour=12))


def test_schedule_date_validates_calendar_date_and_orders() -> None:
    value = ScheduleDate.parse("2026-03-27")

    assert str(value) == "2026-03-27"
    assert value < ScheduleDate(year=2026, month=3, day=28)

    with pytest.raises(ValueError):
        ScheduleDate(year=2026, month=2, day=30)


def test_time_block_kind_is_small_algorithmic_enum() -> None:
    assert set(TimeBlockKind) == {
        TimeBlockKind.FREE,
        TimeBlockKind.BUSY,
        TimeBlockKind.SLEEP,
        TimeBlockKind.LIMITED,
        TimeBlockKind.BLOCKED,
    }
