from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, Protocol, TypeVar

from direttore.orchestration.base_types.message import ApplicationMessage
from direttore.orchestration.auth.access_tags import AccessTags
from direttore.orchestration.auth.exceptions import (
    AccessDeniedError,
    MissingAccessPolicyError,
    MissingAuthenticationError,
)


AuthT = TypeVar("AuthT")
AuthTContraT = TypeVar("AuthTContraT", contravariant=True)

class AccessInvocationKind(StrEnum):
    USER_REQUEST = "user_request"
    SYSTEM_INVOKE = "system_invoke"


@dataclass(frozen=True, slots=True)
class AccessCheckContext:
    invocation_kind: AccessInvocationKind = AccessInvocationKind.USER_REQUEST


class AccessCheckerPort(Protocol[AuthTContraT]):
    def check(
        self,
        *,
        allowed_access_tags: frozenset[str] | None,
        auth: AuthTContraT,
        message: ApplicationMessage | object,
        context: AccessCheckContext | None = None,
    ) -> None:
        raise NotImplementedError


class DefaultAccessChecker(Generic[AuthT]):
    def check(
        self,
        *,
        allowed_access_tags: frozenset[str] | None,
        auth: AuthT,
        message: ApplicationMessage | object,
        context: AccessCheckContext | None = None,
    ) -> None:
        if allowed_access_tags is None:
            raise MissingAccessPolicyError(
                "Handler access policy is not configured. "
                f"Message={type(message).__module__}.{type(message).__qualname__}."
            )

        if not allowed_access_tags:
            raise MissingAccessPolicyError(
                "Handler access policy is empty. "
                f"Message={type(message).__module__}.{type(message).__qualname__}."
            )

        if AccessTags.PUBLIC in allowed_access_tags:
            return

        if auth is None:
            raise MissingAuthenticationError(
                "Authentication is required to execute command. "
                f"Message={type(message).__module__}.{type(message).__qualname__}."
            )

        access_tags = getattr(auth, "access_tags", None)

        if access_tags is None:
            raise AccessDeniedError(
                "DefaultAccessChecker requires auth.access_tags. "
                f"Auth={type(auth).__module__}.{type(auth).__qualname__}."
            )

        effective_context = context or AccessCheckContext()
        auth_tags = set(access_tags)

        if effective_context.invocation_kind == AccessInvocationKind.SYSTEM_INVOKE:
            auth_tags.add(AccessTags.SYSTEM)

        effective_auth_tags = frozenset(auth_tags)

        if AccessTags.AUTHENTICATED in allowed_access_tags:
            return

        if effective_auth_tags.intersection(allowed_access_tags):
            return

        raise AccessDeniedError(
            "Access denied for command. "
            f"Message={type(message).__module__}.{type(message).__qualname__}. "
            f"Invocation={effective_context.invocation_kind.value!r}. "
            f"Allowed={sorted(allowed_access_tags)!r}. "
            f"Actual={sorted(effective_auth_tags)!r}."
        )