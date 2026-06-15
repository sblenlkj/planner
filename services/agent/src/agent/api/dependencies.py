from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from agent.core.settings import get_settings


@dataclass(frozen=True, slots=True)
class InternalRequestContext:
    business_user_id: UUID


async def require_internal_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    settings = get_settings()
    expected = f"Bearer {settings.internal_api_token}"

    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API token",
        )


async def get_internal_context(
    _: None = Depends(require_internal_token),
    x_business_user_id: str | None = Header(default=None, alias="X-Business-User-Id"),
) -> InternalRequestContext:
    if not x_business_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Business-User-Id header is required",
        )

    try:
        business_user_id = UUID(x_business_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Business-User-Id must be UUID",
        ) from exc

    return InternalRequestContext(business_user_id=business_user_id)