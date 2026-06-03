# Telegram Gateway Overview

## Purpose

This document describes the initial high-level architecture of the Planner Telegram Gateway.

The Telegram Gateway is a small FastAPI service responsible for Telegram transport, Telegram user identity resolution, short-term conversation caching, and outgoing Telegram message delivery.

It should stay simple.

It is not a backend domain service, not an agent runtime, and not a long-term memory service.

---

## Core Formula

```text
Telegram Gateway owns Telegram transport + conversation cache.
Backend owns canonical user identity and domain state.
Agent Server owns reasoning.
```

The Telegram Gateway knows about:

```text
telegram_user_id
telegram_chat_id
telegram_message_id
telegram_update_id
business_user_id
session_id
message history
agent run request/response
outgoing Telegram delivery
```

The Telegram Gateway should not know about Planner domain concepts such as:

```text
plan
schedule
graph
analytics
connectors
knowledge cards
user profile signals
```

Those belong to Backend or Agent Server.

---

## Main Responsibilities

The Telegram Gateway has four main responsibilities:

```text
1. Telegram update intake
2. User identity resolution
3. Conversation/session cache
4. Outgoing Telegram delivery endpoint
```

---

## Responsibility 1: Telegram Update Intake

The service receives Telegram updates.

Usually this should happen through FastAPI webhook route:

```text
Telegram -> Telegram Gateway
POST /telegram/webhook
```

The gateway extracts:

```text
telegram_update_id
telegram_user_id
telegram_chat_id
telegram_message_id
message text
timestamp
```

Then it passes a normalized request to the application layer.

The webhook route should not contain all processing logic. It should parse the incoming payload and call an application service.

---

## Responsibility 2: User Identity Resolution

The gateway resolves Telegram identity into Planner business identity.

Canonical mapping:

```text
telegram_user_id -> business_user_id
```

The Backend `user` context remains the canonical source of truth.

The Telegram Gateway only caches this mapping in Redis to avoid calling Backend on every message.

### Resolution flow

```text
1. Telegram Gateway receives Telegram message.
2. Extract telegram_user_id and telegram_chat_id.
3. Check Redis cache: telegram_user_id -> business_user_id.
4. If mapping exists, use it.
5. If mapping does not exist, ask Backend.
6. If Backend knows the user, cache the mapping.
7. If Backend does not know the user, ask Backend to create the user.
8. Cache telegram_user_id -> business_user_id.
9. Cache business_user_id -> telegram_chat_id.
10. Continue processing the message.
```

### Important rule

The Telegram Gateway should not create canonical users by itself.

It should call Backend:

```text
get_or_create_user_by_telegram_identity
```

or equivalent future API.

---

## Responsibility 3: Conversation Cache

The Telegram Gateway stores the short-term conversation transcript in Redis.

This allows the Agent Server to stay stateless per turn.

For every new user message:

```text
Telegram Gateway:
  1. append user message to Redis session history
  2. load current session history
  3. call Agent Server with business_user_id + session_id + messages
  4. receive assistant response
  5. append assistant message to Redis session history
  6. send assistant message to Telegram
```

This means the Agent Server does not need to own persistent chat memory. It receives the relevant message history from the gateway on every turn.

---

## Responsibility 4: Outgoing Delivery Endpoint

The Telegram Gateway exposes an internal FastAPI endpoint for sending Telegram messages to a Planner user.

Example:

```text
Backend -> Telegram Gateway
POST /internal/messages/send
```

The request should use the Planner business user id, not Telegram ids.

Example payload:

```json
{
  "business_user_id": "uuid",
  "text": "Напоминание: пора читать книгу",
  "metadata": {
    "source": "schedule",
    "reminder_id": "..."
  },
  "store_in_session": true
}
```

The gateway resolves:

```text
business_user_id -> telegram_chat_id
```

Then sends the message through Telegram Bot API.

This endpoint is needed for:

```text
reminders
notifications
scheduled events
backend-triggered messages
```

---

## What Telegram Gateway Stores

At the first stage, Redis is enough.

