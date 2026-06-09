# Runtime Context

This document summarizes the intended responsibility of the `runtime` context in the Planner backend.

Unlike documents such as `schedule_domain.md` or `domain_connectors.md`, this file is not a pure domain-model description. `runtime` is a technical/platform context. Its purpose is to describe how the backend reliably runs internal scheduled and asynchronous work inside the modular monolith.

## Purpose

`runtime` owns backend operational execution.

It answers questions such as:

```text
Which internal system jobs should run?
When should they run?
Was a job already scheduled?
Is a job currently running?
Did the last execution succeed or fail?
Should the job be retried?
How do we prevent the same job from being executed twice accidentally?
```

The context exists because the Planner backend does not execute all work directly inside user-facing HTTP/Telegram requests.

Some work is delayed, periodic, or system-triggered:

```text
nightly planning
day generation during user sleep
connector polling/sync
connector event processing
reminder dispatch
maintenance jobs
ready-stream draining
```

`runtime` provides a stable internal place for this operational lifecycle.

---

## Runtime is not a business domain

`runtime` is not a user-facing bounded context.

It does not model the user's schedule, course progress, connector semantics, graph memory, analytics profile, or reminders as business concepts.

Instead, it models the backend's execution machinery:

```text
system jobs
scheduled runs
execution attempts
locks
retry state
technical failure state
```

This distinction is important.

Business domains decide what the system should do.

`runtime` decides when and how backend work is triggered reliably.

Example:

```text
schedule owns Reminder as user-facing domain state.
runtime may later trigger the technical reminder delivery job.
```

Another example:

```text
connectors owns ConnectorJob and ConnectorEvent as integration-domain records.
runtime may trigger a connector polling or event-processing use case.
```

---

## Why this context exists

The project has two different scheduling concerns that must stay separate.

### User-facing schedule domain

The `schedule` context owns user time planning:

```text
weekly templates
generated days
scheduled activities
reminders
deadlines
date observations
```

It may request technical delayed work, but it does not own technical scheduler infrastructure.

### Backend runtime context

The `runtime` context owns backend execution:

```text
periodic system jobs
technical scheduled jobs
job run state
execution locking
retry/failure tracking
```

It does not decide the semantic meaning of user plans, reminders, deadlines, or connector events.

### Shared API scheduler client

The shared API scheduler client is lower-level infrastructure:

```text
shared/api_scheduler
```

It is a port/adapter around the actual technical scheduler API or library.

Other contexts should use it through application ports, not by importing scheduler implementation details into their domains.

The intended separation is:

```text
context/schedule
  user-facing time planning domain

context/connectors
  external integration domain

context/runtime
  backend operational execution context

shared/api_scheduler
  technical client/adapter for scheduling calls
```

---

## Responsibility

`runtime` should own:

```text
system job registration
scheduled system job persistence
job execution state
job run history
technical retry metadata
execution locks / idempotency guards
last success / last failure timestamps
failure messages for operations/debugging
runtime-facing dispatch into application use cases
```

`runtime` should not own:

```text
weekly schedule templates
generated schedule days
reminder domain state
deadline domain state
course tasks
course progress
connector connection lifecycle
connector event payload semantics
external OAuth credentials
agent interpretation
business observations
analytics conclusions
knowledge graph facts
```

The key principle:

```text
runtime runs backend work;
domain contexts define what that work means.
```

---

## Typical flows

## Nightly day generation

```text
Runtime scheduled job becomes due
  -> runtime acquires execution lock
  -> runtime records JobRun as running
  -> runtime calls schedule application service
  -> schedule generates next user's ScheduleDay
  -> runtime marks JobRun as succeeded or failed
```

`runtime` does not generate the day itself.

The generated day belongs to `schedule/execution`.

---

## Reminder delivery

```text
User creates Reminder
  -> schedule/commitment stores Reminder
  -> schedule application service requests technical scheduling through a port
  -> technical scheduler later triggers runtime/entrypoint
  -> runtime calls reminder dispatch use case
  -> schedule/application loads Reminder and dispatches notification
```

`runtime` does not own the Reminder entity.

It only participates in reliable technical triggering.

---

## Connector sync

```text
Runtime scheduled job becomes due
  -> runtime starts connector sync run
  -> connectors application service loads eligible ConnectorConnection / ConnectorJob
  -> connector adapter calls external provider
  -> connectors records ConnectorEvent
  -> runtime records technical success/failure of the run
```

`runtime` does not interpret Gmail, YouTube, calendar, or external payloads.

That belongs to `connectors` and downstream application/agent workflows.

---

## Ready-stream processing

