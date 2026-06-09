import dataclasses

import pytest

from backend.context.schedule.domain.shared import LocalTime
from backend.context.schedule.domain.template.entities import DayMarker
from backend.context.schedule.domain.template.value_objects import DayMarkerKind


def make_marker(**overrides: object) -> DayMarker:
    data = {
        "preferred_start_time": LocalTime(hour=12),
        "preferred_end_time": LocalTime(hour=13),
        "kind": DayMarkerKind.MEAL,
        "title": "Lunch",
        "description": "Preferred lunch window.",
    }
    data.update(overrides)
    return DayMarker(**data)


def test_day_marker_is_keyword_only_and_slotted() -> None:
    with pytest.raises(TypeError):
        DayMarker(LocalTime(hour=12), LocalTime(hour=13), DayMarkerKind.MEAL, "Lunch")

    marker = make_marker()

    assert dataclasses.is_dataclass(marker)
    assert not hasattr(marker, "__dict__")


def test_day_marker_validates_kind_title_and_range() -> None:
    with pytest.raises(ValueError):
        make_marker(kind="meal")

    with pytest.raises(ValueError):
        make_marker(title="")

    with pytest.raises(ValueError):
        make_marker(preferred_start_time=LocalTime(hour=13), preferred_end_time=LocalTime(hour=12))


def test_day_marker_can_be_rescheduled_and_renamed() -> None:
    marker = make_marker(title="  Lunch  ", description="  Eat around noon  ")

    assert marker.title == "Lunch"
    assert marker.description == "Eat around noon"

    marker.rename("  Dinner  ")
    marker.reschedule(
        preferred_start_time=LocalTime(hour=19),
        preferred_end_time=LocalTime(hour=20),
    )
    marker.change_description(None)

    assert marker.title == "Dinner"
    assert marker.preferred_start_time == LocalTime(hour=19)
    assert marker.preferred_end_time == LocalTime(hour=20)
    assert marker.description is None
