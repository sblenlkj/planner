from __future__ import annotations

import hmac
from dataclasses import dataclass

from direttore.orchestration import AuthResolverPort

from backend.shared.application import ADMIN_ACCESS_TAG, USER_ACCESS_TAG
from backend.shared.auth.auth_context import BackendAuth
from backend.shared.auth.auth_input import BackendAuthInput
from backend.shared.auth.errors import MissingAuthenticationError
from backend.shared.auth.jwt_token_service import JwtTokenService


@dataclass(frozen=True, slots=True)
class BackendAuthResolver(AuthResolverPort[BackendAuthInput, BackendAuth]):
    jwt_token_service: JwtTokenService
    internal_api_token: str

    async def resolve_auth(
        self,
        auth_input: BackendAuthInput,
    ) -> BackendAuth:
        token = self._extract_bearer_token(auth_input.authorization_header)

        if hmac.compare_digest(token, self.internal_api_token):
            return BackendAuth.system(system_name="internal-api")

        payload = self.jwt_token_service.verify_access_token(token)

        if payload.role == ADMIN_ACCESS_TAG:
            return BackendAuth.admin(user_id=payload.user_id)

        if payload.role == USER_ACCESS_TAG:
            return BackendAuth.user(user_id=payload.user_id)

        raise MissingAuthenticationError("Unsupported auth role.")

    @staticmethod
    def _extract_bearer_token(authorization_header: str | None) -> str:
        if not authorization_header:
            raise MissingAuthenticationError("Authorization header is required.")

        scheme, _, token = authorization_header.partition(" ")

        if scheme.lower() != "bearer" or not token:
            raise MissingAuthenticationError("Authorization header must use Bearer token.")

        return token.strip()