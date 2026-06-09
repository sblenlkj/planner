from backend.context.graph.domain.value_objects import (
    KnowledgeFragmentStatus,
    KnowledgeNodeStatus,
    KnowledgeNodeType,
)


def test_knowledge_node_type_values() -> None:
    assert KnowledgeNodeType.AREA == "area"
    assert KnowledgeNodeType.TOPIC == "topic"
    assert KnowledgeNodeType.CONCEPT == "concept"
    assert KnowledgeNodeType.SKILL == "skill"
    assert KnowledgeNodeType.RESOURCE == "resource"


def test_knowledge_node_status_values() -> None:
    assert KnowledgeNodeStatus.ACTIVE == "active"
    assert KnowledgeNodeStatus.ARCHIVED == "archived"


def test_knowledge_fragment_status_values() -> None:
    assert KnowledgeFragmentStatus.ACTIVE == "active"
    assert KnowledgeFragmentStatus.ARCHIVED == "archived"
