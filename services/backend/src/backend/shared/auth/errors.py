from __future__ import annotations


class AuthenticationError(RuntimeError):
    pass


class AuthorizationError(RuntimeError):
    pass


class MissingAuthenticationError(AuthenticationError):
    pass


class InvalidTokenError(AuthenticationError):
    pass


class AccessDeniedError(AuthorizationError):
    pass