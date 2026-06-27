from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from telegram_gateway.adapters.outbound.database import (
    create_engine,
    create_session_factory,
    initialize_database,
)
from telegram_gateway.adapters.outbound.http.agent_client import HttpAgentClient
from telegram_gateway.adapters.outbound.http.backend_client import HttpBackendClient
from telegram_gateway.adapters.outbound.http.telegram_client import TelegramBotClient
from telegram_gateway.adapters.outbound.http.telegram_webhook_manager import (
    HttpTelegramWebhookManager,
)
from telegram_gateway.adapters.outbound.redis_conversation_store import (
    RedisConversationStore,
)
from telegram_gateway.adapters.outbound.redis_update_deduplicator import (
    RedisTelegramUpdateDeduplicator,
)
from telegram_gateway.adapters.outbound.unit_of_work import SqlAlchemyUnitOfWork
from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.application.ports.backend_client import BackendClient
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)
from telegram_gateway.application.ports.telegram_update_deduplicator import (
    TelegramUpdateDeduplicator,
)
from telegram_gateway.application.ports.telegram_webhook_manager import (
    TelegramWebhookManager,
)
from telegram_gateway.application.use_cases import (
    AttachTelegram,
    AuthenticateBusinessUser,
    CloseAgentSession,
    GetAgentSession,
    HandleTelegramWebhookMessage,
    SendAgentMessage,
    SendTelegramNotification,
)
from telegram_gateway.settings import Settings


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    uow_factory: Callable[[], SqlAlchemyUnitOfWork]
    redis: Redis
    backend_client: BackendClient
    agent_client: AgentClient
    telegram_message_sender: TelegramMessageSender
    conversation_store: ConversationStore
    telegram_update_deduplicator: TelegramUpdateDeduplicator
    telegram_webhook_manager: TelegramWebhookManager

    authenticate_business_user_use_case: AuthenticateBusinessUser
    attach_telegram_use_case: AttachTelegram
    send_agent_message_use_case: SendAgentMessage
    close_agent_session_use_case: CloseAgentSession
    send_telegram_notification_use_case: SendTelegramNotification
    get_agent_session_use_case: GetAgentSession
    handle_telegram_webhook_message_use_case: HandleTelegramWebhookMessage

    async def aclose(self) -> None:
        await self.redis.aclose()
        await self.engine.dispose()


async def create_container(settings: Settings) -> AppContainer:
    engine = create_engine(settings.database_url)
    await initialize_database(engine)
    session_factory = create_session_factory(engine)
    redis = Redis.from_url(settings.redis_url, decode_responses=False)

    backend_client: BackendClient = HttpBackendClient(
        get_user_url_template=settings.backend_get_user_url_template,
        create_user_url=settings.backend_create_user_url,
        timeout_seconds=settings.http_timeout_seconds,
    )
    agent_client: AgentClient = HttpAgentClient(
        handle_messages_url=settings.agent_handle_messages_url,
        close_session_url=settings.agent_close_session_url,
        internal_api_token=settings.internal_api_token,
        timeout_seconds=settings.agent_http_timeout_seconds,
    )
    telegram_message_sender: TelegramMessageSender = TelegramBotClient(
        bot_token=settings.telegram_bot_token,
        timeout_seconds=settings.http_timeout_seconds,
    )
    conversation_store: ConversationStore = RedisConversationStore(
        redis=redis,
        ttl_seconds=settings.session_ttl_seconds,
    )
    telegram_update_deduplicator: TelegramUpdateDeduplicator = (
        RedisTelegramUpdateDeduplicator(
            redis=redis,
            ttl_seconds=settings.telegram_update_deduplication_ttl_seconds,
        )
    )
    telegram_webhook_manager: TelegramWebhookManager = HttpTelegramWebhookManager(
        bot_token=settings.telegram_bot_token,
        timeout_seconds=settings.http_timeout_seconds,
    )

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        uow_factory=uow_factory,
        redis=redis,
        backend_client=backend_client,
        agent_client=agent_client,
        telegram_message_sender=telegram_message_sender,
        conversation_store=conversation_store,
        telegram_update_deduplicator=telegram_update_deduplicator,
        telegram_webhook_manager=telegram_webhook_manager,
        authenticate_business_user_use_case=AuthenticateBusinessUser(
            backend_client=backend_client,
        ),
        attach_telegram_use_case=AttachTelegram(),
        send_agent_message_use_case=SendAgentMessage(
            agent_client=agent_client,
            conversation_store=conversation_store,
        ),
        close_agent_session_use_case=CloseAgentSession(
            agent_client=agent_client,
            conversation_store=conversation_store,
        ),
        send_telegram_notification_use_case=SendTelegramNotification(
            conversation_store=conversation_store,
            telegram_message_sender=telegram_message_sender,
        ),
        get_agent_session_use_case=GetAgentSession(
            conversation_store=conversation_store,
        ),
        handle_telegram_webhook_message_use_case=HandleTelegramWebhookMessage(
            backend_client=backend_client,
            agent_client=agent_client,
            conversation_store=conversation_store,
            telegram_message_sender=telegram_message_sender,
            telegram_update_deduplicator=telegram_update_deduplicator,
        ),
    )
