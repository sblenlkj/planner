from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from telegram_gateway.application.ports.backend_client import UserRuntimeStatus


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "telegram-gateway"
    app_env: str = "local"
    debug: bool = False

    server_host: str = Field(default="127.0.0.1", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(alias="TELEGRAM_WEBHOOK_SECRET")
    internal_api_token: str = Field(alias="INTERNAL_API_TOKEN")

    use_mock_clients: bool = Field(default=True, alias="USE_MOCK_CLIENTS")
    mock_agent_sleep_seconds: float = Field(
        default=10.0,
        alias="MOCK_AGENT_SLEEP_SECONDS",
    )
    mock_user_runtime_status: UserRuntimeStatus = Field(
        default=UserRuntimeStatus.NOT_READY,
        alias="MOCK_USER_RUNTIME_STATUS",
    )

    backend_scheme: str = Field(default="http", alias="BACKEND_SCHEME")
    backend_host: str = Field(default="localhost", alias="BACKEND_HOST")
    backend_port: int = Field(default=8001, alias="BACKEND_PORT")

    agent_scheme: str = Field(default="http", alias="AGENT_SCHEME")
    agent_host: str = Field(default="localhost", alias="AGENT_HOST")
    agent_port: int = Field(default=8002, alias="AGENT_PORT")

    conversation_ttl_seconds: int = Field(
        default=604800,
        alias="CONVERSATION_TTL_SECONDS",
    )
    binding_cache_ttl_seconds: int = Field(
        default=604800,
        alias="BINDING_CACHE_TTL_SECONDS",
    )
    user_runtime_status_cache_ttl_seconds: int = Field(
        default=300,
        alias="USER_RUNTIME_STATUS_CACHE_TTL_SECONDS",
    )
    telegram_update_deduplication_ttl_seconds: int = Field(
        default=86400,
        alias="TELEGRAM_UPDATE_DEDUPLICATION_TTL_SECONDS",
    )
    closed_session_stream_maxlen: int = Field(
        default=10000,
        alias="CLOSED_SESSION_STREAM_MAXLEN",
    )

    http_timeout_seconds: float = Field(default=10.0, alias="HTTP_TIMEOUT_SECONDS")
    agent_http_timeout_seconds: float = Field(
        default=30.0,
        alias="AGENT_HTTP_TIMEOUT_SECONDS",
    )

    @property
    def backend_base_url(self) -> str:
        return f"{self.backend_scheme}://{self.backend_host}:{self.backend_port}"

    @property
    def agent_base_url(self) -> str:
        return f"{self.agent_scheme}://{self.agent_host}:{self.agent_port}"

    @property
    def backend_create_business_user_url(self) -> str:
        return f"{self.backend_base_url}/users"

    @property
    def backend_get_user_runtime_status_url_template(self) -> str:
        return f"{self.backend_base_url}/users/{{user_id}}/runtime-status"

    @property
    def backend_update_user_runtime_status_url_template(self) -> str:
        return f"{self.backend_base_url}/users/{{user_id}}/runtime-status"

    @property
    def backend_update_user_last_session_at_url_template(self) -> str:
        return f"{self.backend_base_url}/users/{{user_id}}/last-session-at"

    @property
    def backend_generate_day_schedule_url(self) -> str:
        return f"{self.backend_base_url}/runtime/day-generation/request"

    @property
    def agent_handle_onboarding_messages_url(self) -> str:
        return f"{self.agent_base_url}/internal/conversations/onboarding/respond"

    @property
    def agent_handle_messages_url(self) -> str:
        return f"{self.agent_base_url}/internal/conversations/respond"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
