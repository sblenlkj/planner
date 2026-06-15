from __future__ import annotations

from typing import Generic, TypeVar


TResource = TypeVar("TResource")


class ExecutionResourceHolder(Generic[TResource]):
    """
    Stores current execution-scoped resources.

    The holder object is stable and can be injected into long-lived objects:
    coordinators, UoW factories, adapters, services, or execution dependency
    factories.

    The actual resource object is execution-scoped:
    DirettoreApplication attaches it before command/query execution and detaches
    it after execution.

    The resource can be anything the final application needs:

        - a single database session;
        - a composite dataclass with several database sessions;
        - a session plus request metadata;
        - a session plus tracing resources;
        - any user-defined execution resource bundle.

    The framework does not inspect the resource object directly. Concrete
    applications decide how to extract sessions or other objects from it inside
    their coordinator/UoW factories.

    Tracing is intentionally not hardcoded into this holder. If tracing is
    enabled, a separate tracing adapter can extract a tracer/span object from
    the attached resources.
    """

    def __init__(self) -> None:
        self._resource: TResource | None = None

    @property
    def resource(self) -> TResource:
        if self._resource is None:
            raise RuntimeError("Execution resource is not attached.")

        return self._resource

    @property
    def session(self) -> TResource:
        """
        Backward-compatible alias for existing code.

        Existing integrations that treat the attached resource as a session can
        continue using holder.session. Newer integrations should prefer
        holder.resource when the attached object is a broader execution resource
        bundle.
        """
        return self.resource

    def attach(
        self,
        resource: TResource,
    ) -> None:
        if self._resource is not None:
            raise RuntimeError("Execution resource is already attached.")

        self._resource = resource

    def detach(self) -> None:
        self._resource = None

    def has_resource(self) -> bool:
        return self._resource is not None

    def has_session(self) -> bool:
        """
        Backward-compatible alias for existing code.
        """
        return self.has_resource()


class ExecutionSessionHolder(ExecutionResourceHolder[TResource]):
    """
    Backward-compatible name for ExecutionResourceHolder.

    Deprecated conceptually: new code should prefer ExecutionResourceHolder.
    Kept to avoid breaking existing imports and examples while the project
    migrates from "session holder" to "resource holder" terminology.
    """