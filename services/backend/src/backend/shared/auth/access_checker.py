from __future__ import annotations

from direttore.orchestration import (
    AccessCheckerPort,
    AccessCheckContext,
    AccessInvocationKind,
)

from backend.shared.application import SYSTEM_ACCESS_TAG
from backend.shared.auth.auth_context import BackendAuth
from backend.shared.auth.errors import AccessDeniedError, MissingAuthenticationError


class BackendAccessChecker(AccessCheckerPort[BackendAuth | None]):
    def check(
        self,
        *,
        allowed_access_tags: frozenset[str] | None,
        auth: BackendAuth | None,
        message: object,
        context: AccessCheckContext | None = None,
    ) -> None:
        if allowed_access_tags is None or not allowed_access_tags:
            return

        if auth is None:
            raise MissingAuthenticationError(
                "Authentication is required. "
                f"Message={type(message).__module__}.{type(message).__qualname__}."
            )

        actual_tags = set(auth.access_tags)
        effective_context = context or AccessCheckContext()

        if effective_context.invocation_kind == AccessInvocationKind.SYSTEM_INVOKE:
            actual_tags.add(SYSTEM_ACCESS_TAG)

        if actual_tags.intersection(allowed_access_tags):
            return

        raise AccessDeniedError(
            "Access denied. "
            f"Message={type(message).__module__}.{type(message).__qualname__}. "
            f"Allowed={sorted(allowed_access_tags)!r}. "
            f"Actual={sorted(actual_tags)!r}."
        )