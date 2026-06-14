from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from direttore import (
    Container,
    ModularDirettoreWithSimpleSession,
)

from backend.bootstrap.container import build_container
from backend.bootstrap.contexts import build_contexts
from backend.bootstrap.coordinator import BackendUnitOfWorkCoordinator
from backend.bootstrap.execution_dependencies import (
    build_execution_dependency_registry,
)
from backend.bootstrap.settings import get_settings
from backend.shared.logging import configure_logging


@dataclass(frozen=True, slots=True)
class BackendDirettoreApp:
    direttore: ModularDirettoreWithSimpleSession[
        AsyncSession,
        None,
        None,
        None,
        None,
    ]
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    container: Container


@lru_cache(maxsize=1)
def get_backend_direttore_app() -> BackendDirettoreApp:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    container = build_container()

    def coordinator_factory(
        session: AsyncSession,
    ) -> BackendUnitOfWorkCoordinator:
        return BackendUnitOfWorkCoordinator(session=session)

    direttore = ModularDirettoreWithSimpleSession[
        AsyncSession,
        None,
        None,
        None,
        None,
    ](
        session_factory=session_factory,
        coordinator_factory=coordinator_factory,
        contexts=build_contexts(),
        container=container,
        execution_dependency_registry=build_execution_dependency_registry(),
    )

    return BackendDirettoreApp(
        direttore=direttore,
        engine=engine,
        session_factory=session_factory,
        container=container,
    )


def get_direttore() -> ModularDirettoreWithSimpleSession[
    AsyncSession,
    None,
    None,
    None,
    None,
]:
    return get_backend_direttore_app().direttore