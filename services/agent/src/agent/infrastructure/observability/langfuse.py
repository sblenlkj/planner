from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from agent.core.settings import Settings, get_settings

from langfuse.langchain import CallbackHandler

def configure_langfuse_env(settings: Settings | None = None) -> None:
    settings = settings or get_settings()

    if not settings.langfuse_enabled:
        return

    if settings.langfuse_public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key

    if settings.langfuse_secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key

    os.environ["LANGFUSE_BASE_URL"] = settings.langfuse_base_url


def build_langfuse_callback() -> Any | None:
    settings = get_settings()

    if not settings.langfuse_enabled:
        return None

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    return CallbackHandler()


def build_langfuse_config(
    *,
    callback: Any | None,
    business_user_id: UUID,
    session_id: str,
    agent_name: str,
    model_kind: str,
    model: str,
    slot_id: str,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()

    metadata = {
        "langfuse_session_id": session_id,
        "langfuse_user_id": str(business_user_id),
        "langfuse_tags": [
            settings.langfuse_project_name,
            settings.langfuse_environment,
            agent_name,
            model_kind,
        ],
        "agent_name": agent_name,
        "service": settings.app_name,
        "project": settings.langfuse_project_name,
        "environment": settings.langfuse_environment,
        "slot_id": slot_id,
        "model": model,
        "model_kind": model_kind,
        **(extra_metadata or {}),
    }

    config: dict[str, Any] = {
        "metadata": metadata,
    }

    if callback is not None:
        config["callbacks"] = [callback]

    return config