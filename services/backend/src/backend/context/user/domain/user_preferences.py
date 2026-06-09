from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(slots=True)
class UserPreferences:
    user_id: UUID
    language: str
    timezone: str
    region: str | None = None

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        language: str,
        timezone: str,
        region: str | None = None,
    ) -> "UserPreferences":
        return cls(
            user_id=user_id,
            language=language,
            timezone=timezone,
            region=region,
        )

    def __post_init__(self) -> None:
        self.language = self.language.strip().lower()
        self.timezone = self.timezone.strip()
        self.region = self.region.strip().upper() if self.region else None

        self._validate_language(self.language)
        self._validate_timezone(self.timezone)

    def change_language(self, language: str) -> None:
        language = language.strip().lower()

        self._validate_language(language)
        self.language = language

    def change_timezone(self, timezone: str) -> None:
        timezone = timezone.strip()

        self._validate_timezone(timezone)
        self.timezone = timezone

    def change_region(self, region: str | None) -> None:
        self.region = region.strip().upper() if region else None

    @staticmethod
    def _validate_language(language: str) -> None:
        if not language:
            raise ValueError("User language is required.")

        if not re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", language):
            raise ValueError(
                "User language must look like 'en', 'ru', 'it', 'he', or 'en-us'."
            )

    @staticmethod
    def _validate_timezone(timezone: str) -> None:
        if not timezone:
            raise ValueError("User timezone is required.")

        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown user timezone: {timezone}") from exc