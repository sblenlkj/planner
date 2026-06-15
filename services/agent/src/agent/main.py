from __future__ import annotations

from fastapi import FastAPI

from agent.api.exception_handlers import input_guard_blocked_exception_handler
from agent.conversation_agent.input_guard import InputGuardBlockedError
from agent.api import internal_conversations_router, internal_metrics_router, internal_workflows_router
from agent.bootstrap import lifespan
from agent.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.include_router(internal_conversations_router)
    app.include_router(internal_metrics_router)
    app.include_router(internal_workflows_router)

    app.add_exception_handler(
        InputGuardBlockedError,
        input_guard_blocked_exception_handler,
    )
    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "agent.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )