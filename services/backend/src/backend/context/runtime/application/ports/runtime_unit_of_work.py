from __future__ import annotations

from typing import Protocol

from backend.context.runtime.application.ports.runtime_repository import (
    RuntimeRepository,
)


class RuntimeUnitOfWork(Protocol):
    runtime_repository: RuntimeRepository