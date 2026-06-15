from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "planner-backend"
    app_env: str = "local"
    debug: bool = False

    server_host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(default=8001, alias="SERVER_PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://planner:planner@localhost:5432/planner",
        alias="DATABASE_URL",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    agent_extracted_observations_stream: str = Field(
        default="planner.agent.observations.extracted",
        alias="AGENT_EXTRACTED_OBSERVATIONS_STREAM",
    )
    agent_observation_batch_ready_stream: str = Field(
        default="planner.agent.observations.batch_ready",
        alias="AGENT_OBSERVATION_BATCH_READY_STREAM",
    )
    agent_day_generation_requested_stream: str = Field(
        default="planner.agent.day_generation.requested",
        alias="AGENT_DAY_GENERATION_REQUESTED_STREAM",
    )

    jwt_secret: str = Field(
        default="local-dev-jwt-secret",
        alias="JWT_SECRET",
    )
    jwt_ttl_seconds: int = Field(
        default=86400,
        alias="JWT_TTL_SECONDS",
    )

    internal_api_token: str = Field(
        default="local-dev-internal-api-token",
        alias="INTERNAL_API_TOKEN",
    )

    telegram_gateway_scheme: str = Field(
        default="http",
        alias="TELEGRAM_GATEWAY_SCHEME",
    )
    telegram_gateway_host: str = Field(
        default="localhost",
        alias="TELEGRAM_GATEWAY_HOST",
    )
    telegram_gateway_port: int = Field(
        default=8000,
        alias="TELEGRAM_GATEWAY_PORT",
    )

    agent_server_scheme: str = Field(
        default="http",
        alias="AGENT_SERVER_SCHEME",
    )
    agent_server_host: str = Field(
        default="127.0.0.1",
        alias="AGENT_SERVER_HOST",
    )
    agent_server_port: int = Field(
        default=8002,
        alias="AGENT_SERVER_PORT",
    )

    @property
    def agent_server_base_url(self) -> str:
        return (
            f"{self.agent_server_scheme}://"
            f"{self.agent_server_host}:"
            f"{self.agent_server_port}"
        )

    @property
    def agent_server_morning_briefing_url(self) -> str:
        return f"{self.agent_server_base_url}/internal/workflows/morning-briefing/run"

    @property
    def telegram_gateway_base_url(self) -> str:
        return (
            f"{self.telegram_gateway_scheme}://"
            f"{self.telegram_gateway_host}:"
            f"{self.telegram_gateway_port}"
        )

    @property
    def telegram_gateway_send_message_url(self) -> str:
        return f"{self.telegram_gateway_base_url}/internal/messages/send"

    @property
    def telegram_gateway_close_conversation_url(self) -> str:
        return f"{self.telegram_gateway_base_url}/internal/conversations/close"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore