import dataclasses
from uuid import uuid4

import pytest

from backend.context.schedule.domain.shared import LocalTime, TimeBlockKind
from backend.context.schedule.domain.template.entities import DayMarker, ScheduleDayTemplate, TimeBlock
from backend.context.schedule.domain.template.value_objects import DayMarkerKind, Weekday


def make_block(start_hour: int, end_hour: int, *, title: str = "Block") -> TimeBlock:
    return TimeBlock(
        start_time=LocalTime(hour=start_hour),
        end_time=LocalTime(hour=end_hour),
        kind=TimeBlockKind.BUSY,
        title=title,
    )


def make_marker(start_hour: int, end_hour: int, *, title: str = "Marker") -> DayMarker:
    return DayMarker(
        preferred_start_time=LocalTime(hour=start_hour),
        preferred_end_time=LocalTime(hour=end_hour),
        kind=DayMarkerKind.MEAL,
        title=title,
    )


def test_schedule_day_template_is_keyword_only_slotted_and_has_composite_identity() -> None:
    template_id = uuid4()

    with pytest.raises(TypeError):
        ScheduleDayTemplate(template_id, Weekday.MONDAY)

    day = ScheduleDayTemplate(
        weekly_schedule_template_id=template_id,
        weekday=Weekday.MONDAY,
    )

    assert dataclasses.is_dataclass(day)
    assert not hasattr(day, "__dict__")
    assert day.identity == (template_id, Weekday.MONDAY)


def test_schedule_day_template_requires_weekday_enum() -> None:
    with pytest.raises(ValueError):
        ScheduleDayTemplate(
            weekly_schedule_template_id=uuid4(),
            weekday="monday",
        )


def test_schedule_day_template_rejects_overlapping_time_blocks() -> None:
    with pytest.raises(ValueError):
        ScheduleDayTemplate(
            weekly_schedule_template_id=uuid4(),
            weekday=Weekday.MONDAY,
            time_blocks=[make_block(9, 12), make_block(11, 13)],
        )


def test_schedule_day_template_allows_markers_to_overlap_blocks_and_markers() -> None:
    day = ScheduleDayTemplate(
        weekly_schedule_template_id=uuid4(),
        weekday=Weekday.MONDAY,
        time_blocks=[make_block(8, 18, title="Work")],
        markers=[
            make_marker(12, 13, title="Lunch"),
            make_marker(12, 14, title="Long lunch marker"),
        ],
    )

    assert len(day.time_blocks) == 1
    assert len(day.markers) == 2


def test_schedule_day_template_add_replace_and_remove_children() -> None:
    day = ScheduleDayTemplate(
        weekly_schedule_template_id=uuid4(),
        weekday=Weekday.MONDAY,
    )
    morning = make_block(9, 12, title="Morning")
    afternoon = make_block(13, 17, title="Afternoon")
    marker = make_marker(12, 13, title="Lunch")

    day.add_time_block(afternoon)
    day.add_time_block(morning)
    day.add_marker(marker)

    assert day.time_blocks == [morning, afternoon]
    assert day.markers == [marker]

    with pytest.raises(ValueError):
        day.add_time_block(make_block(11, 14, title="Overlap"))

    day.remove_time_block(morning.id)
    day.remove_marker(marker.id)

    assert day.time_blocks == [afternoon]
    assert day.markers == []
