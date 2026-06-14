# Telegram Gateway refactor snapshot

This archive contains the mature Telegram Gateway refactor draft:

- Postgres stores only `TelegramBinding`.
- Redis List stores open conversation messages.
- Redis Stream publishes closed session events.
- Redis KV caches binding and backend-owned user runtime status.
- Backend owns user runtime status and last session timestamp.
- Agent HTTP client handles only active conversation responses: onboarding and main agent.
- Close session no longer calls Agent Server directly; it publishes `ClosedSessionEvent`.
- Internal API endpoints are intentionally unauthenticated for the current dev stage.

## Main use cases

- `HandleTelegramMessage`
- `SendBusinessMessage`
- `CloseTelegramSession`
- `MarkUserReady`

## Run

```bash
uv sync
uv run telegram-gateway
```

Swagger:

```text
http://localhost:8000/docs
```
