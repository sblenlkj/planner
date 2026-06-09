# Graph Domain

## Purpose

The `graph` context owns the user's long-term personal knowledge graph used by Planner agents.

It stores compact knowledge structures such as:

```text
What has the user studied?
Which topics are connected to the user's learning history?
What knowledge fragments were extracted from completed course tasks?
What top-level knowledge areas does the user have?
Which fragments should be retrieved when the user asks about a topic?
```

The context is designed for agent-driven knowledge retrieval and consolidation.

The main idea:

```text
Graph is the user's personal knowledge library.
It stores knowledge nodes and knowledge fragments.
```

---

## Core Concept

The graph context does not store raw course observations.

Course observations are temporary records inside the `course` context. They are accumulated over time while the user is working on a course task.

When the course task is completed, the graph agent summarizes the completed course task and its observations into one or more `KnowledgeFragment` records.

Pipeline:

```text
CourseTask
  + CourseTaskObservation 1
  + CourseTaskObservation 2
  + CourseTaskObservation 3
  completed
        ↓
Graph agent summarizes completed course task
        ↓
KnowledgeFragment
        ↓
Attached to KnowledgeNode
```

A `KnowledgeFragment` is not a source reference. It is the final compact knowledge summary extracted from a completed course task.

The fragment must remain meaningful even if the original course task and course observations are later deleted.

---

## Context Boundary

### Owns

```text
knowledge nodes
knowledge fragments
knowledge node hierarchy
knowledge node lifecycle
knowledge fragment lifecycle
knowledge tags
knowledge fragment captured time
```

### Does not own

```text
courses
course tasks
course task observations
course task progress
source entity references
source snapshots
analytics observations
analytics insights
schedule blocks
reminders
deadlines
raw chat messages
agent reasoning traces
embeddings/vector storage implementation
retrieval ranking implementation
```

If another context needs graph information, it should use explicit application services, ports, queries, commands, or events. Other contexts must not mutate graph tables directly.

---

## Important Design Decisions

### No KnowledgeGraph entity

The current domain does not use a separate `KnowledgeGraph` aggregate.

The user's graph is represented by `KnowledgeNode` and `KnowledgeFragment` records scoped by `user_id`.

Top-level entry points are found by querying nodes where:

```text
parent_id is None
```

This keeps the domain small and avoids a redundant graph aggregate.

---

### User ID is stored directly

Both `KnowledgeNode` and `KnowledgeFragment` store `user_id` directly.

This is intentional.

A fragment is attached to a node through `node_id`, but the node hierarchy may later be rebuilt. During graph reconstruction, fragments still need to be selected by user without relying on the current node tree.

Rule:

```text
KnowledgeFragment must remain user-scoped even if its node attachment changes during graph rebuild.
```

---

### No origin_context / origin_id

The graph domain does not store fields such as:

```text
origin_context
origin_id
source_entity_id
course_task_id
```

The first ingestion source is currently a completed course task, but the graph domain does not keep a live reference to that source.

Reason:

```text
KnowledgeFragment is a self-contained summary, not a source reference.
```

This avoids coupling the graph context to the lifecycle of course tasks and reduces agent/application complexity.

---

### No source snapshots

The graph domain does not model `SourceSnapshot` as a value object.

The useful result of completed course task observations is the `KnowledgeFragment.content` itself.

Correct:

```text
KnowledgeFragment.content:
  User completed a Python course and especially liked the AsyncIO section. They became more comfortable with event loop basics, async/await syntax, and practical backend use cases. They also connected this topic with FastAPI and future backend projects.
```

Not needed:

```text
source_title
source_description
source_observations_summary
source_completed_at
```

Those details may be included naturally inside the fragment content when they matter.

---

## Domain Model

The graph domain has two main domain entities:

```text
KnowledgeNode
KnowledgeFragment
```

And three enum value objects:

```text
KnowledgeNodeType
KnowledgeNodeStatus
KnowledgeFragmentStatus
```

---

## KnowledgeNode

`KnowledgeNode` is a node in the user's personal knowledge tree.

It represents an aggregated topic, area, concept, skill, or resource.

Examples:

```text
Programming
Python
AsyncIO
FastAPI
Backend Development
Clean Architecture
Italian
Italian Grammar
```

Fields:

```text
id
user_id
parent_id
title
description
node_type
status
tags
```

Meaning:

```text
id            Domain UUID identifier.
user_id       Owner user UUID.
parent_id     Optional parent node UUID. None means top-level root node.
title         Required short node title.
description   Optional natural-language description of the aggregated knowledge node.
node_type     Broad semantic kind of node.
status        Lifecycle state.
tags          Lightweight keyword/search tags.
```

Examples:

```text
title: Programming
parent_id: None
node_type: area
description: High-level area for the user's programming and software development knowledge.
tags: programming, software
```

```text
title: AsyncIO
parent_id: <Python node id>
node_type: concept
description: User has accumulated knowledge about Python asynchronous programming, including event loop basics, async/await, and backend use cases.
tags: python, asyncio, event-loop, backend
```

Supported behavior:

