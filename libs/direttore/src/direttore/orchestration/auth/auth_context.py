from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from direttore.orchestration.auth.access_tags import AccessTags


class SupportsAccessTags(Protocol):
    access_tags: Collection[str]


@dataclass(frozen=True, slots=True)
class AnonymousAuthContext:
    access_tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class SystemAuthContext:
    access_tags: frozenset[str] = field(
        default_factory=lambda: frozenset({AccessTags.SYSTEM})
    )
    system_name: str = "system"


@dataclass(frozen=True, slots=True)
class AuthResolutionContext:
    metadata: Mapping[str, Any] = field(default_factory=dict)