Telegram Gateway stores operational transport/session state, not durable business state.

---

## Redis: Telegram User Mapping

Telegram user id to business user id:

```text
tg:user:{telegram_user_id}:business_user_id -> {business_user_id}
```

Example:

```text
tg:user:123456789:business_user_id = "b7c3..."
```

---

## Redis: Business User to Telegram Chat Mapping

Business user id to Telegram chat id:

```text
tg:business_user:{business_user_id}:chat_id -> {telegram_chat_id}
```

This mapping is required for backend-triggered outgoing messages.

Example:

```text
tg:business_user:b7c3...:chat_id = "123456789"
```

---

## Redis: Session Identity

At the beginning, session id can be deterministic:

```text
session_id = "telegram:{telegram_chat_id}"
```

This is simple and sufficient for one active Telegram conversation per chat.

Possible key:

```text
tg:session:{business_user_id}:active_session_id -> {session_id}
```

But this may be unnecessary at first if the deterministic session id is enough.

Recommended initial approach:

```text
session_id = telegram:{telegram_chat_id}
```

---

## Redis: Message History

Message history key:

```text
tg:session:{session_id}:messages
```

Recommended value structure: Redis list of JSON messages.

User message example:

```json
{
  "role": "user",
  "content": "Привет",
  "telegram_message_id": 123,
  "created_at": "2026-06-03T10:00:00Z"
}
```

Assistant message example:

```json
{
  "role": "assistant",
  "content": "Привет, давай начинать",
  "agent_run_id": "...",
  "created_at": "2026-06-03T10:00:01Z"
}
```

Backend notification example:

```json
{
  "role": "assistant",
  "content": "Напоминание: пора читать книгу",
  "source": "backend_notification",
  "metadata": {
    "reminder_id": "..."
  },
  "created_at": "2026-06-03T10:00:01Z"
}
```

---

## Redis: Idempotency

Telegram can resend updates.

The gateway should eventually store processed update ids:

```text
tg:update:{telegram_update_id}:processed -> 1
```

with TTL.

This prevents duplicate processing of the same Telegram update.

Idempotency is not the most urgent first feature, but it is important and should be part of the intended design.

---

## Operational Memory vs Domain Memory

The Telegram Gateway stores a conversation transcript/cache.

It does not store long-term semantic memory.

Important distinction:

```text
Telegram Gateway:
  short-term operational conversation transcript

Backend graph context:
  long-term semantic memory and knowledge cards

Backend analytics context:
  behavioral signals and personalization profile

Agent Server:
  stateless reasoning runtime per turn
```

The Telegram Gateway message history is not the same thing as graph memory or analytics profile.

---

## Agent Server Interaction

The Telegram Gateway should send structured requests to the Agent Server.

Example request:

```json
{
  "business_user_id": "uuid",
  "session_id": "telegram:123456789",
  "channel": "telegram",
  "message": {
    "role": "user",
    "content": "Привет",
    "external_message_id": "123",
    "created_at": "2026-06-03T10:00:00Z"
  },
  "history": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ],
  "metadata": {
    "telegram_user_id": "123456789",
    "telegram_chat_id": "123456789",
    "correlation_id": "..."
  }
}
```

Expected Agent Server response:

```json
{
  "assistant_message": {
    "role": "assistant",
    "content": "..."
  },
  "agent_run_id": "...",
  "metadata": {
    "correlation_id": "..."
  }
}
```

After receiving the response, Telegram Gateway should:

```text
1. append assistant message to Redis history
2. send assistant message to Telegram
```

---

## Should Gateway Store Agent Tool Calls?

No.

Telegram Gateway should not store:

```text
agent tool calls
LLM traces
gRPC calls
internal reasoning
LangSmith traces
Backend use-case traces
```

It may store:

```text
agent_run_id
correlation_id
assistant message text
```

Detailed agent execution belongs to Agent Server tracing/logging.

---

## Long Conversation Policy

The gateway should not send unlimited history forever.

Initial policy can be simple:

```text
keep last 50 messages
```

or:

```text
keep messages for last 24 hours
```

