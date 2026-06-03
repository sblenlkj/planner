# Backend Domain Overview

## Purpose

This document is the first high-level domain overview for the Planner backend.

The backend is a Direttore-based modular monolith. It owns durable domain state, application use cases, command/query handling, persistence, internal events, and typed backend capabilities exposed to other services.

The backend does not own agent reasoning and does not own Telegram-specific UX.

At the current stage, the goal is not to design every domain model in detail. The goal is to fix the first domain map: which bounded contexts exist, what each context owns, what kind of entities and tables may appear there, and where future detailed design should continue.

---

## Backend Role in the System

The backend is the source of truth for Planner domain state.

It owns:

```text
users
plans (ATTENTION! RENAMED TO COURSES!!!)
schedule
knowledge graph
external data connections
analytics/profile signals
scheduled backend operations
```

It exposes capabilities to other services:

```text
Agent Server -> Backend:
  gRPC

Telegram Gateway -> Agent Server:
  HTTP

Backend -> Telegram Gateway:
  HTTP for outgoing delivery if needed

Backend internal async/event behavior:
  Redis Streams later, behind EventStreamPort

Backend scheduled operations:
  API scheduler / runtime scheduler inside backend process
```

The Agent Server should call backend through typed capabilities. It should not read backend database tables directly.

The Telegram Gateway should not contain Planner domain logic. It should map Telegram UX into system requests and render system responses back to Telegram.

---

## Backend Process Model

The backend is planned as one process with one main FastAPI application.

FastAPI is the main process entrypoint. During application startup/lifespan it can initialize:

```text
Direttore modular monolith application
database connections
shared ports and infrastructure
gRPC server runtime
API scheduler runtime
HTTP routes
```

Conceptually:

```text
FastAPI process
  -> builds backend container
  -> builds Direttore application
  -> starts gRPC server
  -> starts API scheduler runtime
  -> serves HTTP endpoints
```

gRPC and scheduler are runtime subsystems inside the backend process, not separate backend services at this stage.

---

## Direttore Modular Monolith Layout

All backend bounded contexts should live under:

```text
src/backend/context/
```

Current context map:

```text
src/backend/context/
  user/
  course/ (previosly "plan")
  schedule/
  graph/
  connectors/
  analytics/
  api_scheduler/
```

Supporting backend-level areas:

```text
src/backend/bootstrap/
src/backend/entrypoints/
src/backend/shared/
```

Recommended meaning:

```text
bootstrap/
  Wires the backend process together.
  Builds containers, Direttore app, settings, context registry.

entrypoints/
  Contains process-facing entrypoint code.
  FastAPI should be the primary entrypoint.
  gRPC and scheduler are initialized from the FastAPI lifecycle.

shared/
  Contains shared ports, tiny shared kernel types, and cross-context interfaces.
  It should not become a dumping ground for domain logic.
```

Important rule:

```text
container.py wires dependencies.
It should not become the implementation home for auth, tracing, API scheduler runtime, or other infrastructure.
```

If shared infrastructure is needed later, define it explicitly in dedicated modules and let the container connect it.

---

## Context: user

### Responsibility

The `user` context owns the basic business identity of a Planner user.

This context should be small, but it should still be explicit because many other contexts refer to the user. It is also the natural place to support future authentication and identity mapping.

### Owns

```text
business user id
user UUID
name
email
basic user record
external identity mappings later
auth-facing user lookup later
```

### Does not own

```text
behavioral analytics
productivity patterns
knowledge graph memory
Telegram chat state
agent session state
```

### Possible entities / models

```text
User
UserIdentity
ExternalIdentityMapping
UserEmail
UserStatus
```

### Possible tables

```text
users
user_identity_mappings
```

Possible `users` fields:

```text
id
public_id / uuid
display_name
email
status
created_at
updated_at
```

Possible `user_identity_mappings` fields:

```text
id
user_id
provider
provider_subject
created_at
updated_at
```

Examples of providers later:

```text
telegram
google
github
email
```

### Future design questions

