from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmModelKind(StrEnum):
    STRONG = "strong"
    WEAK = "weak"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "agent-server"
    app_env: str = "local"
    debug: bool = False

    server_host: str = Field(default="127.0.0.1", alias="SERVER_HOST")
    server_port: int = Field(default=8002, alias="SERVER_PORT")

    internal_api_token: str = Field(alias="INTERNAL_API_TOKEN")

    llm_credentials_list: str = Field(alias="LLM_CREDENTIALS_LIST")
    llm_strong_model: str = Field(default="GigaChat-2-Pro", alias="LLM_STRONG_MODEL")
    llm_weak_model: str = Field(default="GigaChat-2", alias="LLM_WEAK_MODEL")
    llm_gigachat_scope: str = Field(
        default="GIGACHAT_API_PERS",
        alias="LLM_GIGACHAT_SCOPE",
    )
    llm_gigachat_verify_ssl_certs: bool = Field(
        default=False,
        alias="LLM_GIGACHAT_VERIFY_SSL_CERTS",
    )
    llm_acquire_timeout_seconds: float | None = Field(
        default=None,
        alias="LLM_ACQUIRE_TIMEOUT_SECONDS",
    )

    langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_base_url: str = Field(
        default="https://cloud.langfuse.com",
        alias="LANGFUSE_BASE_URL",
    )
    langfuse_project_name: str = Field(
        default="planner-agent",
        alias="LANGFUSE_PROJECT_NAME",
    )
    langfuse_environment: str = Field(default="local", alias="LANGFUSE_ENVIRONMENT")

    def get_llm_credentials(self) -> list[str]:
        credentials = [
            item.strip()
            for item in self.llm_credentials_list.split(",")
            if item.strip()
        ]

        if not credentials:
            raise RuntimeError("LLM_CREDENTIALS_LIST is empty.")

        return credentials


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]