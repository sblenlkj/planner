# Analytics Domain

## Purpose

The `analytics` context owns long-lived user analytics used by the Planner agents.

It stores lightweight semantic memory about the user:

```text
What does the user struggle with?
What does the user prefer?
What patterns should agents keep in mind?
How should the agent communicate with the user?
Which productivity patterns affect planning?
```

The context is designed for agent-driven personalization. It does not model analytics as rigid `subject / predicate / value` triples. Instead, it stores natural-language records with metadata that helps filtering, ranking, lifecycle management, and later context assembly.

The main idea:

```text
Analytics is semantic user memory.
It stores observations and derived insights about the user.
```

---

## Context Boundary

### Owns

```text
analytics observations
analytics insights
analytics scopes
analytics record lifecycle
analytics confidence
analytics importance
analytics stability
analytics tags
analytics evidence text
```

### Does not own

```text
course tasks
course progress
course observations
schedule templates
generated schedule days
reminders
deadlines
knowledge graph relations
technical agent reasoning traces
chat message storage
application context DTO construction
embedding/vector storage implementation
```

If another context needs analytics information, it should use explicit application services, ports, queries, commands, or events. Other contexts must not mutate analytics tables directly.

---

## Domain Model

The analytics domain has two main domain entities:

```text
AnalyticsObservation
AnalyticsInsight
```

Both inherit shared behavior and shared fields from:

```text
AnalyticsRecord
```

`AnalyticsRecord` is not a separate persistent business entity. It is a shared base class used to avoid duplicating common fields and lifecycle behavior between observations and insights.

---

## AnalyticsRecord

`AnalyticsRecord` is a shared base entity for analytics records.

Fields:

```text
id
user_id
scope
description
evidence
confidence
importance
stability
status
tags
valid_until
```

Meaning:

```text
id            Domain UUID identifier.
user_id       Owner user UUID.
scope         High-level analytics area.
description   Natural-language user analytics record.
evidence      Optional short explanation of why the record exists.
confidence    How confident the system is that this record is true, 0.0..1.0.
importance    How important this record is for personalization/planning, 0.0..1.0.
stability     Whether the record is short-term or long-term.
status        Lifecycle state.
tags          Lightweight keyword/search tags.
valid_until   Optional time after which the record should no longer be considered valid.
```

Supported behavior:

```text
change_description
change_evidence
change_confidence
change_importance
change_scores
change_stability
replace_tags
change_valid_until
reject
expire
activate
is_active
```

Validation:

```text
id is UUID
user_id is UUID
scope is AnalyticsScope
description is required
evidence is optional
confidence is 0.0..1.0
importance is 0.0..1.0
stability is AnalyticsStability
status is AnalyticsRecordStatus
tags is tuple[str, ...]
valid_until is optional datetime
```

Text normalization:

```text
description is trimmed and must not be empty.
evidence is trimmed.
blank evidence becomes None.
```

Tag normalization:

```text
tags are trimmed
tags are lowercased
empty tags are removed
duplicate tags are removed
```

Important rule:

```text
AnalyticsRecord should not be used directly by application code as a business entity.
Use AnalyticsObservation or AnalyticsInsight.
```

---

## AnalyticsObservation

`AnalyticsObservation` is a single observed fact or signal about the user.

Fields:

```text
id
user_id
scope
description
evidence
confidence
importance
stability
status
tags
valid_until
source
source_id
observed_at
```

Meaning:

```text
source       Where the observation came from.
source_id    Optional external/source reference.
observed_at  When the observation was made.
```

Examples:

```text
scope: education
description: User struggles with derivatives and needs step-by-step explanations.
evidence: User said they do not understand derivatives.
confidence: 0.8
importance: 0.9
stability: short_term
tags: math, derivatives
```

```text
scope: communication
description: User prefers short direct answers without long introductions.
evidence: User repeatedly asked for shorter responses.
confidence: 0.85
importance: 0.9
stability: long_term
tags: short-answers, direct-style
```

Supported behavior:

```text
create
change_source
change_source_id
change_observed_at
change_valid_until
```

It also supports inherited behavior from `AnalyticsRecord`:

```text
change_description
change_evidence
change_confidence
change_importance
change_scores
change_stability
replace_tags
reject
expire
activate
is_active
```

Observation time rule:

```text
valid_until cannot be earlier than observed_at.
```

Source rule:

```text
source must be AnalyticsObservationSource.
source_id is optional.
```

Observation is not:

```text
course progress
task history
schedule day feedback
raw chat transcript
knowledge graph relation
```

Those records may be used as inputs for analytics, but they are not owned by analytics.

---

## AnalyticsInsight

`AnalyticsInsight` is a derived conclusion about the user.

It is usually built from one or more observations.

Fields:

```text
id
user_id
scope
description
evidence
confidence
importance
stability
status
tags
valid_until
source_observation_ids
derived_at
replaced_by
```

Meaning:

```text
source_observation_ids  Observation UUIDs used to derive the insight.
derived_at              When the insight was derived.
replaced_by             Optional UUID of the newer insight that supersedes this one.
```

Examples:

```text
scope: education
description: User has a recurring difficulty with derivatives and should review the topic through small practical examples.
evidence: Derived from multiple observations about derivative tasks and explanations.
confidence: 0.86
importance: 0.9
stability: short_term
tags: math, derivatives, step-by-step
```

```text
scope: productivity
description: User works better when large tasks are broken into small concrete steps.
evidence: Derived from repeated planning sessions.
confidence: 0.8
importance: 0.9
stability: long_term
tags: small-steps, planning
```

Supported behavior:

```text
create
replace_source_observations
add_source_observation
remove_source_observation
change_derived_at
change_valid_until
supersede_by
```

It also supports inherited behavior from `AnalyticsRecord`:

```text
change_description
change_evidence
change_confidence
change_importance
change_scores
change_stability
replace_tags
reject
expire
activate
is_active
```

Insight time rule:

```text
valid_until cannot be earlier than derived_at.
```

Replacement rules:

```text
Only active insights can be superseded.
An insight cannot supersede itself.
A superseded insight must have replaced_by.
Only superseded insights can have replaced_by.
```

Insight source rule:

```text
source_observation_ids is tuple[UUID, ...].
Duplicate observation ids are removed.
```

Important distinction:

```text
Observation means: this was noticed.
Insight means: this is a derived user-level conclusion.
```

---

## Analytics Scopes

`AnalyticsScope` is the high-level area used to filter analytics records.

Values:

```text
EDUCATION
FOOD
SPORT
PRODUCTIVITY
COMMUNICATION
```

Meaning:

```text
EDUCATION
  Learning, courses, skills, languages, topics, understanding, study behavior.

FOOD
  Food preferences, meal preferences, cooking patterns, dietary likes/dislikes.

SPORT
  Training, exercise, physical activity, sport goals, workout preferences.

PRODUCTIVITY
  Work/study rhythm, planning preferences, energy patterns, focus, procrastination.

COMMUNICATION
  How the agent should communicate with the user:
  tone, answer length, explanation style, amount of structure, directness.
```

Examples:

```text
education:
  User understands Python syntax but struggles with asyncio.

food:
  User does not like fish and prefers simple home food.

sport:
  User prefers short strength workouts over long cardio sessions.

productivity:
  User works better when tasks are split into small steps.

communication:
  User prefers concise direct answers and dislikes overly formal tone.
```

Scope is intentionally broad. The domain does not model narrow subject categories such as `python`, `italian`, `derivatives`, or `asyncio` as separate fields. Those details belong in:

```text
description
tags
future search/retrieval layer
```

---

## AnalyticsStability

`AnalyticsStability` describes how stable the analytics record is expected to be.

Values:

```text
SHORT_TERM
LONG_TERM
```

Meaning:

```text
SHORT_TERM
  Can change over weeks or months.
  Examples: current skill weakness, temporary productivity pattern, current learning difficulty.

LONG_TERM
  Looks like a stable preference or long-running pattern.
  Examples: communication style, food dislike, preferred learning format.
```

There is no ephemeral stability.

Short-lived current states such as:

```text
User is tired today.
User does not want complex tasks tonight.
User is busy right now.
```

should not become analytics records. They belong to current agent/session/planning context or schedule/day feedback, not long-lived analytics memory.

---

## AnalyticsRecordStatus

`AnalyticsRecordStatus` is the lifecycle status of an analytics record.

Values:

```text
ACTIVE
REJECTED
EXPIRED
SUPERSEDED
```

Meaning:

```text
ACTIVE
  The record is currently valid and can be used by application context assembly.

REJECTED
  The record was considered wrong or should not be used.

EXPIRED
  The record is no longer relevant.

SUPERSEDED
  The record was replaced by a newer record.
```

General lifecycle behavior:

```text
reject
  ACTIVE/REJECTED/EXPIRED records can become REJECTED.
  SUPERSEDED records cannot be rejected.

expire
  ACTIVE/REJECTED/EXPIRED records can become EXPIRED.
  SUPERSEDED records cannot be expired.

activate
  REJECTED/EXPIRED records can become ACTIVE.
  SUPERSEDED records cannot be activated.
```

Current usage rule:

```text
SUPERSEDED is primarily meaningful for AnalyticsInsight.
```

---

## AnalyticsObservationSource

`AnalyticsObservationSource` describes where an observation came from.

Values:

```text
USER_MESSAGE
AGENT_OBSERVATION
```

Meaning:

```text
USER_MESSAGE
  The user explicitly said or requested something that should be remembered.

AGENT_OBSERVATION
  The agent inferred or recorded an observation while helping the user.
```

Examples:

```text
USER_MESSAGE:
  User says: "Remember that I do not like fish."

AGENT_OBSERVATION:
  Agent notices that the user repeatedly asks for step-by-step Python explanations.
```

Most observations are expected to be `AGENT_OBSERVATION`.

---

## Description-First Design

Analytics deliberately does not use:

```text
subject
predicate
value
```

Instead, each observation or insight stores a natural-language `description`.

Rationale:

```text
The analytics context is consumed primarily by agents.
Agents benefit from compact semantic statements more than rigid tiny fields.
The system does not need to calculate averages over predicates or values.
Retrieval can later use scope, tags, embeddings, BM25, confidence, and importance.
```

