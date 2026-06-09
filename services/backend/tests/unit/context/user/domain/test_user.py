from uuid import UUID

import pytest

from backend.context.user.domain.user import User, UserStatus


def test_create_user_normalizes_email_and_name() -> None:
    user = User.create(
        email="  PERSON@EXAMPLE.COM  ",
        name="  Alex  ",
    )

    assert isinstance(user.id, UUID)
    assert user.email == "person@example.com"
    assert user.name == "Alex"
    assert user.status == UserStatus.ACTIVE


def test_create_user_requires_email() -> None:
    with pytest.raises(ValueError):
        User.create(
            email="   ",
            name="Alex",
        )


def test_create_user_requires_name() -> None:
    with pytest.raises(ValueError):
        User.create(
            email="person@example.com",
            name="   ",
        )


def test_rename_user() -> None:
    user = User.create(
        email="person@example.com",
        name="Alex",
    )

    user.rename("  Max  ")

    assert user.name == "Max"


def test_disable_and_activate_user() -> None:
    user = User.create(
        email="person@example.com",
        name="Alex",
    )

    user.disable()
    assert user.status == UserStatus.DISABLED

    user.activate()
    assert user.status == UserStatus.ACTIVE
