from __future__ import annotations


class AuthenticationError(RuntimeError):
    pass


class AuthorizationError(RuntimeError):
    pass


class MissingAuthenticationError(AuthenticationError):
    pass


class AccessDeniedError(AuthorizationError):
    pass


class MissingAccessPolicyError(AuthorizationError):
    pass