```text
Should Telegram identity mapping live in backend user context or Telegram Gateway?
What is the difference between authentication identity and business user identity?
Do we need workspaces/accounts, or only users?
Will one user have multiple external identities?
```

---

## Context: course (previously "plan" - RENAMED to course)

### Responsibility

The `plan` context owns user goals and structured plans.

A plan is a meaningful activity program. It can represent a learning track, a project, a task decomposition, or another structured course of action.

Earlier project language used `course-maker` and `course`. In the current backend model, this becomes the `plan` context. The word `course` may remain as a domain concept inside plan if useful, but the bounded context name should stay broader.

### Owns

```text
goals
plans / courses
plan items
materials attached to plan items
dependencies between plan items
progress
user feedback on plan execution
plan lifecycle state
```

### Does not own

```text
calendar time slots
long-term knowledge graph
behavior analytics
external source synchronization
agent reasoning workflow
```

### Possible entities / models

```text
Plan
PlanItem
PlanMaterial
PlanDependency
PlanProgress
PlanFeedback
PlanStatus
PlanItemStatus
```

### Possible tables

```text
plans
plan_items
plan_item_dependencies
plan_materials
plan_progress_events
plan_feedback
```

Possible `plans` fields:

```text
id
user_id
title
description
goal_text
status
created_at
updated_at
completed_at
```

Possible `plan_items` fields:

```text
id
plan_id
parent_item_id
title
description
item_type
status
position
estimated_duration_minutes
created_at
updated_at
```

Possible `plan_materials` fields:

```text
id
plan_id
plan_item_id
source_type
source_ref
title
url
metadata_json
created_at
```

Possible `plan_feedback` fields:

```text
id
plan_id
plan_item_id
user_id
feedback_text
feedback_type
progress_value
metadata_json
created_at
```

### Domain examples

```text
Plan: "Learn Python"
  Item: "Read book 1"
  Item: "Read book 2"
  Item: "Watch video about FastAPI"
  Item: "Build small backend project"

User feedback:
  "I read 10 pages today."
  "This chapter was difficult."
  "I need more practice."
```

### Interaction with graph

When a plan item is completed or a plan accumulates meaningful feedback, the plan context may emit a semantic event or command for the graph context.

Example:

```text
PlanFeedbackCaptured
  -> graph may create/update knowledge cards later

PlanCompleted
  -> graph may aggregate important notes, ideas, and learned concepts
```

The plan context should not directly mutate graph internals.

### Future design questions

```text
Should "course" be a separate aggregate or just a subtype of Plan?
How should plan decomposition be represented: tree, DAG, ordered list, or mixed structure?
Should plan feedback be event-sourced or stored as normal records?
What part of plan creation is deterministic backend logic, and what part comes from Agent Server?
```

---

## Context: schedule

### Responsibility

The `schedule` context owns user time planning.

It transforms plans, deadlines, availability, and constraints into concrete user-facing schedule items.

This context is about what the user should do and when.

### Owns

```text
availability windows
busy/free slots
scheduled work blocks
deadlines
reminders
schedule versions
replanning state
missed or completed schedule items
```

### Does not own

```text
technical command execution scheduling
YouTube/email polling
external provider state
plan decomposition
knowledge graph memory
```

### Possible entities / models

```text
Schedule
ScheduleItem
AvailabilityWindow
Deadline
Reminder
ScheduleRevision
ScheduleFeedback
```

### Possible tables

```text
schedules
schedule_items
availability_windows
deadlines
reminders
schedule_revisions
schedule_feedback
```

Possible `schedule_items` fields:

```text
id
schedule_id
user_id
plan_id
plan_item_id
title
starts_at
ends_at
status
location_context
activity_type
created_at
updated_at
```

Possible `availability_windows` fields:

```text
id
user_id
starts_at
ends_at
allowed_activity_types
source
created_at
updated_at
```

Possible `reminders` fields:

```text
id
user_id
schedule_item_id
remind_at
channel
status
created_at
updated_at
```

### Domain examples

