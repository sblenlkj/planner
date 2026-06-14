from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from backend.shared.application import (
    ADMIN_ACCESS_TAG,
    SYSTEM_ACCESS_TAG,
    USER_ACCESS_TAG,
)


@dataclass(frozen=True, slots=True)
class BackendAuth:
    access_tags: frozenset[str]
    user_id: UUID | None = None
    system_name: str | None = None

    @classmethod
    def user(
        cls,
        *,
        user_id: UUID,
    ) -> "BackendAuth":
        return cls(
            user_id=user_id,
            access_tags=frozenset({USER_ACCESS_TAG}),
        )

    @classmethod
    def admin(
        cls,
        *,
        user_id: UUID,
    ) -> "BackendAuth":
        return cls(
            user_id=user_id,
            access_tags=frozenset({ADMIN_ACCESS_TAG}),
        )

    @classmethod
    def system(
        cls,
        *,
        system_name: str = "system",
    ) -> "BackendAuth":
        return cls(
            system_name=system_name,
            access_tags=frozenset({SYSTEM_ACCESS_TAG}),
        )


@dataclass(frozen=True, slots=True)
class AnonymousBackendAuth:
    access_tags: frozenset[str] = field(default_factory=frozenset)