```text
Messages are written to ready stream
  -> runtime scheduled processor wakes up
  -> runtime drains or delegates ready-stream work
  -> target application service handles the message
  -> runtime records processing result
```

The stream transport is infrastructure.

The semantic action still belongs to the target context.

---

# Internal Model

The first version of `runtime` should stay small.

It does not need a rich domain layer unless real invariants appear. A thin application/system model is enough.

Possible core concepts:

```text
SystemJob
ScheduledSystemJob
JobRun
JobExecutionStatus
RetryPolicy
ExecutionLock
```

These concepts are operational, not business-domain concepts.

---

## SystemJob

Represents a known backend job type that the platform can execute.

Examples:

```text
nightly_day_generation
connector_sync
connector_event_dispatch
reminder_dispatch
ready_stream_drain
maintenance_cleanup
```

Important fields may include:

```text
id
name
description
enabled
created_at
updated_at
```

Meaning:

```text
A stable definition of a backend operation that may be scheduled or triggered.
```

`SystemJob` should not contain business execution logic. It identifies what can be run.

---

## ScheduledSystemJob

Represents a persisted technical schedule for a `SystemJob`.

Important fields may include:

```text
id
system_job_id
schedule_key
scheduled_at
cron_expression
status
last_scheduled_at
next_run_at
created_at
updated_at
```

Meaning:

```text
A durable record that a system job should be triggered at a time or according to a recurring schedule.
```

Why persistence exists:

```text
The backend needs robustness across restarts.
The system should know what was registered with the technical scheduler.
Duplicate registration should be avoidable.
Operational state should be inspectable.
```

---

## JobRun

Represents one execution attempt of a system job.

Important fields may include:

```text
id
system_job_id
scheduled_system_job_id
status
started_at
finished_at
attempt_number
error_message
metadata
```

Meaning:

```text
A record that the backend attempted to run some system job.
```

Typical statuses:

```text
pending
running
succeeded
failed
cancelled
skipped
```

The exact enum should be introduced only when implementation needs it.

---

## RetryPolicy

Represents technical retry rules for a runtime job.

Possible fields:

```text
max_attempts
retry_delay_seconds
backoff_strategy
```

Meaning:

```text
How runtime should retry technical failures.
```

This should not be confused with business retries.

Example:

```text
Retrying connector sync because Gmail API returned a temporary error is runtime/integration behavior.
Creating another course activity because the user missed a study session is schedule/course planning behavior.
```

---

## ExecutionLock

Represents a guard against duplicate execution.

Meaning:

```text
Only one worker/process should execute a particular runtime job for a particular key at a time.
```

Examples of lock keys:

```text
nightly_day_generation:user_id:date
connector_sync:connection_id
reminder_dispatch:reminder_id
ready_stream_drain:stream_name
```

The first implementation may use database uniqueness/transactions rather than a separate domain object.

The important invariant is:

```text
A runtime job should be idempotent or protected by a lock when duplicate execution would be harmful.
```

---

# Application Layer

`runtime` is expected to have a thin application layer.

Possible services:

```text
RuntimeJobRegistry
RuntimeSchedulerService
RuntimeExecutionService
RuntimeLockService
RuntimeRetryService
```

Possible use cases:

```text
register_system_jobs
schedule_system_job
run_due_job
record_job_started
record_job_succeeded
record_job_failed
retry_failed_job
acquire_execution_lock
release_execution_lock
```

The application layer coordinates:

```text
runtime persistence
shared API scheduler port
cross-context application calls
logging/tracing
idempotency
```

It should not contain deep business logic from schedule, course, connectors, graph, analytics, or user.

---

# Ports and Adapters

`runtime` should depend on ports for technical infrastructure.

Possible ports:

```text
RuntimeJobRepository
ScheduledSystemJobRepository
JobRunRepository
ExecutionLockRepository
ApiSchedulerPort
ClockPort
TransactionManager
Logger/Tracer
```

The API scheduler port should hide the concrete scheduling implementation.

Example port-level operations:

```text
schedule_once(key, run_at, payload)
schedule_recurring(key, cron_expression, payload)
cancel(key)
reschedule(key, run_at)
```

The adapter may use:

```text
shared/api_scheduler
```

But application/domain code should not depend directly on the concrete scheduler library.

---

# Persistence Shape

The exact database schema can evolve, but a natural first shape is:

```text
runtime_system_jobs
  id
  name
  description
  enabled
  created_at
  updated_at
```

```text
runtime_scheduled_jobs
  id
  system_job_id
  schedule_key
  schedule_kind
  scheduled_at
  cron_expression
  next_run_at
  status
  created_at
  updated_at

Unique:
  schedule_key
```