```text
11:00-13:00 read Python book
14:00-15:30 solve exercises
tomorrow 10:00 remind user about plan item
deadline: finish homework by Friday
```

### Interaction with API scheduler

The schedule context may request technical scheduled operations through a shared API scheduler port.

Example:

```text
schedule creates Reminder
  -> calls ApiSchedulerPort.schedule_operation(...)
  -> api_scheduler stores durable operation
  -> scheduler runtime later triggers command handler
```

The schedule context should not directly depend on APScheduler.

### Future design questions

```text
Should schedule be regenerated as full versions or updated incrementally?
How should missed tasks affect future schedule?
How much scheduling is algorithmic and how much should involve Agent Server?
How do we represent activity constraints: reading, coding, watching video, commuting, gym?
```

---

## Context: graph

### Responsibility

The `graph` context owns long-term semantic memory.

It stores not raw sources and not behavioral analytics, but meaningful knowledge: notes, cards, concepts, tags, and relationships.

### Owns

```text
knowledge cards
semantic notes
concept nodes
relations between concepts
tags
memory extraction results
links between knowledge and plans/materials
```

### Does not own

```text
raw external source storage
user productivity analytics
plan execution state
schedule slots
connector polling state
```

### Possible entities / models

```text
KnowledgeCard
KnowledgeNode
KnowledgeEdge
Note
Tag
MemoryCluster
SourceReference
```

### Possible tables

At first, this can be relational even if later moved to graph/vector storage.

```text
knowledge_cards
knowledge_nodes
knowledge_edges
knowledge_card_tags
notes
source_references
```

Possible `knowledge_cards` fields:

```text
id
user_id
title
summary
body
source_type
source_ref
created_from_plan_id
created_from_plan_item_id
created_at
updated_at
```

Possible `knowledge_edges` fields:

```text
id
user_id
from_node_id
to_node_id
relation_type
weight
created_at
updated_at
```

### Domain examples

```text
Card: "Unit of Work pattern"
Tags: Python, Architecture, DDD
Related to: Repository Pattern, Transaction Boundary
Created from: feedback on Architecture Patterns with Python
```

### Interaction with plan and analytics

The graph can consume meaningful signals from plan feedback, completed plans, notes, and user reflections.

It should not store every raw behavioral event. Those belong to analytics.

### Future design questions

```text
Do we start with Postgres tables and later add graph/vector storage?
What is a knowledge card versus a note versus a graph node?
How should Agent Server retrieve context from graph?
What operations should graph expose through backend gRPC?
```

---

## Context: connectors

### Responsibility

The `connectors` context owns user connections to external data sources and the state of data discovered through those connections.

This replaces the earlier split between `content-discovery` and `source-storage` for the first modular monolith version.

### Owns

```text
external source connections
YouTube channel subscriptions
email/Gmail watches
website/RSS/API watches
sync state
discovered external items
source metadata
notification candidates
```

### Does not own

```text
schedule slots
knowledge cards
behavior analytics
Telegram UX
LLM reasoning
```

### Possible entities / models

```text
ConnectorAccount
ConnectorSubscription
ExternalSource
ExternalItem
SyncCursor
SyncRun
DiscoveryRule
```

### Possible tables

```text
connector_accounts
connector_subscriptions
external_sources
external_items
sync_cursors
sync_runs
discovery_rules
```

Possible `connector_subscriptions` fields:

```text
id
user_id
connector_type
source_ref
title
status
polling_interval_seconds
last_checked_at
created_at
updated_at
```

Possible `external_items` fields:

```text
id
user_id
connector_type
source_id
external_id
title
url
published_at
status
metadata_json
created_at
updated_at
```

Possible connector types:

```text
youtube
email
website
rss
api
google_docs
```

### Domain examples

```text
User tracks YouTube channel X.
System checks for new videos.
New video is discovered and stored as ExternalItem.
Later it may become a material for a plan or a candidate notification.
```

### Interaction with API scheduler

Connectors should not own runtime scheduling. They should register periodic checks through the shared API scheduler port.

Example:

```text
User subscribes to YouTube channel
  -> connectors stores subscription
  -> connectors requests periodic check operation
  -> api_scheduler later triggers CheckYoutubeChannel command
```

### Future design questions

```text
Should source storage and content discovery be split later?
Should connector-specific code live as submodules inside connectors?
How do we deduplicate discovered items?
Which connector events should become notifications?
Which connector items should be eligible for graph extraction?
```

---

## Context: analytics

### Responsibility

The `analytics` context owns behavioral signals, personalization, user profile insights, and reflective summaries.

It is not the same as `user`. The user context owns identity; analytics owns learned behavioral/profile information.

### Owns

```text
behavior events
productivity signals
preference signals
profile facts
weekly reflection summaries
personalization data
task completion/miss patterns
```

### Does not own

```text
basic user identity
knowledge graph cards
raw external source items
schedule source of truth
plan source of truth
```

### Possible entities / models

```text
BehaviorEvent
UserProfileSignal
UserPreference
ReflectionSummary
ProductivityPattern
AnalyticsSnapshot
```

### Possible tables

```text
behavior_events
user_profile_signals
user_preferences
reflection_summaries
analytics_snapshots
```

Possible `behavior_events` fields:

```text
id
user_id
event_type
source_context
source_ref
payload_json
occurred_at
created_at
```

Possible `user_profile_signals` fields:

```text
id
user_id
signal_type
value_json
confidence
source_event_id
created_at
updated_at
```

Possible `reflection_summaries` fields:

```text
id
user_id
period_start
period_end
summary
insights_json
created_at
```

### Domain examples

```text
User often postpones coding tasks in the morning.
User completes reading tasks during commute.
User needs longer time blocks for math.
User prefers short videos in the evening.
```

### Interaction with other contexts

Analytics may consume events from:

```text
plan
schedule
connectors
graph
api_scheduler
```

It can provide personalization input to Agent Server or backend use cases.

### Future design questions

```text
Which events should be captured as analytics signals?
Which analytics updates are immediate and which are periodic?
Should weekly reflection be generated by Agent Server or backend workflow?
How should confidence and decay of profile signals work?
```

---

## Context: api_scheduler

### Responsibility

The `api_scheduler` context owns durable scheduled backend operations.

It is not the same as the `schedule` context.

```text
schedule = user-facing time plan
api_scheduler = technical backend operation execution plan
```

The API scheduler stores what backend command should be executed later or periodically.

### Owns

```text
scheduled operation records
operation identity
operation type
command handler key
payload
auth/context payload
tags
deduplication/cooldown state
last activation time
next run time
enabled/disabled state
```

### Does not own

```text
user schedule semantics
domain-specific reminder rules
YouTube domain model
analytics profile rules
actual command handler implementation
```

### Possible entities / models

```text
ScheduledOperation
ScheduledOperationRun
ScheduledOperationStatus
OperationTrigger
OperationTag
```

### Possible tables

```text
scheduled_operations
scheduled_operation_runs
```

Possible `scheduled_operations` fields:

```text
id
operation_key
operation_type
owner_type
user_id
command_handler_key
payload_json
auth_context_json
tags_json
schedule_kind
cron_expression
run_at
interval_seconds
last_activated_at
next_run_at
enabled
created_at
updated_at
```

Possible `scheduled_operation_runs` fields:

```text
id
operation_id
status
started_at
finished_at
error_message
result_json
triggered_by
created_at
```

### Domain examples

User-level operations:

```text
send reminder to user
check YouTube channel for new videos
check email for new messages
recalculate schedule for user
```

System-level operations:

```text
aggregate session feedback
refresh user profile signals
compact analytics events
rebuild graph clusters
```

### Runtime model

The runtime scheduler should keep only operation identifiers when possible.

When an operation fires:

```text
scheduler runtime receives operation_id
api_scheduler reads operation from database
api_scheduler checks enabled/dedup/cooldown/last_activated_at
api_scheduler resolves command_handler_key
Direttore executes the command with payload/auth context/tags
api_scheduler records run result
```

Important case:

