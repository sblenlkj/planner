from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from telegram_gateway.adapters.inbound.api import router
from telegram_gateway.adapters.inbound.exception_handlers import (
    register_exception_handlers,
)
from telegram_gateway.adapters.deduplication import TelegramUpdateDeduplicator
from telegram_gateway.adapters.outbound.http.agent_client import HttpAgentClient
from telegram_gateway.adapters.outbound.http.backend_client import HttpBackendClient
from telegram_gateway.adapters.outbound.cache.binding_cache import RedisBindingCache
from telegram_gateway.adapters.outbound.closed_session_publisher import (
    RedisClosedSessionPublisher,
)
from telegram_gateway.adapters.outbound.conversation_store import RedisConversationStore
from telegram_gateway.adapters.outbound.persistence.database import (
    create_engine,
    create_session_factory,
    initialize_database,
)
from telegram_gateway.adapters.outbound.http.mock_agent_client import MockAgentClient
from telegram_gateway.adapters.outbound.http.mock_backend_client import MockBackendClient
from telegram_gateway.adapters.outbound.cache.runtime_status_cache import (
    RedisRuntimeStatusCache,
)
from telegram_gateway.adapters.outbound.http.telegram_client import TelegramBotClient
from telegram_gateway.application.services.binding_service import BindingService
from telegram_gateway.application.services.conversation_service import ConversationService
from telegram_gateway.application.use_cases import (
    CloseTelegramSession,
    HandleTelegramMessage,
    SendBusinessMessage,
)
from telegram_gateway.settings import get_settings
from telegram_gateway.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        await initialize_database(engine)
        session_factory = create_session_factory(engine)

        redis = Redis.from_url(settings.redis_url, decode_responses=True)

        conversation_store = RedisConversationStore(
            redis=redis,
            conversation_ttl_seconds=settings.conversation_ttl_seconds,
        )
        binding_cache = RedisBindingCache(
            redis=redis,
            ttl_seconds=settings.binding_cache_ttl_seconds,
        )
        runtime_status_cache = RedisRuntimeStatusCache(
            redis=redis,
            ttl_seconds=settings.user_runtime_status_cache_ttl_seconds,
        )
        closed_session_publisher = RedisClosedSessionPublisher(
            redis=redis,
            maxlen=settings.closed_session_stream_maxlen,
        )
        update_deduplicator = TelegramUpdateDeduplicator(
            redis=redis,
            ttl_seconds=settings.telegram_update_deduplication_ttl_seconds,
        )

        if settings.use_mock_clients:
            agent_client = MockAgentClient(
                sleep_seconds=settings.mock_agent_sleep_seconds,
            )
            backend_client = MockBackendClient(
                default_runtime_status=settings.mock_user_runtime_status,
            )
        else:
            agent_client = HttpAgentClient(
                handle_onboarding_messages_url=(
                    settings.agent_handle_onboarding_messages_url
                ),
                handle_messages_url=settings.agent_handle_messages_url,
                internal_api_token=settings.internal_api_token,
                timeout_seconds=settings.agent_http_timeout_seconds,
            )
            backend_client = HttpBackendClient(
                create_user_url=settings.backend_create_business_user_url,
                get_user_runtime_status_url_template=(
                    settings.backend_get_user_runtime_status_url_template
                ),
                update_user_runtime_status_url_template=(
                    settings.backend_update_user_runtime_status_url_template
                ),
                update_user_last_session_at_url_template=(
                    settings.backend_update_user_last_session_at_url_template
                ),
                generate_day_schedule_url=settings.backend_generate_day_schedule_url,
                timeout_seconds=settings.http_timeout_seconds,
            )

        telegram_message_sender = TelegramBotClient(
            bot_token=settings.telegram_bot_token,
            timeout_seconds=settings.http_timeout_seconds,
        )

        binding_service = BindingService(
            backend_client=backend_client,
            binding_cache=binding_cache,
        )
        conversation_service = ConversationService(
            conversation_store=conversation_store,
            closed_session_publisher=closed_session_publisher,
            backend_client=backend_client,
        )

        app.state.settings = settings
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.redis = redis
        app.state.update_deduplicator = update_deduplicator

        app.state.handle_telegram_message = HandleTelegramMessage(
            agent_client=agent_client,
            backend_client=backend_client,
            telegram_message_sender=telegram_message_sender,
            binding_service=binding_service,
            conversation_service=conversation_service,
            runtime_status_cache=runtime_status_cache,
        )
        app.state.send_business_message = SendBusinessMessage(
            binding_service=binding_service,
            conversation_service=conversation_service,
            telegram_message_sender=telegram_message_sender,
        )
        app.state.close_telegram_session = CloseTelegramSession(
            binding_service=binding_service,
            conversation_service=conversation_service,
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

    settings = get_settings()
    uvicorn.run(
        "telegram_gateway.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )
