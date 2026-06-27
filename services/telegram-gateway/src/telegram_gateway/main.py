from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from telegram_gateway.adapters.inbound.api import router
from telegram_gateway.adapters.inbound.exception_handlers import register_exception_handlers
from telegram_gateway.bootstrap import AppContainer, create_container
from telegram_gateway.logging import configure_logging, get_logger
from telegram_gateway.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()  # type: ignore[call-arg]
    configure_logging(debug=settings.debug)
    log = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = await create_container(settings)
        container: AppContainer = app.state.container

        log.info("telegram_webhook.configured", enabled=container.settings.use_telegram, public_url=container.settings.telegram_webhook_public_url)

        if container.settings.use_telegram and container.settings.telegram_webhook_url:
            webhook_url = container.settings.telegram_webhook_url
            log.info("telegram_webhook.registration_started", webhook_url=webhook_url)
            await container.telegram_webhook_manager.delete_webhook(drop_pending_updates=True)
            await container.telegram_webhook_manager.set_webhook(
                webhook_url=webhook_url,
                secret_token=container.settings.telegram_webhook_secret,
                drop_pending_updates=True,
            )
            log.info("telegram_webhook.registration_finished", webhook_url=webhook_url)

        yield

        if container.settings.should_delete_telegram_webhook_on_shutdown:
            log.info("telegram_webhook.delete_started")
            await container.telegram_webhook_manager.delete_webhook(drop_pending_updates=True)
            log.info("telegram_webhook.delete_finished")

        await container.aclose()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.include_router(router)
    register_exception_handlers(app)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()  # type: ignore[call-arg]

    uvicorn.run(
        "telegram_gateway.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )
