from uuid import uuid4

import pytest

from backend.context.user.domain.user_preferences import UserPreferences


def test_create_user_preferences_normalizes_values() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="  EN  ",
        utc_offset_minutes=180,
        region=" de ",
    )

    assert preferences.language == "en"
    assert preferences.utc_offset_minutes == 180
    assert preferences.region == "DE"


def test_create_user_preferences_uses_default_language() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        utc_offset_minutes=180,
    )

    assert preferences.language == "en"


def test_create_user_preferences_region_is_optional() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        utc_offset_minutes=180,
    )

    assert preferences.region is None


def test_create_user_preferences_requires_valid_language() -> None:
    with pytest.raises(ValueError):
        UserPreferences.create(
            user_id=uuid4(),
            language="english",
            utc_offset_minutes=180,
        )


def test_create_user_preferences_requires_integer_utc_offset() -> None:
    with pytest.raises(ValueError):
        UserPreferences.create(
            user_id=uuid4(),
            language="en",
            utc_offset_minutes=180.5,  # type: ignore[arg-type]
        )


def test_create_user_preferences_rejects_too_small_utc_offset() -> None:
    with pytest.raises(ValueError):
        UserPreferences.create(
            user_id=uuid4(),
            language="en",
            utc_offset_minutes=-721,
        )


def test_create_user_preferences_rejects_too_large_utc_offset() -> None:
    with pytest.raises(ValueError):
        UserPreferences.create(
            user_id=uuid4(),
            language="en",
            utc_offset_minutes=841,
        )


def test_change_language() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        utc_offset_minutes=180,
    )

    preferences.change_language("RU")

    assert preferences.language == "ru"


def test_change_utc_offset_minutes() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        utc_offset_minutes=180,
    )

    preferences.change_utc_offset_minutes(-240)

    assert preferences.utc_offset_minutes == -240


def test_change_utc_offset_minutes_rejects_invalid_value() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        utc_offset_minutes=180,
    )

    with pytest.raises(ValueError):
        preferences.change_utc_offset_minutes(900)


def test_change_region_can_clear_region() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        utc_offset_minutes=180,
        region="DE",
    )

    preferences.change_region(None)

    assert preferences.region is None