```text
runtime_job_runs
  id
  system_job_id
  scheduled_job_id
  run_key
  status
  attempt_number
  started_at
  finished_at
  error_message
  metadata

Useful indexes:
  system_job_id
  scheduled_job_id
  run_key
  status
  started_at
```

```text
runtime_locks
  lock_key
  owner_id
  acquired_at
  expires_at

PK:
  lock_key
```

This persistence is technical state.

It exists for reliability, observability, deduplication, and recovery.

---

# Relationship with Other Contexts

## Runtime and Schedule

Correct:

```text
runtime triggers schedule application service to generate tomorrow's day.
runtime triggers schedule application service to dispatch due reminders.
schedule uses a port to request technical delayed reminder execution.
```

Incorrect:

```text
runtime creates ScheduleDay entities directly.
runtime mutates Reminder business state without going through schedule application service.
runtime interprets schedule observations.
```

---

## Runtime and Connectors

Correct:

```text
runtime triggers connectors application service to poll/sync external providers.
runtime records technical execution state of that system job.
connectors records ConnectorJob and ConnectorEvent domain state.
```

Incorrect:

```text
runtime owns Gmail message semantics.
runtime owns YouTube polling cursor semantics unless this is purely technical execution state.
runtime converts connector payloads into deadlines or course tasks.
```

---

## Runtime and Course

Correct:

```text
runtime may trigger a course-related maintenance or planning use case.
course application service owns course progress/task changes.
```

Incorrect:

```text
runtime changes course task status as part of generic job execution.
```

---

## Runtime and User

Correct:

```text
runtime may read user timezone/language through application services when scheduling per-user jobs.
user context owns user identity, timezone, language, and profile metadata.
```

Incorrect:

```text
runtime owns user timezone or language fields.
```

---

# File Layout

Recommended initial layout:

```text
src/backend/context/runtime/
  __init__.py

  application/
    __init__.py
    services/
      __init__.py
      runtime_scheduler_service.py
      runtime_execution_service.py
      runtime_lock_service.py
    ports/
      __init__.py
      api_scheduler_port.py
      repositories.py
      clock.py

  infrastructure/
    __init__.py
    persistence/
      __init__.py
      models.py
      repositories.py
    adapters/
      __init__.py
      api_scheduler_adapter.py

  entrypoints/
    __init__.py
    jobs.py
```

A `domain/` folder is optional.

If the first implementation only contains thin operational records and services, the context can start without a rich domain layer.

If runtime invariants become meaningful later, a small domain/system model can be introduced:

```text
runtime/domain/
  entities/
    system_job.py
    scheduled_system_job.py
    job_run.py
  value_objects/
    job_status.py
    schedule_kind.py
```

The important rule:

```text
Do not force runtime to look like a rich business domain if it is only a technical execution context.
```

---

# Implementation Rules

Recommended first-slice style:

```text
Keep runtime small.
Prefer application services over speculative domain modeling.
Persist only the state needed for reliability.
Make job execution idempotent where possible.
Use locks or uniqueness when duplicate execution would be harmful.
Call other contexts through application/use-case boundaries.
Keep scheduler-specific code behind ports/adapters.
Do not import concrete scheduler clients into business domains.
```

Operational failures should be recorded as runtime failures.

Business failures should stay in their owning context.

Example:

```text
Failed to acquire execution lock
  -> runtime technical failure/skip

Reminder is cancelled before dispatch
  -> schedule application decides no notification should be sent

Gmail API is temporarily unavailable
  -> connectors/runtime execution failure depending on where it happened

User missed planned reading activity
  -> schedule/course observation or progress handling, not runtime failure
```

---

# Naming Rules

Use `runtime` for the context:

```text
context/runtime
```

Use `schedule` for user-facing time planning:

```text
context/schedule
```

Use `api_scheduler` only for the technical scheduler client/adapter if the underlying integration is called API Scheduler:

```text
shared/api_scheduler
```

Avoid naming the context `api_scheduler` because that makes a technical adapter look like a bounded context.

Avoid naming it simply `scheduler` because it can be confused with the user-facing `schedule` domain.

---

# Summary

`runtime` is the backend operational execution context.

It exists to make delayed, periodic, and asynchronous backend work reliable inside the modular monolith.

It owns:

```text
system jobs
scheduled technical runs
job run history
locks
retry metadata
scheduler registration state
technical execution observability
```

It does not own:

```text
user schedule semantics
reminder domain state
deadline domain state
course progress
connector payload meaning
agent interpretation
analytics or graph memory
```

The core architectural rule is:

```text
runtime triggers work;
other contexts own the meaning of that work.
```

This keeps technical execution separate from business modeling and prevents `runtime` from becoming a generic place where domain logic leaks.
