from __future__ import annotations


class LlmRuntimeError(Exception):
    """Base error for the LLM runtime module."""


class LlmCapacityTimeoutError(LlmRuntimeError):
    """Raised when no slot can be acquired within the configured wait timeout."""


class LlmSessionExpiredError(LlmRuntimeError):
    """Raised when an LLM session exceeds its configured duration."""


class LlmProviderError(LlmRuntimeError):
    """Raised when the provider adapter fails."""


class UnsupportedProviderFeatureError(LlmRuntimeError):
    """Raised when the caller asks for a provider feature that is unavailable."""
