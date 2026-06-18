# AGENT.md — Telegram Gateway

This file describes the general structure and architectural rules of the `telegram-gateway` service. It is not a task list and should not contain detailed instructions for a specific implementation task.

## Service purpose

`telegram-gateway` is a standalone FastAPI service that connects the internal Planner system with Telegram.

The service is responsible for:

- binding `business_user_id` to a Telegram account and Telegram chat;
- sending messages to users in Telegram;
- storing the current user-agent conversation session;
- forwarding user messages to the Agent Server;
- forwarding closed sessions to the Agent Server for further processing.

The service does not own user business logic, schedules, runtime jobs, user profile state, or agent workflows. Those responsibilities belong to Backend and Agent Server.

## Architectural style

The service follows a clean architecture style with a clear split into:

```text
domain
application
adapters
```

The core idea is that the application layer defines scenarios and ports, while infrastructure details live in adapters.

Internal logic must not depend directly on FastAPI, SQLAlchemy, Redis, HTTP clients, or Telegram Bot API. These dependencies must be connected through ports and adapters.

## Domain

Directory:

```text
src/telegram_gateway/domain/
```

This directory contains the domain models of the service.

The domain should stay simple. In this service, domain models mostly describe:

- Telegram binding;
- session messages;
- message roles.

The domain must not know about FastAPI, Redis, Postgres, HTTP, or external services.

## Application

Directory:

```text
src/telegram_gateway/application/
```

The application layer contains the service scenarios.

### Use cases

Directory:

```text
src/telegram_gateway/application/use_cases/
```

A use case is a class that describes one application scenario.

A use case receives its dependencies through `__init__` and exposes one or more public methods to execute the scenario.

If a use case needs access to persistent storage, it works through `UnitOfWork`. Unit of Work is passed into the use case method and controls the transaction at the scenario level.

A use case may use:

- ports;
- application services;
- domain models;
- Unit of Work.

A use case must not directly create SQLAlchemy sessions, Redis clients, HTTP clients, or FastAPI responses.

### Services

Directory:

```text
src/telegram_gateway/application/services/
```

Application services may be created when reusable application-level logic is needed by multiple use cases.

An application service is similar to a use case because it works with application abstractions, but it usually does not manage Unit of Work itself. If it needs repository access, it receives a repository or Unit of Work from the caller.

Do not create services in advance if they are not needed.

### Ports

Directory:

```text
src/telegram_gateway/application/ports/
```

Ports describe application-layer dependencies on the outside world.

Examples of ports:

- Agent Server client;
- Backend client;
- Telegram message sender;
- conversation store;
- Telegram binding repository;
- Unit of Work;
- Telegram update deduplicator.

Ports are written as simple classes whose methods raise `NotImplementedError`.

Example style:

```python
class SomePort:
    async def do_something(self) -> None:
        raise NotImplementedError
```

Adapters must implement these ports.

### Errors

File:

```text
src/telegram_gateway/application/errors.py
```

This file contains application/business errors of the service.

Use cases should raise application errors, and the inbound layer should map them to HTTP responses through exception handlers.

Avoid scattering random `ValueError` and `TypeError` across the code when the error is a controlled scenario error. Prefer adding an explicit application error.

## Adapters

Directory:

```text
src/telegram_gateway/adapters/
```

Adapters are the integration layer with the outside world.

### Inbound adapters

Directory:

```text
src/telegram_gateway/adapters/inbound/
```

Inbound adapters receive external requests and call use cases.

This layer contains:

- FastAPI routes;
- request/response schemas;
- dependencies;
- exception handlers;
- mappers from incoming payloads to internal DTOs.

An inbound adapter must not contain business logic. Its responsibility is to receive an HTTP request, validate/map the data, call a use case, and return a response.

### Outbound adapters

Directory:

```text
src/telegram_gateway/adapters/outbound/
```

Outbound adapters implement application ports.

This layer contains integrations with:

- Postgres;
- Redis;
- Telegram Bot API;
- Backend HTTP API;
- Agent Server HTTP API.

An outbound adapter may know about concrete libraries: SQLAlchemy, Redis client, httpx, and so on. The application layer must not know about them.

## API and dependencies

FastAPI API lives in the inbound layer.

The API file should only describe the HTTP contract of the service and call use cases.

Dependencies are used to obtain Unit of Work, use case instances, and other objects from `app.state`.

Do not manually create dependencies inside endpoints. All wiring must happen in `main.py` / lifespan.

## Exception handlers

Exception handlers live in the inbound layer.

Their purpose is to map application errors and unexpected errors to HTTP responses.

This allows use cases to raise normal application exceptions while keeping the API from failing in an uncontrolled way.

## Settings

File:

```text
src/telegram_gateway/settings.py
```

This file describes service settings:

- service host/port;
- Postgres URL;
- Redis URL;
- Telegram bot token;
- Backend host/port;
- Agent Server host/port;
- HTTP timeouts;
- webhook-related settings, if webhook is enabled.

Settings are read from `.env`.

## Logging

File:

```text
src/telegram_gateway/logging.py
```

The service uses structured logging.

Use cases should log important scenario boundaries:

- use case start;
- use case completion;
- key identifiers: `business_user_id`, `telegram_chat_id`, `telegram_user_id`;
- scenario result.

Do not log everything. Do not log full user text unless it is explicitly needed for development diagnostics.

## Main and lifespan

File:

```text
src/telegram_gateway/main.py
```

`main.py` is responsible for creating the FastAPI application and wiring dependencies.

The lifespan creates:

- database engine;
- session factory;
- Redis clients/adapters;
- HTTP clients;
- use cases;
- objects stored in `app.state`.

Startup and shutdown actions also belong here.

Endpoints must not assemble dependencies by themselves. They should receive already wired use cases through dependencies.

## General rule for changes

When adding new functionality, first decide:

1. whether a new domain model is needed;
2. whether a new port is needed;
3. whether a new use case is needed;
4. which inbound endpoint calls that use case;
5. which outbound adapter implements the external call or storage.

Do not mix HTTP, Redis/Postgres, and business scenarios in one place.

The service should remain a small gateway service: transport, Telegram binding, Telegram delivery, session buffer, and communication with Agent Server.
