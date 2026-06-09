# Connectors domain context

This document summarizes the current state of the `connectors` bounded context in the planner backend. It is intended as a compact context file for future ChatGPT sessions and implementation discussions.

## Purpose

`connectors` is an integration-oriented bounded context. It manages how external systems become connected to the planner platform and how external signals enter the system.

Examples of external systems:

- Gmail
- YouTube
- later: Google Calendar, GitHub, Notion, etc.

The context is not responsible for interpreting user life-planning semantics directly. It should not own concepts such as deadlines, courses, schedule blocks, reminders, observations, or tasks. Its responsibility is to represent external integrations, record incoming external events, and provide a clean boundary for application/services/adapters to process them.

A typical flow should look like this:

```text
External provider
  -> connector adapter
  -> connectors shared domain: connection/job/event
  -> application service / workflow dispatch
  -> target domain or agent interpretation
```

For example:

```text
Gmail message received
  -> Gmail adapter reads message
  -> ConnectorEvent is recorded
  -> application service dispatches workflow
  -> agent/application extracts possible deadline
  -> schedule/observations domain handles the business result
```

## Current implementation status

At the moment only the shared domain part is implemented.

Current structure:

```text
connectors/
  domain/
    shared/
      entities/
        connector_connection.py
        connector_event.py
        connector_job.py
        __init__.py
      value_objects.py
      __init__.py
```

Provider-specific domain folders such as `gmail/` and `youtube/` are intentionally not implemented yet. They may exist later as placeholders or README-only modules, but we do not want to invent provider-specific entities before implementing the real adapters and understanding the real API shape.

## Design decision: keep shared domain small

The first version was intentionally simplified.

We decided not to create separate value objects for every simple string field. For example, these are currently plain fields with validation inside entities:

- `external_account_ref`
- `external_event_id`
- `scopes`
- error messages
- workflow names

This is deliberate. Only meaningful enum-like concepts live in `value_objects.py`. Simple one-field wrappers were avoided because they added ceremony without enough domain value at this stage.

## Shared value objects

All shared enum-like types are currently collected in one file:

```text
domain/shared/value_objects.py
```

It contains:

```text
ConnectorProvider
  - gmail
  - youtube

ConnectorConnectionStatus
  - active
  - expired
  - revoked
  - error

ConnectorJobStatus
  - pending
  - running
  - succeeded
  - failed
  - cancelled

ConnectorJobType
  - poll
  - sync
  - process_event

ConnectorEventStatus
  - received
  - dispatched
  - ignored
  - failed

ConnectorEventType
  - gmail_message_received
  - youtube_video_detected
```

These enums are enough for the current shared domain skeleton. New statuses/types should be added only when real application/adapters need them.

## Entity: ConnectorConnection

`ConnectorConnection` represents a user's connection to an external provider account.

It answers questions like:

- Which user connected which provider?
- Which external account is connected?
- Is the connection active, expired, revoked, or in error state?
- What scopes were granted?
- When did this connection last succeed or fail?

Important fields:

```text
id
user_id
provider
external_account_ref
status
scopes
connected_at
updated_at
last_success_at
last_error_at
error_message
```

Important behavior:

```text
activate()
mark_expired()
revoke()
mark_error()
mark_success()
replace_scopes()
can_run_jobs()
```

Domain meaning:

- A job should run only when the connection can run jobs.
- Revoked/expired/error states are part of the domain lifecycle, not only infrastructure details.
- Credentials and token encryption are not modeled here. They belong to infrastructure/persistence.

## Entity: ConnectorJob

`ConnectorJob` represents a domain-level record that some connector work should happen or has happened.

It is not a Celery/RQ/cron implementation detail. It is our own domain record of connector work.

Examples:

- poll YouTube channel
- sync Gmail messages
- process connector event

Important fields:

```text
id
connection_id
provider
job_type
scheduled_at
status
retry_count
max_retries
started_at
finished_at
error_message
```

Important behavior:

```text
start()
succeed()
fail()
cancel()
retry()
can_retry()
is_finished()
```

Domain meaning:

- A pending job can be started.
- A running job can succeed or fail.
- A failed job can be retried until retry limit is reached.
- Finished jobs should not be cancelled or restarted accidentally.

The execution mechanism itself remains outside the domain. Application/services and infrastructure decide how jobs are picked up and executed.

## Entity: ConnectorEvent

`ConnectorEvent` represents an external signal normalized into the connectors context.

Examples:

- Gmail message received
- YouTube video detected

Important fields:

```text
id
connection_id
user_id
provider
event_type
occurred_at
received_at
external_event_id
payload
status
dispatched_workflow_name
error_message
```

Important behavior:

```text
dispatch()
ignore()
fail()
replace_payload()
is_terminal()
```

Domain meaning:

- The event records that something happened outside the system.
- The event may later be dispatched to an application service, workflow, or agent process.
- The event itself should not know how to create deadlines, reminders, schedule blocks, or other target-domain objects.
- Payload is currently a plain `dict | None` for v2 simplicity. If needed later, provider-specific payload models or payload references can be introduced.

Deduplication is not currently represented as a separate value object. It can be handled later through repository/database uniqueness, for example by provider plus external event id.

## Provider-specific domains are postponed

We explicitly decided not to model detailed Gmail or YouTube domain entities yet.

Possible future Gmail concepts:

- Gmail message reference
- Gmail thread reference
- Gmail history cursor
- Gmail label reference
- Gmail watch/subscription state
- Gmail matching rule/filter

Possible future YouTube concepts:

- YouTube channel reference
- YouTube video reference
- YouTube channel subscription
- YouTube polling cursor
- playlist reference

These should be introduced only after real adapters/application services show which concepts are stable.

The reason: modeling Gmail or YouTube blindly is risky. Real APIs may force different shapes, for example Gmail `historyId`, labels, threads, pagination, watch/pubsub behavior, sync windows, token refresh, and rate limits.

## Next architectural direction

The next step should not be more speculative domain modeling. The next step should be the integration side:

```text
connectors/
  application/
    services/
      ...
    ports/
      ...

  infrastructure/
    adapters/
      gmail/
        ...
      youtube/
        ...
```

The current preference is:

- application services contain orchestration logic;
- use cases may later be built on top of application services;
- adapters perform real HTTP/API calls;
- shared domain remains focused on connection/job/event lifecycle;
- provider-specific domain is extracted only after repeated real integration needs appear.

A reasonable first practical direction:

```text
Gmail adapter
  - OAuth/token usage
  - list/read messages
  - normalize message into ConnectorEvent

YouTube adapter
  - fetch channel/latest videos
  - polling behavior
  - normalize new video into ConnectorEvent
```

Then application services can coordinate:

```text
connection state
job lifecycle
event persistence
event dispatch to workflows/agents
```

## Boundary rules

`connectors` should own:

- external provider connection state;
- connector job lifecycle;
- incoming external event lifecycle;
- provider-specific integration rules only when they become stable;
- normalized handoff into application services/workflows.

`connectors` should not own:

- schedule blocks;
- deadlines;
- courses;
- observations;
- reminders;
- user semantic interpretation;
- OAuth HTTP clients directly in domain;
- token encryption in domain;
- cron/Celery/RQ implementation details in domain.

The key principle:

```text
connectors delivers external signals;
target domains and application/agent workflows decide what those signals mean.
```