```text
rename
change_description
change_type
move_to_parent
move_to_root
replace_tags
archive
activate
is_root
is_active
```

Validation:

```text
id is UUID
user_id is UUID
parent_id is optional UUID
title is required
node_type is KnowledgeNodeType
status is KnowledgeNodeStatus
tags is tuple[str, ...]
node cannot be its own parent
```

Text normalization:

```text
title is trimmed and must not be empty.
description is trimmed.
blank description becomes None.
```

Tag normalization:

```text
tags are trimmed
tags are lowercased
empty tags are removed
duplicate tags are removed
```

Root rule:

```text
parent_id is None means the node is a root/top-level node.
```

Tree rule:

```text
A KnowledgeNode can have zero or one parent.
The current version does not model many-to-many node relations.
```

---

## KnowledgeFragment

`KnowledgeFragment` is a compact, self-contained summary of user knowledge extracted from a completed course task and its accumulated observations.

It is attached to a `KnowledgeNode` and represents one meaningful contribution to that node.

Examples:

```text
A fragment attached to AsyncIO:
  User completed a long Python course and especially liked the AsyncIO section. They became more comfortable with event loop basics, async/await syntax, and practical backend use cases. They connected this topic with FastAPI and want to practice it in real projects.
```

```text
A fragment attached to Clean Architecture:
  User read parts of Clean Architecture and found the idea of use-case boundaries useful. They connected this to modular monolith design and backend context isolation.
```

Fields:

```text
id
user_id
node_id
title
content
status
tags
captured_at
```

Meaning:

```text
id            Domain UUID identifier.
user_id       Owner user UUID.
node_id       Knowledge node UUID this fragment is currently attached to.
title         Required short fragment title.
content       Required natural-language knowledge summary.
status        Lifecycle state.
tags          Lightweight keyword/search tags.
captured_at   When the fragment was captured into the graph domain.
```

Supported behavior:

```text
rename
change_content
move_to_node
replace_tags
change_captured_at
archive
activate
is_active
```

Validation:

```text
id is UUID
user_id is UUID
node_id is UUID
title is required
content is required
status is KnowledgeFragmentStatus
tags is tuple[str, ...]
captured_at is datetime
captured_at must be naive UTC datetime or aware UTC datetime
```

Text normalization:

```text
title is trimmed and must not be empty.
content is trimmed and must not be empty.
```

Tag normalization:

```text
tags are trimmed
tags are lowercased
empty tags are removed
duplicate tags are removed
```

Attachment rule:

```text
A KnowledgeFragment is attached to one KnowledgeNode through node_id.
```

User scope rule:

```text
KnowledgeFragment stores user_id directly, even though it is attached to a node.
This supports graph rebuilds where node attachments can change.
```

Independence rule:

```text
KnowledgeFragment is not a source reference.
It does not depend on the original CourseTask, CourseTaskObservation, or any other source entity remaining available.
```

---

## KnowledgeNodeType

`KnowledgeNodeType` describes the broad semantic kind of a knowledge node.

Values:

```text
AREA
TOPIC
CONCEPT
SKILL
RESOURCE
```

Meaning:

```text
AREA
  A broad top-level or organizational area.
  Examples: Programming, Books, Languages, Mathematics.

TOPIC
  A subject or subdomain.
  Examples: Python, Backend Development, Italian Grammar.

CONCEPT
  A specific concept inside a topic.
  Examples: AsyncIO, event loop, dependency injection.

SKILL
  A practical capability the user is learning or has practiced.
  Examples: building FastAPI endpoints, reading Italian texts, solving derivatives.

RESOURCE
  A knowledge object that is useful as a node itself.
  Examples: Clean Architecture, Designing Data-Intensive Applications.
```

Important rule:

```text
Not every course, video, article, or book must become a RESOURCE node.
A source becomes a node only when it is useful as a long-term object in the user's knowledge library.
Otherwise, its useful content should be summarized into KnowledgeFragment.content.
```

---

## KnowledgeNodeStatus

`KnowledgeNodeStatus` is the lifecycle status of a knowledge node.

Values:

```text
ACTIVE
ARCHIVED
```

Meaning:

```text
ACTIVE
  The node is currently valid and can be used by retrieval/context assembly.

ARCHIVED
  The node should not be used as an active knowledge entry, but is retained instead of being physically deleted.
```

Supported lifecycle behavior:

```text
archive
activate
is_active
```

---

## KnowledgeFragmentStatus

`KnowledgeFragmentStatus` is the lifecycle status of a knowledge fragment.

Values:

```text
ACTIVE
ARCHIVED
```

Meaning:

```text
ACTIVE
  The fragment is currently valid and can be used by retrieval/context assembly.

ARCHIVED
  The fragment should not be used as an active knowledge contribution, but is retained instead of being physically deleted.
```

Supported lifecycle behavior:

```text
archive
activate
is_active
```

---

## Ingestion from Course Context

In the current version, graph knowledge is created only from completed course tasks.

The graph context does not process raw user messages directly.

The graph context does not process active course tasks directly.

The graph context does not receive arbitrary manual knowledge writes in the first version.

