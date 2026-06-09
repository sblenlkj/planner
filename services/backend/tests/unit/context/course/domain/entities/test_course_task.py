from uuid import UUID, uuid4

import pytest

from backend.context.course.domain.entities.course_task import CourseTask
from backend.context.course.domain.value_objects import (
    CourseTaskLink,
    CourseTaskPriority,
    CourseTaskProgress,
    CourseTaskStatus,
)


def test_create_course_task() -> None:
    course_id = uuid4()

    task = CourseTask.create(
        course_id=course_id,
        title="  Read chapter 1  ",
        description="  Read the first chapter carefully  ",
    )

    assert isinstance(task.id, UUID)
    assert task.course_id == course_id
    assert task.title == "Read chapter 1"
    assert task.description == "Read the first chapter carefully"
    assert task.priority == CourseTaskPriority.normal()
    assert task.status == CourseTaskStatus.PENDING
    assert task.progress == CourseTaskProgress.zero()
    assert task.next_task_id is None
    assert task.links == []


def test_create_course_task_requires_title() -> None:
    with pytest.raises(ValueError):
        CourseTask.create(
            course_id=uuid4(),
            title="   ",
            description="Read the first chapter carefully",
        )


def test_create_course_task_requires_description() -> None:
    with pytest.raises(ValueError):
        CourseTask.create(
            course_id=uuid4(),
            title="Read chapter 1",
            description="   ",
        )


def test_course_task_cannot_reference_itself_as_next_task() -> None:
    task_id = uuid4()

    with pytest.raises(ValueError):
        CourseTask.create(
            id=task_id,
            course_id=uuid4(),
            title="Read chapter 1",
            description="Read the first chapter carefully",
            next_task_id=task_id,
        )


def test_set_next_task() -> None:
    task = CourseTask.create(
        course_id=uuid4(),
        title="Read chapter 1",
        description="Read the first chapter carefully",
    )
    next_task_id = uuid4()

    task.set_next_task(next_task_id)

    assert task.next_task_id == next_task_id


def test_add_link() -> None:
    task = CourseTask.create(
        course_id=uuid4(),
        title="Read article",
        description="Read article about FastAPI",
    )

    link = task.add_link(
        description="FastAPI article",
        url=" https://example.com/fastapi ",
    )

    assert link == CourseTaskLink(
        description="FastAPI article",
        url="https://example.com/fastapi",
    )
    assert task.links == [link]


def test_change_progress_starts_pending_task() -> None:
    task = CourseTask.create(
        course_id=uuid4(),
        title="Read chapter 1",
        description="Read the first chapter carefully",
    )

    task.change_progress(CourseTaskProgress.percent(30))

    assert task.progress == CourseTaskProgress.percent(30)
    assert task.status == CourseTaskStatus.IN_PROGRESS


def test_complete_task_sets_progress_to_complete() -> None:
    task = CourseTask.create(
        course_id=uuid4(),
        title="Read chapter 1",
        description="Read the first chapter carefully",
    )

    task.start()
    task.complete()

    assert task.progress == CourseTaskProgress.complete()
    assert task.status == CourseTaskStatus.COMPLETED


def test_skip_task() -> None:
    task = CourseTask.create(
        course_id=uuid4(),
        title="Read chapter 1",
        description="Read the first chapter carefully",
    )

    task.skip()

    assert task.status == CourseTaskStatus.SKIPPED
