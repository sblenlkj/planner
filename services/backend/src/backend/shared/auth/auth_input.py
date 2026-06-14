from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackendAuthInput:
    authorization_header: str | None = None