Current ingestion rule:

```text
Only completed CourseTask records with accumulated observations can be converted into graph knowledge.
```

Expected flow:

```text
Course context publishes completed course task information
        ↓
Application layer asks graph agent to interpret it
        ↓
Graph agent finds or creates relevant KnowledgeNode records
        ↓
Graph agent creates one or more KnowledgeFragment records
        ↓
Fragments are attached to relevant nodes
```

A single completed course task may create multiple knowledge fragments.

Example:

```text
Completed course task:
  70-hour Python course

Observations:
  User liked AsyncIO.
  User liked FastAPI.
  User understood type hints better.

Possible graph result:
  KnowledgeFragment attached to AsyncIO
  KnowledgeFragment attached to FastAPI
  KnowledgeFragment attached to Type Hints
```

The graph domain itself does not need to store the course task ID to support this.

---

## Retrieval Model

The basic retrieval model is tree-oriented.

Top-level nodes:

```text
select KnowledgeNode where user_id = :user_id and parent_id is None and status = active
```

Topic subtree:

```text
select child KnowledgeNode records under a selected parent node
```

Fragments for a node:

```text
select KnowledgeFragment where user_id = :user_id and node_id = :node_id and status = active
```

The graph domain does not own vector search, embeddings, BM25, ranking, or prompt assembly.

Those belong to the application/infrastructure/retrieval layer.

---

## Distinction from Analytics

The graph context and analytics context store different kinds of memory.

Graph:

```text
User studied AsyncIO from completed learning work.
User has knowledge fragments about Python, FastAPI, and event loop basics.
```

Analytics:

```text
User struggles with abstract explanations.
User prefers short direct answers.
User learns better through practical examples.
```

Rule:

```text
Graph stores the user's knowledge library.
Analytics stores semantic user memory about preferences, struggles, patterns, and personalization.
```

Do not store graph relations in analytics.
Do not store user communication/productivity preferences in graph.

---

## Identity Rules

All graph domain identifiers are UUIDs.

The field name is:

```text
id
```

Do not use:

```text
auto-increment database IDs
public_id/internal_id duplication by default
```

Related IDs are also UUIDs:

```text
user_id
parent_id
node_id
```

---

## Timestamp Rules

Do not add `created_at` / `updated_at` by default.

Timestamps are added only when they carry explicit domain meaning.

Current domain timestamp:

```text
captured_at
  When a KnowledgeFragment was captured into the graph domain.
```

`captured_at` accepts naive UTC datetime or aware UTC datetime.

---

## Application Boundary Note

The domain only owns graph entities and value objects.

The application layer may define DTOs such as:

```text
GraphContextDto
KnowledgeNodeDto
KnowledgeFragmentDto
```

These DTOs can group graph records for agent consumption, for example:

```text
root_nodes
selected_nodes
fragments
```

The DTOs are not part of the domain model.

Application services, repository ports, Unit of Work ports, graph ingestion orchestration, retrieval logic, embeddings, BM25, and prompt/context formatting are outside this domain document.

---

## Persistence Shape

The domain model is not required to mirror database tables exactly, but the current natural table shape is:

## Nodes

```text
knowledge_nodes
  id
  user_id
  parent_id
  title
  description
  node_type
  status
  tags
```

## Fragments

```text
knowledge_fragments
  id
  user_id
  node_id
  title
  content
  status
  tags
  captured_at
```

---

## Current File Layout

Recommended current layout:

```text
src/backend/context/graph/
  __init__.py

  domain/
    __init__.py
    graph_domain.md

    entities/
      __init__.py
      knowledge_node.py
      knowledge_fragment.py

    value_objects/
      __init__.py
      knowledge_node_type.py
      knowledge_node_status.py
      knowledge_fragment_status.py
```

Recommended unit test layout:

```text
tests/unit/context/graph/domain/
  entities/
    test_knowledge_node.py
    test_knowledge_fragment.py

  value_objects/
    test_graph_value_objects.py
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
No separate title/content/tag value objects
Validation directly in __post_init__
Validation directly in entity methods that mutate fields
```

General text field rules:

```text
title is used for compact human-readable labels.
description is used for optional node-level summary.
content is used for full fragment summary.
```

Status/lifecycle rules:

```text
KnowledgeNode supports active/archived lifecycle.
KnowledgeFragment supports active/archived lifecycle.
Archived records are retained but should not be used by active retrieval/context assembly.
```

---

## Summary

The `graph` domain stores the user's personal knowledge library.

It has two primary entities:

```text
KnowledgeNode
  A node in the user's knowledge tree.

KnowledgeFragment
  A compact summary extracted from completed course task observations and attached to a node.
```

The most important design choices are:

```text
Do not create a separate KnowledgeGraph entity.
Use user_id directly on nodes and fragments.
Use parent_id=None to identify root nodes.
Use KnowledgeFragment as the final summarized knowledge object.
Do not store source snapshots.
Do not store origin_context or origin_id.
Do not couple fragments to the lifecycle of course tasks.
Keep graph simple: tree nodes plus attached fragments.
```
