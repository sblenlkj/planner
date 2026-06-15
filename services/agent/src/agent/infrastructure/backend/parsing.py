from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID
from collections.abc import Mapping

def as_uuid(value: Any, *, field: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    raise TypeError(f"Expected UUID-compatible value for {field}, got {type(value).__name__}.")


def as_optional_uuid(value: Any, *, field: str) -> UUID | None:
    if value is None:
        return None
    return as_uuid(value, field=field)


def as_date(value: Any, *, field: str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f"Expected ISO date for {field}, got {type(value).__name__}.")


def as_optional_date(value: Any, *, field: str) -> date | None:
    if value is None:
        return None
    return as_date(value, field=field)


def as_datetime(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError(f"Expected ISO datetime for {field}, got {type(value).__name__}.")


def as_optional_datetime(value: Any, *, field: str) -> datetime | None:
    if value is None:
        return None
    return as_datetime(value, field=field)


def as_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def as_float(value: Any, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def as_tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple | set):
        return tuple(str(item) for item in value)
    raise TypeError(f"Expected tags-like collection, got {type(value).__name__}.")


def as_tuple_of_uuids(value: Any, *, field: str) -> tuple[UUID, ...]:
    if value is None:
        return ()
    if isinstance(value, list | tuple | set):
        return tuple(as_uuid(item, field=field) for item in value)
    raise TypeError(f"Expected UUID list for {field}, got {type(value).__name__}.")


def require_mapping(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object, got {type(payload).__name__}.")
    return payload


def require_list(payload: Any) -> list[Any]:
    if not isinstance(payload, list):
        raise TypeError(f"Expected JSON array, got {type(payload).__name__}.")
    return payload


def unwrap_items(payload: Any, *keys: str) -> list[Any]:
    """Accept either a raw list or an object containing list under common keys."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for key in ("items", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise TypeError(f"Expected JSON array or object with list payload, got {type(payload).__name__}.")


def extract_created_id(payload: Any, *keys: str) -> UUID:
    if not isinstance(payload, Mapping):
        raise TypeError(f"Expected create response mapping, got: {payload!r}")

    for key in keys:
        value = payload.get(key)
        if value is not None:
            return UUID(str(value))

    raise TypeError(f"Cannot extract created id from payload: {payload!r}")