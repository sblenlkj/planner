from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..value_objects import KnowledgeNodeStatus, KnowledgeNodeType


@dataclass(kw_only=True, slots=True)
class KnowledgeNode:
    user_id: UUID
    title: str
    parent_id: UUID | None = None
    description: str | None = None
    node_type: KnowledgeNodeType = KnowledgeNodeType.TOPIC
    status: KnowledgeNodeStatus = KnowledgeNodeStatus.ACTIVE
    tags: tuple[str, ...] = ()
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate_uuid(self.id, field_name="id")
        self._validate_uuid(self.user_id, field_name="user_id")

        if self.parent_id is not None:
            self._validate_uuid(self.parent_id, field_name="parent_id")

            if self.parent_id == self.id:
                raise ValueError("node cannot be its own parent")

        if not isinstance(self.node_type, KnowledgeNodeType):
            raise ValueError("node_type must be KnowledgeNodeType")

        if not isinstance(self.status, KnowledgeNodeStatus):
            raise ValueError("status must be KnowledgeNodeStatus")

        self._validate_title(self.title)
        self.title = self.title.strip()

        self.description = self._normalize_optional_text(self.description)
        self.tags = self._normalize_tags(self.tags)

    def rename(self, title: str) -> None:
        self._validate_title(title)
        self.title = title.strip()

    def change_description(self, description: str | None) -> None:
        self.description = self._normalize_optional_text(description)

    def change_type(self, node_type: KnowledgeNodeType) -> None:
        if not isinstance(node_type, KnowledgeNodeType):
            raise ValueError("node_type must be KnowledgeNodeType")

        self.node_type = node_type

    def move_to_parent(self, parent_id: UUID) -> None:
        self._validate_uuid(parent_id, field_name="parent_id")

        if parent_id == self.id:
            raise ValueError("node cannot be its own parent")

        self.parent_id = parent_id

    def move_to_root(self) -> None:
        self.parent_id = None

    def replace_tags(self, tags: tuple[str, ...]) -> None:
        self.tags = self._normalize_tags(tags)

    def archive(self) -> None:
        self.status = KnowledgeNodeStatus.ARCHIVED

    def activate(self) -> None:
        self.status = KnowledgeNodeStatus.ACTIVE

    def is_root(self) -> bool:
        return self.parent_id is None

    def is_active(self) -> bool:
        return self.status == KnowledgeNodeStatus.ACTIVE

    @staticmethod
    def _validate_uuid(value: UUID, *, field_name: str) -> None:
        if not isinstance(value, UUID):
            raise ValueError(f"{field_name} must be UUID")

    @staticmethod
    def _validate_title(title: str) -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title is required")

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError("text field must be str or None")

        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(tags, tuple):
            raise ValueError("tags must be tuple[str, ...]")

        normalized: list[str] = []
        seen: set[str] = set()

        for tag in tags:
            if not isinstance(tag, str):
                raise ValueError("tags must contain only str values")

            normalized_tag = tag.strip().lower()

            if not normalized_tag or normalized_tag in seen:
                continue

            normalized.append(normalized_tag)
            seen.add(normalized_tag)

        return tuple(normalized)
