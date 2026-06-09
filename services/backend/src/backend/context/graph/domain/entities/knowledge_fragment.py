from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..value_objects import KnowledgeFragmentStatus


@dataclass(kw_only=True, slots=True)
class KnowledgeFragment:
    user_id: UUID
    node_id: UUID
    title: str
    content: str
    status: KnowledgeFragmentStatus = KnowledgeFragmentStatus.ACTIVE
    tags: tuple[str, ...] = ()
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate_uuid(self.id, field_name="id")
        self._validate_uuid(self.user_id, field_name="user_id")
        self._validate_uuid(self.node_id, field_name="node_id")
        self._validate_utc_datetime(self.captured_at, field_name="captured_at")

        if not isinstance(self.status, KnowledgeFragmentStatus):
            raise ValueError("status must be KnowledgeFragmentStatus")

        self._validate_title(self.title)
        self.title = self.title.strip()

        self._validate_content(self.content)
        self.content = self.content.strip()

        self.tags = self._normalize_tags(self.tags)

    def rename(self, title: str) -> None:
        self._validate_title(title)
        self.title = title.strip()

    def change_content(self, content: str) -> None:
        self._validate_content(content)
        self.content = content.strip()

    def move_to_node(self, node_id: UUID) -> None:
        self._validate_uuid(node_id, field_name="node_id")
        self.node_id = node_id

    def replace_tags(self, tags: tuple[str, ...]) -> None:
        self.tags = self._normalize_tags(tags)

    def change_captured_at(self, captured_at: datetime) -> None:
        self._validate_utc_datetime(captured_at, field_name="captured_at")
        self.captured_at = captured_at

    def archive(self) -> None:
        self.status = KnowledgeFragmentStatus.ARCHIVED

    def activate(self) -> None:
        self.status = KnowledgeFragmentStatus.ACTIVE

    def is_active(self) -> bool:
        return self.status == KnowledgeFragmentStatus.ACTIVE

    @staticmethod
    def _validate_uuid(value: UUID, *, field_name: str) -> None:
        if not isinstance(value, UUID):
            raise ValueError(f"{field_name} must be UUID")

    @staticmethod
    def _validate_title(title: str) -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title is required")

    @staticmethod
    def _validate_content(content: str) -> None:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content is required")

    @staticmethod
    def _validate_utc_datetime(value: datetime, *, field_name: str) -> None:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be datetime")

        if value.tzinfo is None:
            return

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must be UTC datetime or naive UTC datetime")

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
