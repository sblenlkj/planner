from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\b"
)

PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bignore\s+(all\s+)?(previous|prior)\s+(instructions|rules|prompts)\b", re.I),
    re.compile(r"\bforget\s+(your|the)\s+(system|developer)\s+(prompt|instructions|rules)\b", re.I),
    re.compile(r"\bdisregard\s+(all\s+)?(previous|prior)\s+(instructions|rules|prompts)\b", re.I),
    re.compile(r"\breveal\s+(your|the)\s+(system|developer)\s+(prompt|instructions)\b", re.I),
    re.compile(r"\bshow\s+me\s+(your|the)\s+(system|developer)\s+(prompt|instructions)\b", re.I),
    re.compile(r"\byou\s+must\s+only\s+do\s+what\s+i\s+say\b", re.I),
    re.compile(r"\bdo\s+only\s+as\s+i\s+say\b", re.I),
    re.compile(r"\bact\s+as\s+if\s+you\s+have\s+no\s+rules\b", re.I),

    re.compile(r"\bзабудь\s+(свой|все|всю|предыдущие|предыдущий).{0,40}(промпт|инструкц|правил)", re.I),
    re.compile(r"\bигнорируй\s+(все|предыдущие|прошлые).{0,40}(инструкц|правил|промпт)", re.I),
    re.compile(r"\bне\s+следуй\s+(своим|предыдущим).{0,40}(инструкц|правил)", re.I),
    re.compile(r"\bпокажи\s+(свой|системный|developer).{0,40}(промпт|инструкц)", re.I),
    re.compile(r"\bраскрой\s+(свой|системный|developer).{0,40}(промпт|инструкц)", re.I),
    re.compile(r"\bделай\s+только\s+как\s+я\s+скажу\b", re.I),
)


class InputGuardViolationCode(StrEnum):
    PROMPT_INJECTION = "prompt_injection"
    EXPLICIT_UUID = "explicit_uuid"


@dataclass(frozen=True, slots=True)
class InputGuardViolation:
    code: InputGuardViolationCode
    message: str


class InputGuardBlockedError(Exception):
    def __init__(
        self,
        *,
        violations: tuple[InputGuardViolation, ...],
    ) -> None:
        super().__init__("User message was blocked by input guard")
        self.violations = violations

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(violation.code.value for violation in self.violations)


@dataclass(frozen=True, slots=True)
class InputGuardResult:
    allowed: bool
    violations: tuple[InputGuardViolation, ...] = ()

    @classmethod
    def allow(cls) -> "InputGuardResult":
        return cls(allowed=True)

    @classmethod
    def block(cls, violations: Iterable[InputGuardViolation]) -> "InputGuardResult":
        return cls(allowed=False, violations=tuple(violations))


class UserInputGuard:
    def validate_text(self, text: str) -> InputGuardResult:
        violations: list[InputGuardViolation] = []

        if self._has_prompt_injection(text):
            violations.append(
                InputGuardViolation(
                    code=InputGuardViolationCode.PROMPT_INJECTION,
                    message="Message looks like an instruction override attempt.",
                )
            )

        if self._has_uuid(text):
            violations.append(
                InputGuardViolation(
                    code=InputGuardViolationCode.EXPLICIT_UUID,
                    message="Message contains a raw UUID-like identifier.",
                )
            )

        if violations:
            return InputGuardResult.block(violations)

        return InputGuardResult.allow()

    def ensure_safe_text(self, text: str) -> None:
        result = self.validate_text(text)

        if not result.allowed:
            raise InputGuardBlockedError(violations=result.violations)

    def _has_prompt_injection(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in PROMPT_INJECTION_PATTERNS)

    def _has_uuid(self, text: str) -> bool:
        return UUID_RE.search(text) is not None