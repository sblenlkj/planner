# Command Executors

This module contains command execution entrypoints and the low-level execution engine used by the orchestration layer.

The command executor layer is responsible for:

- executing command handlers inside a unit-of-work lifecycle
- collecting domain events recorded by aggregate roots
- pushing collected events into the event queue
- draining the event queue
- dispatching events through the configured event dispatcher
- enforcing event processing limits

It is not responsible for domain behavior, repository logic, command deserialization, HTTP routing, broker subscriptions, or dependency injection container setup.

## Module layout

```text
command_executors/
  __init__.py
  config.py
  engine.py
  exceptions.py
  executors.py
```

## `engine.py`

`engine.py` contains the low-level execution mechanics.

The main class is `CommandExecutionEngine`.

The engine receives:

```text
command + already resolved command handler
```

and executes them through:

```text
UoW.run(...)
collect_new_events()
EventQueue
EventDispatcher
```

The engine does not resolve command handlers. It does not know about command registries or command handler registries.

This separation allows the same engine to be used by different public executor APIs.

## `executors.py`

`executors.py` contains public executor wrappers.

There are two common executor styles.

### `CommandExecutor`

`CommandExecutor` is the normal high-level API.

It receives only a command:

```python
await command_executor.handle(command)
```

Internally it:

1. resolves the command handler through `CommandHandlerResolverPort`
2. passes the command and handler to `CommandExecutionEngine`

This is the preferred API for input adapters such as REST endpoints, consumers, CLI commands, and in-process facades.

### `DirectCommandExecutor`

`DirectCommandExecutor` is a lower-level API.

It receives both the command and an already created handler:

```python
await direct_command_executor.handle(command, handler)
```

This is useful for tests, experiments, manual wiring, or places where the caller already owns handler construction.

`DirectCommandExecutor` still delegates execution mechanics to `CommandExecutionEngine`.

## `config.py`

`config.py` contains executor configuration.

The core execution mode is `CommandExecutionMode`.

### `IN_TRANSACTION`

The command handler and event draining run inside the command UoW lifecycle.

This mode allows context event handlers to receive the current command UoW through `EventHandlerContextWithCommandUOW`.

In this mode, event draining happens in cycles:

```text
collect events from UoW
push events to queue
process queue
collect events from UoW again
repeat until no new events exist
```

This is important because event handlers may mutate aggregates through the current UoW and produce new domain events.

### `AFTER_EXECUTION`

The command handler runs inside the command UoW lifecycle first.

After the command finishes, the engine collects events once and drains the event queue outside the command UoW context.

Event handlers do not receive the current command UoW in this mode.

## Event draining

The engine has two important safety limits:

```text
max_processed_events
max_drain_cycles
```

`max_processed_events` prevents an unbounded number of events from being processed in a single command execution.

`max_drain_cycles` prevents endless event-generation cycles where event handlers keep producing new domain events through the current UoW.

Both limits exist to protect the process from accidental infinite event loops.

## Event dispatcher dependency

The engine depends on `EventDispatcherPort`.

The event dispatcher decides how to invoke event handlers:

```text
plain event handler
context event handler
```

The command engine does not know how event handlers are constructed. Handler construction belongs to event handler resolvers.

## Command handler dependency

The engine receives an already resolved command handler.

The high-level `CommandExecutor` uses `CommandHandlerResolverPort` to resolve the handler.

The direct executor receives the handler from the caller.

This gives two valid integration styles:

```text
command -> resolver -> handler -> engine
command + handler -> engine
```

## Modular monolith behavior

There is no separate modular-monolith command execution engine.

The regular `CommandExecutionEngine` works for both service mode and modular monolith mode because event collection is delegated to the UoW public API:

```python
uow.collect_new_events()
```

In service mode, a regular UoW collects events from its own tracking repositories.

In modular monolith mode, a modular-aware UoW may override `collect_new_events()` and delegate event collection to a modular UoW coordinator.

This keeps the engine generic and avoids duplicating execution logic.

## Relationship with UoW

The engine depends on `AbstractOrchestrationUnitOfWork`.

The UoW owns execution lifecycle details such as:

- session opening
- transaction boundaries
- commit / rollback behavior
- request-scoped resources
- in-memory test lifecycle flags

The engine does not implement database/session behavior. It only calls:

```python
await uow.run(...)
uow.collect_new_events()
```

## Relationship with registries and resolvers

Registries store metadata:

```text
command type -> command handler type
event type -> event handler types
```

Resolvers create handler instances:

```text
handler type -> initialized handler instance
```

Executors run initialized handlers through the UoW/event pipeline.

Keep these responsibilities separate.

## Naming rules

Use:

```text
CommandExecutionEngine
CommandExecutor
DirectCommandExecutor
CommandExecutorConfig
CommandExecutionMode
```

Avoid naming modular-monolith-specific executor engines unless the execution mechanics actually diverge from the regular engine.

At the current design stage, modular monolith behavior belongs to UoW/coordinator implementations, not to a separate command engine.

## Design rule

The command executor module should stay focused on execution mechanics.

Do not add:

- command deserialization
- HTTP routing
- broker consumer logic
- concrete repository code
- concrete database sessions
- domain-specific UoW creation
- modular context creation rules

Those responsibilities belong to input adapters, DI/container setup, application composition roots, or modular-monolith UoW/coordinator implementations.
