from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260_000
PASSWORD_SALT_BYTES = 16


@dataclass(frozen=True, kw_only=True)
class PasswordHasher:
    iterations: int = PASSWORD_HASH_ITERATIONS

    def hash_password(self, password: str) -> str:
        password = password.strip()

        if not password:
            raise ValueError("Password is required.")

        salt = os.urandom(PASSWORD_SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.iterations,
        )

        return (
            f"{PASSWORD_HASH_ALGORITHM}"
            f"${self.iterations}"
            f"${salt.hex()}"
            f"${digest.hex()}"
        )

    def verify_password(self, *, password: str, password_hash: str) -> bool:
        algorithm, iterations_raw, salt_hex, digest_hex = password_hash.split("$", 3)

        if algorithm != PASSWORD_HASH_ALGORITHM:
            raise ValueError(f"Unsupported password hash algorithm: {algorithm}")

        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(actual_digest, expected_digest)