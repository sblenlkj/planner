from __future__ import annotations

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from backend.context.user.domain.user_runtime_profile import UserRuntimeStatus

class CreateUserRequest(BaseModel):
    password: str = Field(min_length=1)
    name: str = Field(min_length=1)
    utc_offset_minutes: int
    login: str


class CreateUserResponse(BaseModel):
    user_id: UUID


class CreateAdminRequest(BaseModel):
    login: str = Field(min_length=1)
    name: str = Field(min_length=1)
    password: str = Field(min_length=1)


class CreateAdminResponse(BaseModel):
    admin_id: UUID


class AuthenticateUserRequest(BaseModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)

class AuthenticateUserResponse(BaseModel):
    user_id: UUID
    access_token: str
    token_type: str = "bearer"
    role: str

class GetUserRuntimeStatusResponse(BaseModel):
    user_id: UUID
    status: UserRuntimeStatus


class UpdateUserRuntimeStatusRequest(BaseModel):
    status: UserRuntimeStatus


class UpdateUserRuntimeStatusResponse(BaseModel):
    user_id: UUID
    status: UserRuntimeStatus

class UpdateUserLastSessionAtRequest(BaseModel):
    last_session_at: datetime


class UpdateUserLastSessionAtResponse(BaseModel):
    user_id: UUID
    last_session_at: datetime

class GetUserResponse(BaseModel):
    user_id: UUID
    login: str | None
    name: str | None
    language: str | None
    utc_offset_minutes: int | None
    region: str | None
    runtime_status: UserRuntimeStatus | None