Correct:

```text
description:
  User struggles with Python asyncio and needs explanations that start from event-loop basics.
```

Not needed:

```text
subject: python_asyncio
predicate: struggles_with
value: true
```

---

## Tags

Tags are lightweight keyword labels used for search/debug/retrieval.

Rules:

```text
tags are tuple[str, ...]
tags are normalized to lowercase
duplicates are removed
empty tags are removed
```

Tags are not:

```text
a domain ontology
a substitute for scope
a replacement for description
a guaranteed complete classification
```

Examples:

```text
python
asyncio
event-loop
math
derivatives
short-answers
fish
strength-training
```

---

## Confidence and Importance

Analytics uses two independent scores.

### Confidence

`confidence` means how likely the record is to be true.

Examples:

```text
0.2  weak guess
0.5  plausible but uncertain
0.8  strong signal
1.0  explicit or highly reliable
```

### Importance

`importance` means how useful the record is for future personalization/planning.

Examples:

```text
User dislikes fish:
  confidence may be high.
  importance depends on food planning context.

User works better with small steps:
  confidence may be medium/high.
  importance is often high for planning and agent behavior.
```

Validation:

```text
confidence is 0.0..1.0
importance is 0.0..1.0
```

---

## Evidence

`evidence` is optional short text explaining why a record exists.

Examples:

```text
User explicitly said this during onboarding.
Derived from three observations about missed morning study blocks.
Agent noticed repeated requests for shorter explanations.
```

Evidence is intentionally lightweight. The domain does not store full message bodies or agent traces.

If deeper traceability is needed, `source_id` for observations or `source_observation_ids` for insights can point to other records.

---

## Identity Rules

All analytics domain identifiers are UUIDs.

The field name is:

```text
id
```

Do not use:

```text
auto-increment database IDs
public_id/internal_id duplication by default
```

`id` means domain UUID identity.

Related IDs are also UUIDs:

```text
user_id
source_observation_ids
replaced_by
```

---

## Timestamp Rules

Do not add `created_at` / `updated_at` by default.

Timestamps are added only when they carry explicit domain meaning.

Current domain timestamps:

```text
observed_at
  When an observation was made.

derived_at
  When an insight was derived.

valid_until
  Optional domain validity boundary.
```

---

## Application Boundary Note

The domain only owns analytics entities and value objects.

The application layer may define:

```text
AnalyticsContextDto
```

This DTO can group domain entities for agent consumption, for example:

```text
insights
observations
```

The DTO is not part of the domain model. It is an application-level context assembly result.

Application services, repository ports, Unit of Work ports, retrieval logic, embeddings, BM25, and prompt/context formatting are outside this domain document.

---

## Persistence Shape

The domain model is not required to mirror database tables exactly, but the current natural table shape is:

## Observations

```text
analytics_observations
  id
  user_id
  scope
  description
  evidence
  confidence
  importance
  stability
  status
  tags
  valid_until
  source
  source_id
  observed_at
```

## Insights

```text
analytics_insights
  id
  user_id
  scope
  description
  evidence
  confidence
  importance
  stability
  status
  tags
  valid_until
  source_observation_ids
  derived_at
  replaced_by
```

---

## Current File Layout

Recommended current layout:

```text
src/backend/context/analytics/
  __init__.py

  domain/
    __init__.py

    entities/
      __init__.py
      analytics_record.py
      analytics_observation.py
      analytics_insight.py

    value_objects/
      __init__.py
      analytics_scope.py
      analytics_stability.py
      analytics_record_status.py
      analytics_observation_source.py
```

---

## Implementation Rules

Current implementation style:

```text
Pure dataclasses
kw_only=True
slots=True
UUID fields directly inside entities
No separate ID value objects
No separate description/evidence/score value objects
Validation directly in __post_init__
Validation directly in entity methods that mutate fields
```

For slotted dataclass inheritance, child entities should call the base post-init explicitly:

```text
AnalyticsRecord.__post_init__(self)
```

instead of:

```text
super().__post_init__()
```

This avoids runtime issues with slotted dataclass inheritance.

General text field rules:

```text
description is used for natural-language analytics content.
evidence is used only for optional supporting explanation.
Do not add title unless there is a strong domain reason.
```

Status/lifecycle rules:

```text
AnalyticsObservation supports ordinary lifecycle: active, rejected, expired.
AnalyticsInsight additionally supports supersede_by.
```

---

## Summary

The `analytics` domain stores long-lived semantic user memory for Planner agents.

It has two primary entities:

```text
AnalyticsObservation
  A concrete observed signal about the user.

AnalyticsInsight
  A derived conclusion built from observations.
```

Both share common fields and lifecycle through:

```text
AnalyticsRecord
```

The most important design choices are:

```text
Use description-first records instead of subject/predicate/value.
Keep scopes broad: education, food, sport, productivity, communication.
Use tags as lightweight search hints, not ontology.
Use confidence and importance as independent scores.
Use short-term/long-term stability only.
Do not store ephemeral current states in analytics.
Keep domain simple and application context assembly outside the domain.
