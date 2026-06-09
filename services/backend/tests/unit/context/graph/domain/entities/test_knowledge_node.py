from uuid import UUID, uuid4

import pytest

from backend.context.graph.domain.entities import KnowledgeNode
from backend.context.graph.domain.value_objects import KnowledgeNodeStatus, KnowledgeNodeType


def test_create_root_node_with_defaults() -> None:
    user_id = uuid4()

    node = KnowledgeNode(user_id=user_id, title="Python")

    assert isinstance(node.id, UUID)
    assert node.user_id == user_id
    assert node.title == "Python"
    assert node.parent_id is None
    assert node.description is None
    assert node.node_type == KnowledgeNodeType.TOPIC
    assert node.status == KnowledgeNodeStatus.ACTIVE
    assert node.tags == ()
    assert node.is_root() is True
    assert node.is_active() is True


def test_create_child_node_with_explicit_fields_and_normalization() -> None:
    user_id = uuid4()
    parent_id = uuid4()

    node = KnowledgeNode(
        user_id=user_id,
        parent_id=parent_id,
        title="  AsyncIO  ",
        description="  Python asynchronous I/O knowledge.  ",
        node_type=KnowledgeNodeType.CONCEPT,
        status=KnowledgeNodeStatus.ACTIVE,
        tags=(" Python ", "ASYNCIO", "", "python", " event-loop "),
    )

    assert node.user_id == user_id
    assert node.parent_id == parent_id
    assert node.title == "AsyncIO"
    assert node.description == "Python asynchronous I/O knowledge."
    assert node.node_type == KnowledgeNodeType.CONCEPT
    assert node.status == KnowledgeNodeStatus.ACTIVE
    assert node.tags == ("python", "asyncio", "event-loop")
    assert node.is_root() is False


def test_blank_description_becomes_none() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python", description="   ")

    assert node.description is None


@pytest.mark.parametrize("title", ["", "   "])
def test_title_is_required(title: str) -> None:
    with pytest.raises(ValueError, match="title is required"):
        KnowledgeNode(user_id=uuid4(), title=title)


def test_title_must_be_string() -> None:
    with pytest.raises(ValueError, match="title is required"):
        KnowledgeNode(user_id=uuid4(), title=123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("id", {"id": "not-uuid"}),
        ("user_id", {"user_id": "not-uuid"}),
        ("parent_id", {"parent_id": "not-uuid"}),
    ],
)
def test_uuid_fields_must_be_uuid(field_name: str, kwargs: dict[str, object]) -> None:
    data: dict[str, object] = {
        "user_id": uuid4(),
        "title": "Python",
    }
    data.update(kwargs)

    with pytest.raises(ValueError, match=f"{field_name} must be UUID"):
        KnowledgeNode(**data)  # type: ignore[arg-type]


def test_node_cannot_be_its_own_parent_on_create() -> None:
    node_id = uuid4()

    with pytest.raises(ValueError, match="node cannot be its own parent"):
        KnowledgeNode(id=node_id, user_id=uuid4(), parent_id=node_id, title="Python")


def test_node_type_must_be_knowledge_node_type() -> None:
    with pytest.raises(ValueError, match="node_type must be KnowledgeNodeType"):
        KnowledgeNode(user_id=uuid4(), title="Python", node_type="topic")  # type: ignore[arg-type]


def test_status_must_be_knowledge_node_status() -> None:
    with pytest.raises(ValueError, match="status must be KnowledgeNodeStatus"):
        KnowledgeNode(user_id=uuid4(), title="Python", status="active")  # type: ignore[arg-type]


def test_description_must_be_string_or_none() -> None:
    with pytest.raises(ValueError, match="text field must be str or None"):
        KnowledgeNode(user_id=uuid4(), title="Python", description=123)  # type: ignore[arg-type]


def test_tags_must_be_tuple() -> None:
    with pytest.raises(ValueError, match="tags must be tuple"):
        KnowledgeNode(user_id=uuid4(), title="Python", tags=["python"])  # type: ignore[arg-type]


def test_tags_must_contain_only_strings() -> None:
    with pytest.raises(ValueError, match="tags must contain only str values"):
        KnowledgeNode(user_id=uuid4(), title="Python", tags=("python", 123))  # type: ignore[arg-type]


def test_rename_changes_trimmed_title() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    node.rename("  AsyncIO  ")

    assert node.title == "AsyncIO"


def test_rename_rejects_blank_title() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    with pytest.raises(ValueError, match="title is required"):
        node.rename("   ")


def test_change_description_normalizes_text() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    node.change_description("  Backend programming language.  ")
    assert node.description == "Backend programming language."

    node.change_description("   ")
    assert node.description is None

    node.change_description(None)
    assert node.description is None


def test_change_type_updates_type() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    node.change_type(KnowledgeNodeType.SKILL)

    assert node.node_type == KnowledgeNodeType.SKILL


def test_change_type_rejects_invalid_type() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    with pytest.raises(ValueError, match="node_type must be KnowledgeNodeType"):
        node.change_type("skill")  # type: ignore[arg-type]


def test_move_to_parent_and_move_to_root() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="AsyncIO")
    parent_id = uuid4()

    node.move_to_parent(parent_id)
    assert node.parent_id == parent_id
    assert node.is_root() is False

    node.move_to_root()
    assert node.parent_id is None
    assert node.is_root() is True


def test_move_to_parent_rejects_invalid_parent_id() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="AsyncIO")

    with pytest.raises(ValueError, match="parent_id must be UUID"):
        node.move_to_parent("not-uuid")  # type: ignore[arg-type]


def test_move_to_parent_rejects_self_parent() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="AsyncIO")

    with pytest.raises(ValueError, match="node cannot be its own parent"):
        node.move_to_parent(node.id)


def test_replace_tags_normalizes_tags() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    node.replace_tags((" Python ", "python", " Backend ", ""))

    assert node.tags == ("python", "backend")


def test_archive_and_activate() -> None:
    node = KnowledgeNode(user_id=uuid4(), title="Python")

    node.archive()
    assert node.status == KnowledgeNodeStatus.ARCHIVED
    assert node.is_active() is False

    node.activate()
    assert node.status == KnowledgeNodeStatus.ACTIVE
    assert node.is_active() is True
