from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from types import TracebackType
from typing import Protocol, Self

from direttore.orchestration.base_classes.repo import TrackingRepository
from direttore.orchestration.base_types.message import DomainEvent


class AbstractUnitOfWork(ABC):
    """
    Base framework-owned Unit of Work lifecycle.

    Concrete Unit of Work implementations must implement the low-level session
    and transaction primitives:

        enter_session()
        exit_session()
        commit()
        rollback()

    The framework owns the async context manager protocol:

        async with uow:
            ...

    It means concrete UoWs should not usually override __aenter__ or __aexit__.
    Engines use the context manager to open the execution/session boundary and
    to commit or rollback according to the concrete UoW type.

    Command UoWs commit on successful execution.
    Query UoWs do not commit on successful execution.

    Typical concrete implementation shape:

        class SqlCommandUnitOfWork(AbstractCommandUnitOfWork, AppCommandUoWPort):
            def __init__(self, session_holder: ExecutionSessionHolder[Session]):
                self._session_holder = session_holder
                self.orders = SqlOrderRepository(session_holder)

            async def enter_session(self) -> None:
                ...

            async def exit_session(self) -> None:
                ...

            async def commit(self) -> None:
                await self._session_holder.session.commit()

            async def rollback(self) -> None:
                await self._session_holder.session.rollback()

            def _iter_repositories(self) -> Iterable[TrackingRepository]:
                return (self.orders,)

    Application-layer UoW ports should normally be Protocols and should not
    inherit from this abstract class. Concrete infrastructure UoWs should inherit
    from both the application port and the framework abstract UoW.
    """

    async def __aenter__(self) -> Self:
        await self.enter_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        try:
            if exc_type is None:
                if self._commit_on_success:
                    await self.commit()
            else:
                await self.rollback()
        finally:
            await self.exit_session()

        return False

    @property
    @abstractmethod
    def _commit_on_success(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def enter_session(self) -> None:
        """
        Open or enter the current UoW session boundary.

        Implement this method when the concrete UoW owns a real session lifecycle.

        Examples:
            - open a DB session
            - begin a logical in-memory execution scope
            - assert that a session holder has an attached session
            - initialize per-execution adapter state

        In simple in-memory implementations this method may be a no-op:

            async def enter_session(self) -> None:
                return None

        Do not commit or rollback here.
        """
        raise NotImplementedError

    @abstractmethod
    async def exit_session(self) -> None:
        """
        Close or leave the current UoW session boundary.

        This method is always called by __aexit__, even after rollback/commit
        failures where possible.

        Examples:
            - close a DB session
            - release a connection
            - detach or clear per-execution state
            - no-op for externally owned session/session holder

        Do not commit or rollback here. Transaction outcome is handled by
        commit() or rollback().
        """
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit current transaction state.

        Command UoWs must implement real commit behavior.

        Query UoWs usually inherit the no-op implementation from
        AbstractQueryUnitOfWork and do not need to override this method.

        This method is called automatically by __aexit__ when:
            - no exception happened inside async with uow
            - _commit_on_success is True
        """
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """
        Roll back current transaction state.

        Command UoWs must implement real rollback behavior.

        Query UoWs usually inherit the no-op implementation from
        AbstractQueryUnitOfWork and do not need to override this method.

        This method is called automatically by __aexit__ when an exception
        escapes from async with uow.
        """
        raise NotImplementedError


class AbstractCommandUnitOfWork(AbstractUnitOfWork):
    """
    Framework abstract base for write-side Unit of Work implementations.

    Use this class for concrete UoWs that are passed to command handlers.

    Required concrete methods:
        enter_session()
        exit_session()
        commit()
        rollback()
        _iter_repositories()

    Framework-provided behavior:
        __aenter__()
        __aexit__()
        collect_new_events()
        clear_tracking()
        iter_tracking_repositories()

    Command UoW semantics:
        - commits on successful command execution
        - rolls back on failed command execution
        - exposes write-side repositories through an application-specific port
        - can load state needed to perform writes
        - can persist aggregates/entities
        - owns TrackingRepository instances for event collection

    Important layering rule:
        Do not make application ports inherit from AbstractCommandUnitOfWork.

        Prefer:

            class WarehouseCommandUnitOfWork(Protocol):
                warehouse: WarehouseWriteRepository

            class InMemoryWarehouseCommandUnitOfWork(
                AbstractCommandUnitOfWork,
                WarehouseCommandUnitOfWork,
            ):
                ...

    _iter_repositories() must return only repositories that participate in
    tracking and domain-event collection. Repositories returned from this method
    must be TrackingRepository instances.

    Example:

        class InMemoryWarehouseCommandUnitOfWork(
            AbstractCommandUnitOfWork,
            WarehouseCommandUnitOfWork,
        ):
            def __init__(self, database: InMemoryWarehouseDatabase, session: FakeSession):
                self._session = session
                self.warehouse = InMemoryWarehouseWriteRepository(database)

            async def enter_session(self) -> None:
                return None

            async def exit_session(self) -> None:
                return None

            async def commit(self) -> None:
                await self._session.commit()

            async def rollback(self) -> None:
                await self._session.rollback()

            def _iter_repositories(self) -> Iterable[TrackingRepository]:
                return (self.warehouse,)

    Command handlers should not call commit(), rollback(), enter_session(), or
    exit_session() manually. The command execution engine owns the lifecycle.
    """

    @property
    def _commit_on_success(self) -> bool:
        return True

    @abstractmethod
    def _iter_repositories(self) -> Iterable[TrackingRepository]:
        """
        Return tracking repositories owned by this command UoW.

        The command execution engine uses these repositories to collect domain
        events and clear aggregate tracking state.

        Return an empty iterable if this command UoW has no tracking
        repositories, although most command UoWs should normally have at least
        one write-side TrackingRepository.
        """
        raise NotImplementedError

    def iter_tracking_repositories(self) -> Iterable[TrackingRepository]:
        return self._iter_repositories()

    def collect_new_events(self) -> list[DomainEvent]:
        return self._collect_new_events_from_tracking_repositories()

    def _collect_new_events_from_tracking_repositories(self) -> list[DomainEvent]:
        events: list[DomainEvent] = []

        for repository in self.iter_tracking_repositories():
            events.extend(repository.collect_events())
            repository.clear_tracked()

        return events

    def clear_tracking(self) -> None:
        self._clear_tracking_repositories()

    def _clear_tracking_repositories(self) -> None:
        for repository in self.iter_tracking_repositories():
            repository.clear_tracked()


class AbstractQueryUnitOfWork(AbstractUnitOfWork):
    """
    Framework abstract base for read-side Unit of Work implementations.

    Use this class for concrete UoWs that are passed to query handlers.

    Required concrete methods:
        enter_session()
        exit_session()

    Usually not required:
        commit()
        rollback()

    AbstractQueryUnitOfWork provides no-op commit() and rollback(), because
    query execution is read-side execution and does not commit state changes.

    Query UoW semantics:
        - opens/enters a read session boundary
        - does not commit on successful execution
        - does not collect domain events
        - does not expose tracking repositories
        - exposes read-side repositories through an application-specific port

    Important layering rule:
        Do not make application ports inherit from AbstractQueryUnitOfWork.

        Prefer:

            class WarehouseQueryUnitOfWork(Protocol):
                warehouse: WarehouseReadRepository

            class InMemoryWarehouseQueryUnitOfWork(
                AbstractQueryUnitOfWork,
                WarehouseQueryUnitOfWork,
            ):
                ...

    Example:

        class InMemoryWarehouseQueryUnitOfWork(
            AbstractQueryUnitOfWork,
            WarehouseQueryUnitOfWork,
        ):
            def __init__(self, database: InMemoryWarehouseDatabase, session: FakeSession):
                self._session = session
                self.warehouse = InMemoryWarehouseReadRepository(database)

            async def enter_session(self) -> None:
                return None

            async def exit_session(self) -> None:
                return None

    Query handlers should not call commit(), rollback(), enter_session(), or
    exit_session() manually. The query execution engine owns the lifecycle.
    """

    @property
    def _commit_on_success(self) -> bool:
        return False

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    def clear_tracking(self) -> None:
        return None


class AbstractOrchestrationUnitOfWork(AbstractCommandUnitOfWork):
    """
    Backward-compatible alias for the old write-side UoW contract.

    Deprecated:
        Prefer AbstractCommandUnitOfWork for command handlers and
        AbstractQueryUnitOfWork for query handlers.
    """

    pass


class UnitOfWorkFactoryPort(Protocol):
    def __call__(self) -> AbstractUnitOfWork:
        raise NotImplementedError


class CommandUnitOfWorkFactoryPort(Protocol):
    def __call__(self) -> AbstractCommandUnitOfWork:
        raise NotImplementedError


class QueryUnitOfWorkFactoryPort(Protocol):
    def __call__(self) -> AbstractQueryUnitOfWork:
        raise NotImplementedError


class OrchestrationUnitOfWorkFactoryPort(Protocol):
    """
    Backward-compatible factory alias.

    Deprecated:
        Prefer CommandUnitOfWorkFactoryPort.
    """

    def __call__(self) -> AbstractOrchestrationUnitOfWork:
        raise NotImplementedError