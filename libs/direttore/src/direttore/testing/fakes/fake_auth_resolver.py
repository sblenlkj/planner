from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from direttore.orchestration.auth import AuthResolverPort


AuthInputT = TypeVar("AuthInputT")
AuthT = TypeVar("AuthT")


@dataclass(slots=True)
class FakeAuthResolver(Generic[AuthInputT, AuthT], AuthResolverPort[AuthInputT, AuthT]):
    auth: AuthT

    async def resolve_auth(
        self,
        auth_input: AuthInputT,
    ) -> AuthT:
        return self.auth