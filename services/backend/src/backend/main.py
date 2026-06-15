from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from backend.bootstrap.direttore import (
    get_backend_direttore_app,
)
from backend.context.runtime.adapters.api_scheduler_adapter import (
    ApschedulerApiSchedulerAdapter,
)
from backend.context.runtime.adapters.inbound.api import router as runtime_router
from backend.context.user.adapters.inbound.api import router as user_router
from backend.context.course.adapters.inbound.api import router as course_router
from backend.context.schedule.adapters.inbound.api import router as schedule_router
from backend.context.analytics.adapters.inbound.api import router as analytics_router

from backend.context.runtime.application.use_cases import (
    RecoverActiveFutureRemindersCommand
)

from backend.context.runtime.application.runtime_jobs import (
    ENSURE_RUNTIME_JOBS_HANDLER_KEY,
)

from backend.shared.adapters.persistence.base import Base
import backend.bootstrap.models  # noqa: F401
from backend.shared.application.ports.api_scheduler import ApiSchedulerPort
from backend.shared.logging import get_logger


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    backend_app = get_backend_direttore_app()
    app.state.backend = backend_app
    app.state.direttore = backend_app.direttore
    app.state.container = backend_app.container

    async with backend_app.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    logger.info("backend_database_schema_ensured")

    api_scheduler = backend_app.container.get(ApiSchedulerPort)

    if isinstance(api_scheduler, ApschedulerApiSchedulerAdapter):
        api_scheduler.bind_direttore(backend_app.direttore)

    await backend_app.direttore.handle_by_key(
        key=ENSURE_RUNTIME_JOBS_HANDLER_KEY,
        payload={"register_scheduler_jobs": True},
    )
    await backend_app.direttore.handle(
        RecoverActiveFutureRemindersCommand(),
    )

    backend_app.direttore.validate_command_handlers()
    backend_app.direttore.validate_event_handlers()

    logger.info("backend_runtime_jobs_ensured")

    if isinstance(api_scheduler, ApschedulerApiSchedulerAdapter):
        api_scheduler.start()

    logger.info("backend_started")

    try:
        yield
    finally:
        if isinstance(api_scheduler, ApschedulerApiSchedulerAdapter):
            api_scheduler.shutdown()

        await backend_app.engine.dispose()

        logger.info("backend_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Planner Backend",
        lifespan=lifespan,
    )

    app.include_router(user_router)
    app.include_router(runtime_router)
    app.include_router(course_router)
    app.include_router(schedule_router)
    app.include_router(analytics_router)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    from backend.bootstrap.settings import get_settings

    settings = get_settings()

    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()