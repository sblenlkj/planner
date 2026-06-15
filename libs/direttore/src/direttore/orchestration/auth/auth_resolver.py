from __future__ import annotations

from typing import Protocol, TypeVar


AuthInputContraT = TypeVar("AuthInputContraT", contravariant=True)
AuthContraT = TypeVar("AuthContraT", covariant=True)


class AuthResolverPort(Protocol[AuthInputContraT, AuthContraT]):
    async def resolve_auth(
        self,
        auth_input: AuthInputContraT,
    ) -> AuthContraT:
        raise NotImplementedError