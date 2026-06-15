from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from telegram_gateway.adapters.inbound.api import router
from telegram_gateway.adapters.inbound.exception_handlers import register_exception_handlers
from telegram_gateway.adapters.outbound.database import (
    create_engine,
    create_session_factory,
    initialize_database,
)
from telegram_gateway.adapters.outbound.http.agent_client import HttpAgentClient
from telegram_gateway.adapters.outbound.http.backend_client import HttpBackendClient
from telegram_gateway.adapters.outbound.http.telegram_client import TelegramBotClient
from telegram_gateway.adapters.outbound.redis_conversation_store import (
    RedisConversationStore,
)
from telegram_gateway.adapters.outbound.unit_of_work import SqlAlchemyUnitOfWork
from telegram_gateway.application.use_cases import (
    AttachTelegram,
    AuthenticateBusinessUser,
    CloseAgentSession,
    SendAgentMessage,
    SendTelegramNotification,
    GetAgentSession,
)
from telegram_gateway.logging import configure_logging
from telegram_gateway.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()  # type: ignore[call-arg]
    configure_logging(debug=settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        await initialize_database(engine)

        session_factory = create_session_factory(engine)
        redis = Redis.from_url(
            settings.redis_url,
            decode_responses=False,
        )

        backend_client = HttpBackendClient(
            get_user_url_template=settings.backend_get_user_url_template,
            timeout_seconds=settings.http_timeout_seconds,
        )

        agent_client = HttpAgentClient(
            handle_messages_url=settings.agent_handle_messages_url,
            close_session_url=settings.agent_close_session_url,
            internal_api_token=settings.internal_api_token,
            timeout_seconds=settings.agent_http_timeout_seconds,
        )

        telegram_message_sender = TelegramBotClient(
            bot_token=settings.telegram_bot_token,
            timeout_seconds=settings.http_timeout_seconds,
        )

        conversation_store = RedisConversationStore(
            redis=redis,
            ttl_seconds=settings.session_ttl_seconds,
        )

        def uow_factory() -> SqlAlchemyUnitOfWork:
            return SqlAlchemyUnitOfWork(session_factory)

        app.state.settings = settings
        app.state.engine = engine
        app.state.redis = redis
        app.state.session_factory = session_factory
        app.state.uow_factory = uow_factory

        app.state.authenticate_business_user_use_case = AuthenticateBusinessUser(
            backend_client=backend_client,
        )
        app.state.attach_telegram_use_case = AttachTelegram()
        app.state.send_agent_message_use_case = SendAgentMessage(
            agent_client=agent_client,
            conversation_store=conversation_store,
        )
        app.state.close_agent_session_use_case = CloseAgentSession(
            agent_client=agent_client,
            conversation_store=conversation_store,
        )
        app.state.send_telegram_notification_use_case = SendTelegramNotification(
            conversation_store=conversation_store,
            telegram_message_sender=telegram_message_sender,
        )

        app.state.get_agent_session_use_case = GetAgentSession(
            conversation_store=conversation_store,
        )

        yield

        await redis.aclose()
        await engine.dispose()

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