For MVP, recommended policy:

```text
keep last 50 messages per Telegram session
```

Later, if conversation becomes too long, summarization can be added. That summarization should probably be done by Agent Server or Backend, not by Telegram Gateway itself.

---

## Backend-Triggered Messages and Session History

When Backend sends a notification through Telegram Gateway, we need to decide whether it becomes part of conversation history.

Recommended default:

```text
store_in_session = true
```

Reason:

```text
The next agent turn should know that the user already received this reminder/notification.
```

But the internal send endpoint should allow explicit control:

```json
{
  "business_user_id": "uuid",
  "text": "...",
  "store_in_session": true
}
```

If `store_in_session` is false, the message is delivered to Telegram but not appended to conversation history.

---

## Proposed Service Structure

Telegram Gateway is a simple FastAPI service. It does not use Direttore.

Recommended structure:

```text
services/telegram-gateway/
  src/
    telegram_gateway/
      __init__.py
      main.py
      settings.py

      entrypoints/
        __init__.py
        fastapi.py
        telegram_webhook.py
        internal_api.py

      application/
        __init__.py
        handle_update.py
        send_message.py

      clients/
        __init__.py
        backend_client.py
        agent_client.py
        telegram_client.py

      storage/
        __init__.py
        redis_user_mapping.py
        redis_session_store.py
        redis_idempotency.py

      schemas/
        __init__.py
        telegram.py
        agent.py
        internal.py
```

No domain layer is needed at this stage.

No bounded contexts are needed inside Telegram Gateway.

---

## Directory Responsibilities

### `main.py`

Main Python module.

Responsible for starting the application or exposing app import target.

---

### `settings.py`

Configuration:

```text
Telegram bot token
Backend base URL
Agent Server base URL
Redis URL
Webhook secret
history limit
timeouts
```

---

### `entrypoints/fastapi.py`

Creates FastAPI app.

Includes routers.

Initializes lifecycle hooks.

---

### `entrypoints/telegram_webhook.py`

Telegram webhook route.

Recommended endpoint:

```text
POST /telegram/webhook
```

Responsibilities:

```text
parse Telegram update
validate webhook secret if needed
call handle_update application service
return Telegram-compatible response
```

Should not contain full orchestration logic.

---

### `entrypoints/internal_api.py`

Internal API for Backend or trusted internal services.

Recommended endpoint:

```text
POST /internal/messages/send
```

Responsibilities:

```text
accept business_user_id and message text
call send_message application service
return delivery status
```

---

### `application/handle_update.py`

Main incoming Telegram message use case.

Pseudo-flow:

```text
handle_telegram_update(update):
  check idempotency
  extract telegram user/chat/message
  resolve business_user_id
  append user message to session history
  load session history
  call Agent Server
  append assistant message to session history
  send assistant response to Telegram
```

---

### `application/send_message.py`

Backend-triggered outgoing message use case.

Pseudo-flow:

```text
send_message_to_user(business_user_id, text):
  resolve telegram_chat_id
  send Telegram message
  optionally append message to session history
```

---

### `clients/backend_client.py`

HTTP client to Backend.

Initial capabilities:

```text
get_user_by_telegram_identity
create_user_from_telegram_identity
get_or_create_user_by_telegram_identity
```

The exact API can be designed later.

---

### `clients/agent_client.py`

HTTP client to Agent Server.

Initial capability:

```text
run_agent_turn
```

It sends:

```text
business_user_id
session_id
channel
current user message
message history
metadata/correlation_id
```

---

### `clients/telegram_client.py`

Wrapper around Telegram Bot API.

Initial capabilities:

```text
send_message
send_typing_action
set_webhook later if needed
```

---

### `storage/redis_user_mapping.py`

Redis-backed identity cache.

Responsibilities:

```text
get_business_user_id_by_telegram_user_id
set_business_user_mapping
get_telegram_chat_id_by_business_user_id
set_chat_mapping
```

---

### `storage/redis_session_store.py`

Redis-backed conversation session transcript.

Responsibilities:

```text
append_message
get_messages
trim_history
clear_session
```

