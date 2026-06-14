from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

DEFAULT_USER_LANGUAGE = "en"
MIN_UTC_OFFSET_MINUTES = -12 * 60
MAX_UTC_OFFSET_MINUTES = 14 * 60


@dataclass(slots=True)
class UserPreferences:
    user_id: UUID
    language: str
    utc_offset_minutes: int
    region: str | None = None

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        utc_offset_minutes: int,
        language: str | None = None,
        region: str | None = None,
    ) -> "UserPreferences":
        return cls(
            user_id=user_id,
            language=language or DEFAULT_USER_LANGUAGE,
            utc_offset_minutes=utc_offset_minutes,
            region=region,
        )

    def __post_init__(self) -> None:
        self.language = self._normalize_language(self.language)
        self.region = self._normalize_region(self.region)
        self._validate_utc_offset_minutes(self.utc_offset_minutes)

    def change_language(self, language: str) -> None:
        self.language = self._normalize_language(language)

    def change_utc_offset_minutes(self, utc_offset_minutes: int) -> None:
        self._validate_utc_offset_minutes(utc_offset_minutes)
        self.utc_offset_minutes = utc_offset_minutes

    def change_region(self, region: str | None) -> None:
        self.region = self._normalize_region(region)

    @staticmethod
    def _normalize_language(language: str) -> str:
        language = language.strip().lower()

        if not language:
            raise ValueError("User language is required.")

        if not re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", language):
            raise ValueError(
                "User language must look like 'en', 'ru', 'it', 'he', or 'en-us'."
            )

        return language

    @staticmethod
    def _normalize_region(region: str | None) -> str | None:
        if region is None:
            return None

        region = region.strip().upper()
        return region or None

    @staticmethod
    def _validate_utc_offset_minutes(utc_offset_minutes: int) -> None:
        if not isinstance(utc_offset_minutes, int):
            raise ValueError("User UTC offset must be an integer number of minutes.")

        if (
            utc_offset_minutes < MIN_UTC_OFFSET_MINUTES
            or utc_offset_minutes > MAX_UTC_OFFSET_MINUTES
        ):
            raise ValueError(
                "User UTC offset must be between UTC-12:00 and UTC+14:00."
            )