from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis

from direttore import Container

from backend.bootstrap.settings import get_settings
from backend.context.runtime.adapters.api_scheduler_adapter import (
    ApschedulerApiSchedulerAdapter,
)
from backend.context.runtime.adapters.day_generation_stream_adapter import (
    RedisDayGenerationStreamAdapter,
)
from backend.context.runtime.adapters.observation_stream_adapter import (
    RedisObservationStreamAdapter,
)
from backend.context.runtime.adapters.telegram_gateway_adapter import (
    HttpTelegramGatewayAdapter,
)
from backend.context.runtime.application.ports.day_generation_stream_port import (
    DayGenerationStreamPort,
)
from backend.context.runtime.application.ports.observation_stream_port import (
    ObservationStreamPort,
)
from backend.context.runtime.application.ports.telegram_gateway_port import (
    TelegramGatewayPort,
)
from backend.shared.application.ports.api_scheduler import ApiSchedulerPort
from backend.shared.auth import JwtTokenService
from backend.shared.security.password_hashing import PasswordHasher


from backend.context.runtime.adapters.agent_server_adapter import (
    HttpAgentServerAdapter,
)
from backend.context.runtime.application.ports.agent_server_port import (
    AgentServerPort,
)

AGENT_EXTRACTED_OBSERVATIONS_OFFSET_KEY = (
    "runtime:streams:planner.agent.observations.extracted:last_id"
)


def build_container() -> Container:
    settings = get_settings()

    jwt_token_service = JwtTokenService(
        secret=settings.jwt_secret,
        ttl_seconds=settings.jwt_ttl_seconds,
    )

    scheduler = AsyncIOScheduler(
        timezone="UTC",
    )

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=False,
    )

    api_scheduler_adapter = ApschedulerApiSchedulerAdapter(
        scheduler=scheduler,
    )

    telegram_gateway_adapter = HttpTelegramGatewayAdapter(
        send_message_url=settings.telegram_gateway_send_message_url,
        close_conversation_url=settings.telegram_gateway_close_conversation_url,
    )

    observation_stream_adapter = RedisObservationStreamAdapter(
        redis=redis,
        extracted_observations_stream_name=settings.agent_extracted_observations_stream,
        observation_batch_ready_stream_name=settings.agent_observation_batch_ready_stream,
        read_offset_key=AGENT_EXTRACTED_OBSERVATIONS_OFFSET_KEY,
    )

    day_generation_stream_adapter = RedisDayGenerationStreamAdapter(
        redis=redis,
        day_generation_requested_stream_name=settings.agent_day_generation_requested_stream,
    )

    agent_server_adapter = HttpAgentServerAdapter(
        morning_briefing_url=settings.agent_server_morning_briefing_url,
        internal_api_token=settings.internal_api_token,
    )

    return Container.from_mapping(
        {
            PasswordHasher: PasswordHasher(),
            JwtTokenService: jwt_token_service,
            ApiSchedulerPort: api_scheduler_adapter,
            TelegramGatewayPort: telegram_gateway_adapter,
            ObservationStreamPort: observation_stream_adapter,
            DayGenerationStreamPort: day_generation_stream_adapter,
            AgentServerPort: agent_server_adapter,
        }
    )