# Course Domain

## Purpose

The `course` context owns user courses and the domain state required to execute them.

A course is a long-lived user goal or learning/work track, for example:

```text
Learn Python
Learn Italian
Prepare for a backend developer role
Read architecture books
```

The context is designed for agent-driven planning. It does not keep a separate `CoursePlan` or `CoursePlanStep` model. Instead, the agent can shape execution through tasks, priorities, task ordering, progress, links, and observations.

---

## Context Boundary

### Owns

```text
courses
course tasks
course-level observations
task-level observations
task priority
task progress
task lifecycle
task ordering
course lifecycle
task links/resources
```

### Does not own

```text
calendar slots
reminders
technical scheduled operations
agent reasoning workflow
knowledge graph storage
analytics/profile signals
external connector sync state
```

If another context needs course information, it should use explicit queries, commands, events, or ports. Other contexts must not mutate course tables directly.

---

## Domain Model

### Course

`Course` is the aggregate root.

It represents the main user-owned course container.

Fields:

```text
id
user_id
title
description
status
```

Meaning:

```text
id          Domain UUID identifier.
user_id     Owner user UUID.
title       Short course name.
description Longer explanation of the course goal/context.
status      Course lifecycle state.
```

Examples:

```text
title: Learn Python
description: User wants to learn Python to become a backend developer.
```

Lifecycle actions:

```text
complete
archive
reactivate
rename
change_description
```

---

### CourseTask

`CourseTask` is an executable task inside a course.

Fields:

```text
id
course_id
title
description
priority
status
progress
next_task_id
links
```

Meaning:

```text
id            Domain UUID identifier.
course_id     Parent course UUID.
title         Short task name.
description   Longer task explanation.
priority      Task priority value object, 1..3.
status        Task lifecycle state.
progress      Task progress value object, 0..100.
next_task_id  Optional pointer to the task that should be done after this task.
links         Resource links attached to the task.
```

`next_task_id` is used to build simple task chains. The meaning is:

```text
After the current CourseTask is done, next_task_id points to the task that should follow.
```

This is intentionally not a full plan model. It is a lightweight linked-list style ordering mechanism.

Lifecycle/progress actions:

```text
start
skip
complete
reopen
change_progress
change_priority
set_next_task
add_link
remove_link
rename
change_description
```

---

### CourseObservation

`CourseObservation` is an agent-facing observation at course level.

Fields:

```text
id
course_id
title
description
```

Purpose:

Course observations store important context about the course that should be available to the agent later.

Examples:

```text
title: Backend motivation
description: User wants to learn Python because they want to become a backend developer.
```

```text
title: Data science motivation
description: User wants to learn Python because they want to work with data science tasks.
```

This is not analytics and not a knowledge graph card. It is local course context.

---

### CourseTaskObservation

`CourseTaskObservation` is a meaningful observation about a specific course task.

Fields:

```text
id
task_id
title
description
progress
```

Meaning:

```text
id          Domain UUID identifier.
task_id     Parent task UUID.
title       Short observation name.
description Detailed observation.
progress    Optional progress value associated with this observation.
```

Important rule:

`CourseTaskObservation` does not store `course_id`. The course is reachable through the parent task.

Examples of good task observations:

```text
Understood dependency injection
The book explains dependency injection through a service construction example in chapter 3.
```

```text
Found useful FastAPI pattern
The article shows how to separate routers, services, and repositories in a small backend.
```

Examples that should not be stored here:

```text
Read 20 pages
Need to repeat this later
This is difficult
```

`Read 20 pages` should usually change task progress. Difficulty/repetition signals may later belong to analytics, scheduling, or another domain signal model.

---

## Value Objects

### CourseStatus

Course lifecycle status.

Values:

```text
ACTIVE
COMPLETED
ARCHIVED
```

Managed through Direttore `StateMachine`.

Allowed transitions:

```text
ACTIVE -> COMPLETED
ACTIVE -> ARCHIVED
COMPLETED -> ACTIVE
COMPLETED -> ARCHIVED
ARCHIVED -> ACTIVE
```

