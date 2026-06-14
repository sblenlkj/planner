from __future__ import annotations

from typing import Annotated

from direttore import ModularDirettoreWithSimpleSession
from fastapi import APIRouter, Depends
from uuid import UUID

from backend.context.user.adapters.inbound.schemas import (
    AuthenticateUserRequest,
    AuthenticateUserResponse,
    CreateAdminRequest,
    CreateAdminResponse,
    CreateUserRequest,
    CreateUserResponse,
    GetUserRuntimeStatusResponse,
    UpdateUserRuntimeStatusRequest,
    UpdateUserRuntimeStatusResponse,
    UpdateUserLastSessionAtRequest,
    UpdateUserLastSessionAtResponse,
)
from backend.context.user.application.use_cases import (
    AuthenticateUserCommand,
    AuthenticateUserCommandResult,
    CreateAdminCommand,
    CreateAdminCommandResult,
    CreateUserCommand,
    CreateUserCommandResult,
    GetUserRuntimeStatusCommand,
    GetUserRuntimeStatusCommandResult,
    UpdateUserRuntimeStatusCommand,
    UpdateUserRuntimeStatusCommandResult,
    UpdateUserLastSessionAtCommand,
    UpdateUserLastSessionAtCommandResult,
)
from backend.bootstrap.direttore import get_direttore


router = APIRouter(
    prefix="/users",
    tags=["user"],
)

DirettoreDep = Annotated[
    ModularDirettoreWithSimpleSession,
    Depends(get_direttore),
]


@router.post(
    "",
    response_model=CreateUserResponse,
)
async def create_user(
    request: CreateUserRequest,
    direttore: DirettoreDep,
) -> CreateUserResponse:
    result = await direttore.handle(
        CreateUserCommand(
            password=request.password,
            login=request.login,
        )
    )

    if not isinstance(result, CreateUserCommandResult):
        raise TypeError(
            "CreateUserCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateUserResponse(user_id=result.user_id)


@router.post(
    "/admin",
    response_model=CreateAdminResponse,
)
async def create_admin(
    request: CreateAdminRequest,
    direttore: DirettoreDep,
) -> CreateAdminResponse:
    result = await direttore.handle(
        CreateAdminCommand(
            login=request.login,
            name=request.name,
            password=request.password,
        )
    )

    if not isinstance(result, CreateAdminCommandResult):
        raise TypeError(
            "CreateAdminCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateAdminResponse(admin_id=result.admin_id)


@router.post(
    "/auth",
    response_model=AuthenticateUserResponse,
)
async def authenticate_user(
    request: AuthenticateUserRequest,
    direttore: DirettoreDep,
) -> AuthenticateUserResponse:
    result = await direttore.handle(
        AuthenticateUserCommand(
            login=request.login,
            password=request.password,
        )
    )

    if not isinstance(result, AuthenticateUserCommandResult):
        raise TypeError(
            "AuthenticateUserCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return AuthenticateUserResponse(
        user_id=result.user_id, # type: ignore
        access_token=result.access_token,
        token_type="bearer",
        role=result.role,
    )


@router.get(
    "/{user_id}/runtime-status",
    response_model=GetUserRuntimeStatusResponse,
)
async def get_user_runtime_status(
    user_id: UUID,
    direttore: DirettoreDep,
) -> GetUserRuntimeStatusResponse:
    result = await direttore.handle(
        GetUserRuntimeStatusCommand(
            user_id=user_id,
        )
    )

    if not isinstance(result, GetUserRuntimeStatusCommandResult):
        raise TypeError(
            "GetUserRuntimeStatusCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return GetUserRuntimeStatusResponse(
        user_id=result.user_id,
        status=result.status,
    )


@router.patch(
    "/{user_id}/runtime-status",
    response_model=UpdateUserRuntimeStatusResponse,
)
async def update_user_runtime_status(
    user_id: UUID,
    request: UpdateUserRuntimeStatusRequest,
    direttore: DirettoreDep,
) -> UpdateUserRuntimeStatusResponse:
    result = await direttore.handle(
        UpdateUserRuntimeStatusCommand(
            user_id=user_id,
            status=request.status,
        )
    )

    if not isinstance(result, UpdateUserRuntimeStatusCommandResult):
        raise TypeError(
            "UpdateUserRuntimeStatusCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return UpdateUserRuntimeStatusResponse(
        user_id=result.user_id,
        status=result.status,
    )

@router.patch(
    "/{user_id}/last-session-at",
    response_model=UpdateUserLastSessionAtResponse,
)
async def update_user_last_session_at(
    user_id: UUID,
    request: UpdateUserLastSessionAtRequest,
    direttore: DirettoreDep,
) -> UpdateUserLastSessionAtResponse:
    result = await direttore.handle(
        UpdateUserLastSessionAtCommand(
            user_id=user_id,
            last_session_at=request.last_session_at,
        )
    )

    if not isinstance(result, UpdateUserLastSessionAtCommandResult):
        raise TypeError(
            "UpdateUserLastSessionAtCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return UpdateUserLastSessionAtResponse(
        user_id=result.user_id,
        last_session_at=result.last_session_at,
    )