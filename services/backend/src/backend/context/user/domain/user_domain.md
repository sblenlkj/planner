# User Domain

## Purpose

The `user` context owns the minimal business identity of a Planner user and the explicit user preferences that other contexts need to interpret user-facing behavior correctly.

This context is intentionally small. It does not own analytics, course progress, schedule items, graph memory, connector sync state, Telegram UX, or agent session state.

## Current Domain Model

```text
User
UserPreferences
UserStatus
```

## Entities

### User

`User` is the core user identity record.

Fields:

```text
id
email
name
status
```

Meaning:

- `id` is the domain UUID identifier. It is not an auto-increment database id.
- `email` is normalized by trimming spaces and lowercasing.
- `name` is the user's display name / first-name-like label.
- `status` describes whether the user is active or disabled.

Supported behavior:

```text
create
rename
change_email
disable
activate
```

Validation rules:

```text
email is required
email must contain "@"
name is required
```

### UserPreferences

`UserPreferences` stores explicit user settings used by other contexts and agents.

Fields:

```text
user_id
language
timezone
region
```

Meaning:

- `user_id` references `User.id`.
- `language` controls the preferred language for agent/user-facing responses.
- `timezone` is used for schedule/reminder interpretation.
- `region` is optional and can be used later for localization.

Supported behavior:

```text
create
change_language
change_timezone
change_region
```

Validation and normalization rules:

```text
language is trimmed and lowercased
language must look like "en", "ru", "it", "he", or "en-us"
timezone is trimmed and validated through zoneinfo
region is optional and uppercased when present
```

## Value Objects / Enums

### UserStatus

```text
active
disabled
```

At this stage `UserStatus` is a simple enum, not a state machine. Direct transitions are enough for the current model.

## Design Rules Applied

The user context follows the shared backend domain rules:

```text
id fields are UUID domain identifiers
no auto-increment ids
no created_at / updated_at by default
domain validation protects the model, not only API input
```

For text fields, the context uses the current simple user naming:

```text
name
email
language
timezone
region
```

The broader `title` / `description` naming rule is intended for entities that represent agent-facing domain content, such as courses, tasks, observations, and links. It does not replace identity-specific fields like `name` or `email`.

## Current File Layout

```text
src/backend/context/user/
  __init__.py

  domain/
    __init__.py
    user.py
    user_preferences.py
```

## Current Boundaries

The `user` context owns:

```text
business user id
email
name
status
language preference
timezone preference
optional region preference
```

The `user` context does not own:

```text
behavioral analytics
course progress
schedule items
knowledge graph memory
connector discovered items
Telegram chat state
agent session state
```

## Future Extensions

Possible future additions:

```text
UserGoogleAccount
UserExternalIdentity
UserAuthorizationGrant
UserAuthorizationSecretRef
```

These are intentionally not part of the first minimal domain slice. For now, the user context only contains `User` and `UserPreferences`.