---

### CourseTaskStatus

Task lifecycle status.

Values:

```text
PENDING
IN_PROGRESS
COMPLETED
SKIPPED
```

Managed through Direttore `StateMachine`.

Allowed transitions:

```text
PENDING -> IN_PROGRESS
PENDING -> COMPLETED
PENDING -> SKIPPED
IN_PROGRESS -> COMPLETED
IN_PROGRESS -> SKIPPED
COMPLETED -> IN_PROGRESS
SKIPPED -> PENDING
SKIPPED -> IN_PROGRESS
```

---

### CourseTaskPriority

Simple frozen value object.

Values:

```text
1 = low
2 = normal
3 = high
```

No Direttore `Validatable` is needed here. It is intentionally a small dataclass value object.

---

### CourseTaskProgress

Simple frozen value object.

Values:

```text
0..100
```

Meaning:

```text
0   Not started.
1..99 Partially done.
100 Completed.
```

No Direttore `Validatable` is needed here. It is intentionally a small dataclass value object.

---

### CourseTaskLink

Simple frozen value object stored inside `CourseTask.links`.

Fields:

```text
description
url
```

Meaning:

```text
description Required explanation of the resource.
url         Optional URL. Can be empty for offline/non-URL resources.
```

Examples:

```text
description: Official FastAPI tutorial
url: https://fastapi.tiangolo.com/tutorial/
```

```text
description: Physical book on my desk, chapter about dependency injection
url: None
```

`CourseTaskLink` is not an entity. It has no `id` and no `task_id`. It belongs to a task because it is inside `CourseTask.links`.

---

## Naming Rules

For domain text fields, use only:

```text
title
description
```

Use `title` for short human/agent-readable names.

Use `description` for longer explanations, context, or agent-facing details.

Avoid alternative text field names unless there is a strong domain reason:

```text
comment
note
notes
text
result
summary
body
```

This keeps domain entities consistent and makes agent context assembly easier.

---

## Identity Rules

All domain identifiers are UUIDs.

The field name is still:

```text
id
```

Do not use:

```text
auto-increment database IDs
public_id/internal_id duplication by default
```

`id` means domain UUID identity.

---

## Timestamp Rules

Do not add `created_at` / `updated_at` by default.

Timestamps are added only when they carry explicit domain meaning, for example scheduled operations, execution time, publication time, or domain events where time is part of the model.

---

## Direttore Usage

Use Direttore where it adds domain value:

```text
SimpleAggregateRoot for Course
StateMachine for CourseStatus and CourseTaskStatus
Validatable for entities with object-level invariants
```

Do not overuse Direttore for tiny value objects where a simple dataclass is enough.

Important validation rule:

If an entity inherits from `Validatable`, do not call `validate_invariants()` manually from factory methods such as `create()`. `Validatable` calls invariant validation automatically during object initialization. Explicit calls should be reserved for methods that mutate object-level invariants after creation.

For narrow field updates, prefer local validation before assignment instead of calling `validate_invariants()` everywhere.

---

## Proposed File Structure

```text
src/backend/context/course/
  __init__.py

  domain/
    __init__.py

    entities/
      __init__.py
      course.py
      course_task.py
      course_observation.py
      course_task_observation.py

    value_objects/
      __init__.py
      course_status.py
      course_task_status.py
      course_task_priority.py
      course_task_progress.py
      course_task_link.py
```

---

## Current First Slice

The first domain slice is intentionally small:

```text
Course
CourseTask
CourseObservation
CourseTaskObservation
CourseStatus
CourseTaskStatus
CourseTaskPriority
CourseTaskProgress
CourseTaskLink
```

Do not add these yet unless a real use case requires them:

```text
CoursePlan
CoursePlanStep
CourseMaterial
CourseDependency
CourseProgressEvent
ScheduleBinding
Deadline
Reminder
```

The current design is enough to represent a user course, executable tasks, lightweight task ordering, progress, resources, and agent-facing observations.