```text
A system operation runs every 24 hours.
An admin manually triggered the same operation 1 hour ago.
The scheduled run should check last_activated_at and skip if appropriate.
```

### Shared port

Other contexts should not depend directly on APScheduler or runtime implementation.

They should use a shared port, for example:

```text
shared/ports/api_scheduler.py
```

Possible port operations:

```text
schedule_operation
cancel_operation
reschedule_operation
trigger_operation_now
disable_operation
```

### Future design questions

```text
How do we represent cron versus one-time versus interval operations?
How do we model deduplication and cooldown?
Should operation_type be system/user/integration/reminder?
How should auth context be validated before command execution?
Should operation runs be stored forever or compacted?
```

---

## Cross-Context Rules

### No direct ownership leaks

A context should not mutate another context's tables directly.

Correct:

```text
plan emits event or command for graph
schedule requests operation through API scheduler port
connectors stores external item and emits candidate event
analytics consumes behavior signals
```

Incorrect:

```text
plan writes graph tables directly
connectors writes schedule tables directly
schedule mutates analytics profile directly
agent imports backend repositories directly
```

### Shared is not a domain context

`shared/` may contain ports and small technical/kernel abstractions.

It should not own business state.

Good shared candidates:

```text
ClockPort
IdGeneratorPort
ApiSchedulerPort
TracingPort
AuthContext
CorrelationId
```

Bad shared candidates:

```text
Plan
Schedule
UserProfile
KnowledgeCard
ConnectorSubscription
```

### Context communication

Inside the backend modular monolith, contexts can communicate through Direttore command/query/event mechanisms and explicit ports.

The exact mechanics will be designed later, but the intended direction is:

```text
context command handlers
context query handlers
domain/application events
shared ports for cross-cutting capabilities
Direttore application wiring in bootstrap
```

---

## Current Recommended Backend Tree

Current minimal tree should stay small:

```text
services/backend/
  src/
    backend/
      __init__.py

      bootstrap/
        __init__.py
        container.py
        contexts.py
        direttore.py
        settings.py

      context/
        __init__.py
        user/
          __init__.py
        plan/
          __init__.py
        schedule/
          __init__.py
        graph/
          __init__.py
        connectors/
          __init__.py
        analytics/
          __init__.py
        api_scheduler/
          __init__.py
          README.md

      entrypoints/
        __init__.py

      shared/
        __init__.py
        ports/
          __init__.py
          api_scheduler.py
```

No need to create full `domain/`, `application/`, `adapters/` folders yet. Those should appear context-by-context when a real vertical slice is designed.

---

## First Implementation Direction

Recommended implementation order later:

```text
1. user
   Create minimal user record and user lookup.

2. api_scheduler
   Define ScheduledOperation and ApiSchedulerPort.

3. plan
   Create first Plan/PlanItem model and plan creation command.

4. schedule
   Create basic schedule item/reminder model.

5. connectors
   Add first connector subscription model, probably YouTube or email later.

6. graph
   Add minimal KnowledgeCard model.

7. analytics
   Add behavior event and profile signal models.
```

This order is not final, but it keeps the system grounded:

```text
user exists first
scheduler infrastructure exists early
plan/schedule are core product behavior
connectors/graph/analytics grow from real flows
```

---

## Open Decisions

```text
Should the user context own Telegram identity mapping, or should Telegram Gateway own it and backend only receive business user_id?

Should "course" remain a domain term inside plan, or should everything be called plan?

Should graph start with Postgres tables, or should graph/vector storage be introduced early?

Should API scheduler be implemented before reminders, or only when the first scheduled operation appears?

Should analytics store raw events, derived profile signals, or both from the beginning?

Should connectors and source storage remain one context for now, or split later?
```

---

## Current Conclusion

The backend domain currently consists of seven contexts:

```text
user
course
schedule
graph
connectors
analytics
api_scheduler
```

The backend should remain a modular monolith.

Each context owns its own domain language and durable state.

The first goal is not to over-design every context, but to keep the context boundaries explicit so that future domain work can proceed one vertical slice at a time.
