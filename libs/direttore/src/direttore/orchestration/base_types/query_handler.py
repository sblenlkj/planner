from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from direttore.orchestration.base_classes.uow import (
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.base_types.message import Query


AuthT = TypeVar("AuthT")


@dataclass(slots=True)
class QueryHandlerContext(Generic[AuthT]):
    """
Runtime context passed to every AbstractQueryHandler.

This context represents the read-side execution boundary for a single query
handler call. It is created by the query execution engine and should be treated
as framework-owned runtime state.

Attributes:
    uow:
        Current query Unit of Work.

        The concrete type is application-specific. In a bounded context, users
        normally narrow this field in their own context subclass:

            class WarehouseQueryHandlerContext(
                QueryHandlerContext[ExampleAuth],
            ):
                uow: WarehouseQueryUnitOfWork

        Query handlers use this UoW to access read-side repositories or read
        models. Query UoWs should not expose write methods, tracking
        repositories, domain-event collection, or mutation-oriented APIs.

        Query handlers must not call commit(), rollback(), enter_session(), or
        exit_session() manually. The query execution engine owns the UoW
        lifecycle. A query UoW normally does not commit on successful execution.

    auth:
        Resolved auth object for the current execution, or None when the auth
        pipeline is disabled.

        The concrete auth type is user-defined. A project can narrow it in its
        own context subclass:

            class WarehouseQueryHandlerContext(
                QueryHandlerContext[ExampleAuth],
            ):
                auth: ExampleAuth | None

        If a query requires authenticated data, it should handle the None case
        explicitly or rely on allowed_access_tags plus a configured access
        checker to reject unauthenticated execution before the handler is called.

QueryHandlerContext deliberately has no event queue and no runtime command
invocation API. Query handlers are read-side handlers: they should read data and
return a result, not mutate state, dispatch events, or orchestrate write-side
flows.
"""
    uow: AbstractQueryUnitOfWork
    auth: AuthT | None = None


@dataclass(frozen=True, slots=True)
class QueryHandlerConfig:
    cache_handler: bool = False
    allowed_access_tags: frozenset[str] | None = None


class QueryHandler:
    query_handler_key: ClassVar[str | None] = None


class AbstractQueryHandler(QueryHandler, ABC):
    @abstractmethod
    async def __call__(
        self,
        query: Query,
        context: QueryHandlerContext[Any],
    ) -> Any:
        raise NotImplementedError