import dataclasses

import pytest

from backend.context.schedule.domain.execution.entities import ScheduledBlock
from backend.context.schedule.domain.shared import LocalTime, TimeBlockKind


def make_block(**overrides: object) -> ScheduledBlock:
    data = {
        "start_time": LocalTime(hour=8),
        "end_time": LocalTime(hour=18),
        "kind": TimeBlockKind.BUSY,
        "title": "Work",
        "description": "Copied day context.",
    }
    data.update(overrides)
    return ScheduledBlock(**data)


def test_scheduled_block_is_keyword_only_slotted_and_has_no_subtype() -> None:
    with pytest.raises(TypeError):
        ScheduledBlock(LocalTime(hour=8), LocalTime(hour=18), TimeBlockKind.BUSY, "Work")

    block = make_block()

    assert dataclasses.is_dataclass(block)
    assert not hasattr(block, "__dict__")
    assert not hasattr(block, "subtype")


def test_scheduled_block_validates_kind_title_and_time_range() -> None:
    with pytest.raises(ValueError):
        make_block(kind="busy")

    with pytest.raises(ValueError):
        make_block(title="")

    with pytest.raises(ValueError):
        make_block(start_time=LocalTime(hour=18), end_time=LocalTime(hour=8))


def test_scheduled_block_normalizes_text_overlaps_and_reschedules() -> None:
    block = make_block(title="  Work  ", description="  Office context  ")
    overlapping = make_block(start_time=LocalTime(hour=17), end_time=LocalTime(hour=19))
    adjacent = make_block(start_time=LocalTime(hour=18), end_time=LocalTime(hour=19))

    assert block.title == "Work"
    assert block.description == "Office context"
    assert block.overlaps(overlapping)
    assert not block.overlaps(adjacent)

    block.reschedule(start_time=LocalTime(hour=9), end_time=LocalTime(hour=17))
    block.rename("  University  ")
    block.change_description(None)

    assert block.start_time == LocalTime(hour=9)
    assert block.end_time == LocalTime(hour=17)
    assert block.title == "University"
    assert block.description is None
