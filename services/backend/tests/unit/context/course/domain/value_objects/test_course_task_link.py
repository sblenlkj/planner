import pytest

from backend.context.course.domain.value_objects import CourseTaskLink


def test_course_task_link_normalizes_values() -> None:
    link = CourseTaskLink(
        description="  FastAPI article  ",
        url=" https://example.com/fastapi ",
    )

    assert link.description == "FastAPI article"
    assert link.url == "https://example.com/fastapi"


def test_course_task_link_allows_missing_url() -> None:
    link = CourseTaskLink(
        description="Book on my desk",
    )

    assert link.description == "Book on my desk"
    assert link.url is None


def test_course_task_link_requires_description() -> None:
    with pytest.raises(ValueError):
        CourseTaskLink(description="   ")
