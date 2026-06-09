from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from backend.context.graph.domain.entities import KnowledgeFragment
from backend.context.graph.domain.value_objects import KnowledgeFragmentStatus


def test_create_fragment_with_defaults() -> None:
    user_id = uuid4()
    node_id = uuid4()

    fragment = KnowledgeFragment(
        user_id=user_id,
        node_id=node_id,
        title="AsyncIO notes",
        content="User learned event loop basics.",
    )

    assert isinstance(fragment.id, UUID)
    assert fragment.user_id == user_id
    assert fragment.node_id == node_id
    assert fragment.title == "AsyncIO notes"
    assert fragment.content == "User learned event loop basics."
    assert fragment.status == KnowledgeFragmentStatus.ACTIVE
    assert fragment.tags == ()
    assert isinstance(fragment.captured_at, datetime)
    assert fragment.captured_at.tzinfo == UTC
    assert fragment.is_active() is True


def test_create_fragment_with_explicit_fields_and_normalization() -> None:
    captured_at = datetime(2026, 6, 9, 12, 30, tzinfo=UTC)

    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="  Python course fragment  ",
        content="  User liked AsyncIO and FastAPI parts.  ",
        status=KnowledgeFragmentStatus.ACTIVE,
        tags=(" Python ", "ASYNCIO", "", "python", " fastapi "),
        captured_at=captured_at,
    )

    assert fragment.title == "Python course fragment"
    assert fragment.content == "User liked AsyncIO and FastAPI parts."
    assert fragment.status == KnowledgeFragmentStatus.ACTIVE
    assert fragment.tags == ("python", "asyncio", "fastapi")
    assert fragment.captured_at == captured_at


@pytest.mark.parametrize("title", ["", "   "])
def test_title_is_required(title: str) -> None:
    with pytest.raises(ValueError, match="title is required"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title=title,
            content="Valid content.",
        )


def test_title_must_be_string() -> None:
    with pytest.raises(ValueError, match="title is required"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title=123,  # type: ignore[arg-type]
            content="Valid content.",
        )


@pytest.mark.parametrize("content", ["", "   "])
def test_content_is_required(content: str) -> None:
    with pytest.raises(ValueError, match="content is required"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="Valid title",
            content=content,
        )


def test_content_must_be_string() -> None:
    with pytest.raises(ValueError, match="content is required"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="Valid title",
            content=123,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("id", {"id": "not-uuid"}),
        ("user_id", {"user_id": "not-uuid"}),
        ("node_id", {"node_id": "not-uuid"}),
    ],
)
def test_uuid_fields_must_be_uuid(field_name: str, kwargs: dict[str, object]) -> None:
    data: dict[str, object] = {
        "user_id": uuid4(),
        "node_id": uuid4(),
        "title": "AsyncIO fragment",
        "content": "User learned event loop basics.",
    }
    data.update(kwargs)

    with pytest.raises(ValueError, match=f"{field_name} must be UUID"):
        KnowledgeFragment(**data)  # type: ignore[arg-type]


def test_status_must_be_knowledge_fragment_status() -> None:
    with pytest.raises(ValueError, match="status must be KnowledgeFragmentStatus"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="AsyncIO fragment",
            content="User learned event loop basics.",
            status="active",  # type: ignore[arg-type]
        )


def test_captured_at_must_be_datetime() -> None:
    with pytest.raises(ValueError, match="captured_at must be datetime"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="AsyncIO fragment",
            content="User learned event loop basics.",
            captured_at="2026-06-09",  # type: ignore[arg-type]
        )


def test_captured_at_accepts_naive_datetime_as_naive_utc() -> None:
    captured_at = datetime(2026, 6, 9, 12, 30)

    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
        captured_at=captured_at,
    )

    assert fragment.captured_at == captured_at


def test_captured_at_rejects_non_utc_timezone() -> None:
    captured_at = datetime(2026, 6, 9, 12, 30, tzinfo=timezone(timedelta(hours=2)))

    with pytest.raises(ValueError, match="captured_at must be UTC datetime or naive UTC datetime"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="AsyncIO fragment",
            content="User learned event loop basics.",
            captured_at=captured_at,
        )


def test_tags_must_be_tuple() -> None:
    with pytest.raises(ValueError, match="tags must be tuple"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="AsyncIO fragment",
            content="User learned event loop basics.",
            tags=["python"],  # type: ignore[arg-type]
        )


def test_tags_must_contain_only_strings() -> None:
    with pytest.raises(ValueError, match="tags must contain only str values"):
        KnowledgeFragment(
            user_id=uuid4(),
            node_id=uuid4(),
            title="AsyncIO fragment",
            content="User learned event loop basics.",
            tags=("python", 123),  # type: ignore[arg-type]
        )


def test_rename_changes_trimmed_title() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    fragment.rename("  Python course summary  ")

    assert fragment.title == "Python course summary"


def test_rename_rejects_blank_title() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    with pytest.raises(ValueError, match="title is required"):
        fragment.rename("   ")


def test_change_content_changes_trimmed_content() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    fragment.change_content("  User learned async/await and event loop basics.  ")

    assert fragment.content == "User learned async/await and event loop basics."


def test_change_content_rejects_blank_content() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    with pytest.raises(ValueError, match="content is required"):
        fragment.change_content("   ")


def test_move_to_node_changes_node_id() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )
    new_node_id = uuid4()

    fragment.move_to_node(new_node_id)

    assert fragment.node_id == new_node_id


def test_move_to_node_rejects_invalid_node_id() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    with pytest.raises(ValueError, match="node_id must be UUID"):
        fragment.move_to_node("not-uuid")  # type: ignore[arg-type]


def test_replace_tags_normalizes_tags() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    fragment.replace_tags((" Python ", "python", " AsyncIO ", ""))

    assert fragment.tags == ("python", "asyncio")


def test_change_captured_at_updates_timestamp() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )
    captured_at = datetime(2026, 6, 9, 12, 30, tzinfo=UTC)

    fragment.change_captured_at(captured_at)

    assert fragment.captured_at == captured_at


def test_change_captured_at_rejects_invalid_datetime() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    with pytest.raises(ValueError, match="captured_at must be datetime"):
        fragment.change_captured_at("2026-06-09")  # type: ignore[arg-type]


def test_archive_and_activate() -> None:
    fragment = KnowledgeFragment(
        user_id=uuid4(),
        node_id=uuid4(),
        title="AsyncIO fragment",
        content="User learned event loop basics.",
    )

    fragment.archive()
    assert fragment.status == KnowledgeFragmentStatus.ARCHIVED
    assert fragment.is_active() is False

    fragment.activate()
    assert fragment.status == KnowledgeFragmentStatus.ACTIVE
    assert fragment.is_active() is True
