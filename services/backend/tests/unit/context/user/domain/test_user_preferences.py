from uuid import uuid4

import pytest

from backend.context.user.domain.user_preferences import UserPreferences


def test_create_user_preferences_normalizes_values() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="  EN  ",
        timezone="Europe/Berlin",
        region=" de ",
    )

    assert preferences.language == "en"
    assert preferences.timezone == "Europe/Berlin"
    assert preferences.region == "DE"


def test_create_user_preferences_requires_valid_language() -> None:
    with pytest.raises(ValueError):
        UserPreferences.create(
            user_id=uuid4(),
            language="english",
            timezone="Europe/Berlin",
        )


def test_create_user_preferences_requires_valid_timezone() -> None:
    with pytest.raises(ValueError):
        UserPreferences.create(
            user_id=uuid4(),
            language="en",
            timezone="Unknown/Timezone",
        )


def test_change_language() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        timezone="Europe/Berlin",
    )

    preferences.change_language("RU")

    assert preferences.language == "ru"


def test_change_region_can_clear_region() -> None:
    preferences = UserPreferences.create(
        user_id=uuid4(),
        language="en",
        timezone="Europe/Berlin",
        region="DE",
    )

    preferences.change_region(None)

    assert preferences.region is None
