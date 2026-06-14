# Backend Auth Notes

## Purpose

This file documents the current backend authorization/authentication design around Direttore runtime, JWT tokens, and internal service calls.

The implementation is intentionally minimal and experimental. If runtime auth integration becomes unstable, it is acceptable to temporarily disable the auth resolver/access checker and continue development without authorization.

## Main Idea

Backend inbound calls may come from two different sources:

```text
1. External user/admin request
   Authorization: Bearer <jwt_access_token>

2. Internal service request
   Authorization: Bearer <internal_api_token>
```

JWT tokens identify real backend users or admins.

Internal API token identifies trusted backend-to-backend system calls, for example calls from Telegram Gateway or Agent Server.

## User Roles vs Access Tags

Domain `User.role` supports only:

```text
user
admin
```

`system` is not a user role. It is a technical access actor used for trusted internal calls.

Shared access tag constants live in shared application configuration:

```text
USER_ACCESS_TAG = "user"
ADMIN_ACCESS_TAG = "admin"
SYSTEM_ACCESS_TAG = "system"
```

`UserRole.USER` and `UserRole.ADMIN` reuse these shared tag values.

## Suggested File Layout

```text
src/backend/shared/auth/
  __init__.py
  auth_input.py
  auth_context.py
  errors.py
  jwt_token_service.py
  backend_auth_resolver.py
  access_checker.py
```

## Auth Input

`BackendAuthInput` is the inbound auth payload passed to the Direttore runtime/auth resolver.

Current shape:

```text
BackendAuthInput
  authorization_header: str | None
```

The FastAPI adapter should create this object from the HTTP `Authorization` header.

## Auth Context

`BackendAuth` is the resolved auth object used by the backend runtime and access checker.

It can represent:

```text
BackendAuth.user(user_id)
BackendAuth.admin(user_id)
BackendAuth.system(system_name="internal-api")
```

Expected access tags:

```text
user  -> {"user"}
admin -> {"admin"}
system -> {"system"}
```

## JWT Token Service

`JwtTokenService` creates and verifies backend access tokens.

Minimal JWT payload:

```json
{
  "sub": "<user_id>",
  "role": "user|admin",
  "iat": 123,
  "exp": 456
}
```

Token creation belongs to user-facing authentication logic, because user context owns password hash, role, and status.

Token verification belongs to shared auth, because every inbound adapter/runtime call may need to resolve JWT into backend auth context.

Current implementation can use stdlib HMAC SHA-256 JWT-like tokens for MVP. Later it can be replaced with a standard JWT library if needed.

## Backend Auth Resolver

`BackendAuthResolver` resolves `BackendAuthInput` into `BackendAuth`.

Resolution order:

```text
1. Extract Bearer token from Authorization header.
2. If token matches internal_api_token:
     return BackendAuth.system(system_name="internal-api")
3. Otherwise verify token as JWT.
4. If JWT role == "admin":
     return BackendAuth.admin(user_id)
5. If JWT role == "user":
     return BackendAuth.user(user_id)
6. Otherwise fail authentication.
```

This allows both external JWT requests and trusted service-to-service calls to use the same Direttore execution pipeline.

## Access Checker

`BackendAccessChecker` checks handler-level access restrictions.

Rule:

```text
If handler config has no allowed_access_tags, allow the call.
If allowed_access_tags exists, resolved auth must have at least one matching tag.
```

Examples:

```text
allowed_access_tags={"admin", "system"}
  allows admin JWT and internal API token
  denies regular user JWT

allowed_access_tags={"user"}
  allows regular user JWT
  denies admin unless admin is explicitly included
```

Public handlers should normally omit config entirely.

Protected handlers should explicitly use shared protected configs or custom handler configs with `allowed_access_tags`.

## FastAPI Integration

FastAPI should not manually call repositories for auth-sensitive application behavior.

Expected flow:

```text
HTTP request
  -> FastAPI router/dependency extracts Authorization header
  -> BackendAuthInput
  -> Direttore runtime invokes command with auth input
  -> BackendAuthResolver resolves user/admin/system
  -> BackendAccessChecker validates allowed tags
  -> Command handler executes
```

If auth integration becomes unstable, temporarily bypass resolver/access checker and invoke commands without auth. This is acceptable during early development.

## User Context Auth Responsibilities

The `user` context owns:

```text
User.id
User.role
User.status
User.password_hash
password verification
JWT issuing after successful authentication
```

Recommended use case:

```text
AuthenticateUserCommand
  user_id
  password

AuthenticateUserCommandResult
  user_id
  role
  access_token
  token_type = "bearer"
```

Authentication should verify password using `PasswordHasher` and then create a JWT access token using `JwtTokenService`.

## Telegram Gateway / Internal Service Calls

Telegram Gateway should call backend with:

```text
Authorization: Bearer <internal_api_token>
```

For user creation, Telegram Gateway can call backend `CreateUser` and store the returned backend business `user_id` in its own mapping.

The Telegram Gateway does not need a user JWT for internal backend calls. It uses the internal API token and resolves as `system`.

## Temporary Development Policy

Current auth layer is experimental.

If it blocks progress:

```text
1. Disable runtime auth resolver/access checker temporarily.
2. Keep command handlers and user/password/JWT code in place.
3. Continue implementing user/course/schedule application flows.
4. Return to auth integration after the main backend wiring is stable.
```

Do not mix temporary auth bypasses into domain entities. Auth bypass should stay in runtime/inbound wiring only.