Recommended initial trim policy:

```text
last 50 messages
```

---

### `storage/redis_idempotency.py`

Redis-backed update deduplication.

Responsibilities:

```text
is_processed(update_id)
mark_processed(update_id)
```

Recommended TTL:

```text
several days
```

---

### `schemas/telegram.py`

DTOs for normalized Telegram update/message data.

---

### `schemas/agent.py`

DTOs for Agent Server request/response.

---

### `schemas/internal.py`

DTOs for internal API requests, especially outgoing message delivery.

---

## Boundaries

### Telegram Gateway owns

```text
Telegram webhook handling
Telegram Bot API delivery
Telegram identity cache
Telegram chat id cache
short-term conversation transcript in Redis
internal send-message endpoint
Telegram-specific transport metadata
```

### Telegram Gateway does not own

```text
canonical user identity
Planner domain logic
plans
schedule
graph
analytics
connectors
agent reasoning
LLM tool calls
long-term memory
business persistence
```

---

## First User Message Flow

Example: user sends "Привет".

```text
1. Telegram sends update to Telegram Gateway.
2. Gateway checks telegram_update_id idempotency.
3. Gateway extracts telegram_user_id and telegram_chat_id.
4. Gateway checks Redis mapping telegram_user_id -> business_user_id.
5. If not found, Gateway calls Backend.
6. Backend returns existing user or creates a new business user.
7. Gateway caches telegram_user_id -> business_user_id.
8. Gateway caches business_user_id -> telegram_chat_id.
9. Gateway creates session_id = telegram:{telegram_chat_id}.
10. Gateway appends user message to Redis session history.
11. Gateway loads recent history.
12. Gateway calls Agent Server with business_user_id, session_id, message, history.
13. Agent Server returns assistant message.
14. Gateway appends assistant message to Redis session history.
15. Gateway sends assistant message to Telegram.
16. Gateway marks update as processed.
```

---

## Backend Notification Flow

Example: schedule reminder.

```text
1. Backend schedule/api_scheduler decides to notify user.
2. Backend calls Telegram Gateway internal API:
   POST /internal/messages/send
3. Payload contains business_user_id and text.
4. Gateway resolves business_user_id -> telegram_chat_id from Redis.
5. If not found, Gateway may ask Backend for Telegram mapping or return delivery error.
6. Gateway sends message through Telegram Bot API.
7. If store_in_session=true, Gateway appends message to Redis session history.
8. Gateway returns delivery result to Backend.
```

---

## Open Decisions

```text
Should Telegram identity mapping be durably stored only in Backend, or also persisted by Telegram Gateway later?

Should Telegram Gateway support only one active session per chat at first?

What should be the exact history retention policy: last N messages, TTL, token estimate, or mixed?

Should backend-triggered notifications always be included in conversation history?

Should Telegram Gateway support message edits, buttons, callback queries, and pending actions in the first version?

Should Telegram Gateway expose a health/debug endpoint showing Redis and Backend/Agent connectivity?

Should Telegram Gateway be allowed to call Backend directly only for user resolution, or also for other small metadata requests?
```

---

## Initial Implementation Priority

Recommended order later:

```text
1. FastAPI app and health endpoint.
2. Telegram webhook endpoint.
3. Telegram client wrapper.
4. Redis user mapping cache.
5. Backend user resolution client.
6. Redis session store.
7. Agent Server client.
8. Incoming message flow end-to-end.
9. Internal send-message endpoint.
10. Redis idempotency.
```

This keeps the service small and testable.

---

## Current Conclusion

Telegram Gateway should be a small FastAPI service.

Its essential responsibilities are:

```text
resolve Telegram identity to business_user_id
cache mapping in Redis
store short-term conversation transcript in Redis
call Agent Server with message history
send Agent response back to Telegram
expose internal endpoint for backend-triggered Telegram messages
```

It should remain thin and should not become a domain service.

The most important architectural rule:

```text
Backend is canonical identity and domain state.
Agent Server is reasoning.
Telegram Gateway is transport and conversation cache.
