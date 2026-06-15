from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="telegram-gateway", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    server_host: str = Field(default="localhost", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    session_ttl_seconds: int = Field(default=604800, alias="SESSION_TTL_SECONDS")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    internal_api_token: str = Field(alias="INTERNAL_API_TOKEN")

    backend_scheme: str = Field(default="http", alias="BACKEND_SCHEME")
    backend_host: str = Field(default="localhost", alias="BACKEND_HOST")
    backend_port: int = Field(default=8001, alias="BACKEND_PORT")

    agent_scheme: str = Field(default="http", alias="AGENT_SCHEME")
    agent_host: str = Field(default="localhost", alias="AGENT_HOST")
    agent_port: int = Field(default=8002, alias="AGENT_PORT")

    http_timeout_seconds: float = Field(default=30.0, alias="HTTP_TIMEOUT_SECONDS")
    agent_http_timeout_seconds: float = Field(default=60.0, alias="AGENT_HTTP_TIMEOUT_SECONDS")

    @property
    def backend_base_url(self) -> str:
        return f"{self.backend_scheme}://{self.backend_host}:{self.backend_port}"

    @property
    def agent_base_url(self) -> str:
        return f"{self.agent_scheme}://{self.agent_host}:{self.agent_port}"

    @property
    def backend_get_user_url_template(self) -> str:
        return f"{self.backend_base_url}/users/{{user_id}}"

    @property
    def agent_handle_messages_url(self) -> str:
        return f"{self.agent_base_url}/internal/conversations/respond"

    @property
    def agent_close_session_url(self) -> str:
        return f"{self.agent_base_url}/internal/workflows/session-close/run"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
