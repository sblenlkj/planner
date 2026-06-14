from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.shared.application import ADMIN_ACCESS_TAG, USER_ACCESS_TAG
from backend.shared.auth.errors import InvalidTokenError

JWT_ALGORITHM = "HS256"
JWT_TOKEN_TYPE = "JWT"


@dataclass(frozen=True, slots=True)
class JwtTokenPayload:
    user_id: UUID
    role: str
    issued_at: int
    expires_at: int


@dataclass(frozen=True, slots=True)
class JwtTokenService:
    secret: str
    ttl_seconds: int = 60 * 60 * 24

    def create_access_token(
        self,
        *,
        user_id: UUID,
        role: str,
    ) -> str:
        if role not in {USER_ACCESS_TAG, ADMIN_ACCESS_TAG}:
            raise ValueError("JWT role must be 'user' or 'admin'.")

        issued_at = int(time.time())
        expires_at = issued_at + self.ttl_seconds

        header = {
            "alg": JWT_ALGORITHM,
            "typ": JWT_TOKEN_TYPE,
        }
        payload = {
            "sub": str(user_id),
            "role": role,
            "iat": issued_at,
            "exp": expires_at,
        }

        encoded_header = self._base64url_encode_json(header)
        encoded_payload = self._base64url_encode_json(payload)
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        signature = self._sign(signing_input)

        return f"{encoded_header}.{encoded_payload}.{signature}"

    def verify_access_token(self, token: str) -> JwtTokenPayload:
        parts = token.split(".")

        if len(parts) != 3:
            raise InvalidTokenError("JWT must contain header, payload and signature.")

        encoded_header, encoded_payload, encoded_signature = parts
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")

        expected_signature = self._sign(signing_input)

        if not hmac.compare_digest(expected_signature, encoded_signature):
            raise InvalidTokenError("JWT signature is invalid.")

        header = self._base64url_decode_json(encoded_header)
        payload = self._base64url_decode_json(encoded_payload)

        if header.get("alg") != JWT_ALGORITHM:
            raise InvalidTokenError("Unsupported JWT algorithm.")

        expires_at = int(payload["exp"])

        if expires_at < int(time.time()):
            raise InvalidTokenError("JWT is expired.")

        role = str(payload["role"])

        if role not in {USER_ACCESS_TAG, ADMIN_ACCESS_TAG}:
            raise InvalidTokenError("JWT role is invalid.")

        return JwtTokenPayload(
            user_id=UUID(str(payload["sub"])),
            role=role,
            issued_at=int(payload["iat"]),
            expires_at=expires_at,
        )

    def _sign(self, signing_input: bytes) -> str:
        digest = hmac.new(
            self.secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        return self._base64url_encode_bytes(digest)

    @staticmethod
    def _base64url_encode_json(value: dict[str, Any]) -> str:
        raw = json.dumps(
            value,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        return JwtTokenService._base64url_encode_bytes(raw)

    @staticmethod
    def _base64url_encode_bytes(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _base64url_decode_json(value: str) -> dict[str, Any]:
        padding = "=" * (-len(value) % 4)
        raw = base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
        decoded = json.loads(raw.decode("utf-8"))

        if not isinstance(decoded, dict):
            raise InvalidTokenError("JWT JSON section must be an object.")

        return decoded