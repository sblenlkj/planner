import dataclasses

import pytest

from backend.context.schedule.domain.shared import LocalTime, TimeBlockKind
from backend.context.schedule.domain.template.entities import TimeBlock


def make_block(**overrides: object) -> TimeBlock:
    data = {
        "start_time": LocalTime(hour=9),
        "end_time": LocalTime(hour=12),
        "kind": TimeBlockKind.BUSY,
        "title": "Work",
        "description": "User is busy at work.",
    }
    data.update(overrides)
    return TimeBlock(**data)


def test_time_block_is_keyword_only_and_slotted() -> None:
    with pytest.raises(TypeError):
        TimeBlock(LocalTime(hour=9), LocalTime(hour=12), TimeBlockKind.BUSY, "Work")

    block = make_block()

    assert dataclasses.is_dataclass(block)
    assert not hasattr(block, "__dict__")


def test_time_block_normalizes_text_and_has_no_subtype() -> None:
    block = make_block(title="  Work  ", description="  Office time  ")

    assert block.title == "Work"
    assert block.description == "Office time"
    assert not hasattr(block, "subtype")


def test_time_block_requires_valid_kind_title_and_time_range() -> None:
    with pytest.raises(ValueError):
        make_block(kind="busy")

    with pytest.raises(ValueError):
        make_block(title="  ")

    with pytest.raises(ValueError):
        make_block(start_time=LocalTime(hour=12), end_time=LocalTime(hour=9))


def test_time_block_overlaps_and_reschedule() -> None:
    block = make_block(start_time=LocalTime(hour=9), end_time=LocalTime(hour=12))
    overlapping = make_block(start_time=LocalTime(hour=11), end_time=LocalTime(hour=13))
    adjacent = make_block(start_time=LocalTime(hour=12), end_time=LocalTime(hour=13))

    assert block.overlaps(overlapping)
    assert not block.overlaps(adjacent)

    block.reschedule(start_time=LocalTime(hour=8), end_time=LocalTime(hour=10))

    assert block.start_time == LocalTime(hour=8)
    assert block.end_time == LocalTime(hour=10)


def test_time_block_renames_and_changes_description() -> None:
    block = make_block()

    block.rename("  Deep work  ")
    block.change_description("  Focused work window  ")

    assert block.title == "Deep work"
    assert block.description == "Focused work window"

    block.change_description(None)

    assert block.description is None
