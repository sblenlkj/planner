from __future__ import annotations

from direttore import CommandHandlerConfig, QueryHandlerConfig

USER_ACCESS_TAG = "user"
ADMIN_ACCESS_TAG = "admin"
SYSTEM_ACCESS_TAG = "system"

ADMIN_SYSTEM_ACCESS_TAGS = frozenset(
    {
        ADMIN_ACCESS_TAG,
        SYSTEM_ACCESS_TAG,
    }
)

PROTECTED_COMMAND_HANDLER_CONFIG = CommandHandlerConfig(
    allowed_access_tags=ADMIN_SYSTEM_ACCESS_TAGS,
)

PROTECTED_QUERY_HANDLER_CONFIG = QueryHandlerConfig(
    allowed_access_tags=ADMIN_SYSTEM_ACCESS_TAGS,
)