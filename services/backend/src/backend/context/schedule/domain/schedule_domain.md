# Schedule Domain

## Purpose

The `schedule` context owns user-facing time planning in the Planner backend.

It answers questions such as:

```text
What does the user's ordinary week look like?
What should the user do on a concrete date?
Which future date-specific notes should affect planning?
Which reminders and deadlines should the system keep in mind?
```

The context is not a technical scheduler. Technical delayed/periodic execution belongs to the backend API scheduler/runtime layer. The `schedule` context may request technical operations through a port, but it does not own APScheduler/runtime implementation details.

The context is also not the `course` context. Schedule may reference course tasks by UUID, but it does not own course progress, course task lifecycle, course observations, or course materials.

---

## Internal Subcontexts

The `schedule` context is split into three internal domain subcontexts:

```text
schedule/domain/template
schedule/domain/execution
schedule/domain/commitment
```

Their responsibilities are:

```text
template
  The user's ordinary repeating weekly time model.

execution
  Concrete generated days, day snapshots, planned activities, and day observations.

commitment
  Time commitments that must be remembered or considered: reminders and deadlines.
```

This is not a split into separate bounded contexts. All three live inside one `schedule` bounded context because they share the same language of user time planning.

---

## Shared Domain Types

Shared schedule types live under:

```text
schedule/domain/shared
```

They are small value objects/enums used by multiple schedule subcontexts.

### LocalTime

```text
LocalTime
  hour: int
  minute: int
```

Meaning:

```text
Abstract local time inside a user's day.
It does not contain timezone information.
```

Examples:

```text
09:00
13:30
22:15
```

Validation:

```text
hour is 0..23
minute is 0..59
```

Timezone handling rule:

```text
Weekly templates and generated day time ranges use abstract local day time.
User timezone is stored in the user context and is applied by application services when needed.
```

---

### LocalTimeRange

```text
LocalTimeRange
  start_time: LocalTime
  end_time: LocalTime
```

Meaning:

```text
A range inside one local day.
```

Validation:

```text
start_time < end_time
```

Supported behavior:

```text
overlaps(other)
```

---

### ScheduleDate

```text
ScheduleDate
  year: int
  month: int
  day: int
```

Meaning:

```text
A concrete calendar date in the user's planning model.
```

It is used for generated days and date-specific observations.

---

### TimeBlockKind

```text
TimeBlockKind
  FREE
  BUSY
  SLEEP
  LIMITED
  BLOCKED
```

Meaning:

```text
FREE
  User is available for ordinary planning.

BUSY
  User is occupied. The concrete meaning is described by title/description.

SLEEP
  User is sleeping. This is a strong non-planning state.

LIMITED
  User has limited availability, for example commuting or waiting.

BLOCKED
  Time should not be used for planning and user should generally not be disturbed.
```

Important rule:

```text
There is no TimeBlockSubtype.
```

Earlier WORK/STUDY/ERRANDS-like subtypes were removed. The current model keeps `TimeBlockKind` small and algorithmic. The concrete meaning of a busy block belongs in:

```text
title
description
```

Example:

```text
kind: BUSY
title: Work
description: User is at work.
```

---

# Subcontext: Template

## Purpose

The `template` subcontext describes the user's ordinary repeating week.

It does not contain concrete dates. It does not contain generated activities. It does not represent what happened today. It is the baseline weekly model from which concrete days may later be generated.

Path:

```text
schedule/domain/template
```

## Entities

```text
WeeklyScheduleTemplate
ScheduleDayTemplate
TimeBlock
DayMarker
WeeklyScheduleObservation
```

## Value Objects / Enums

```text
Weekday
DayMarkerKind
```

It also uses shared types:

```text
LocalTime
LocalTimeRange
TimeBlockKind
```

---

## WeeklyScheduleTemplate

Aggregate root for a user's ordinary weekly schedule template.

```text
WeeklyScheduleTemplate
  id: UUID
  user_id: UUID
  days: list[ScheduleDayTemplate]
  observations: list[WeeklyScheduleObservation]
```

Meaning:

```text
A stable weekly structure of the user's ordinary life.
```

At the current product stage, each user is expected to have one active weekly template. The model still has its own UUID and child references by `weekly_schedule_template_id`, so the architecture can later support multiple templates per user without changing the core entity shape.

Identity:

```text
id
```

Invariants:

```text
belongs to one user_id
has exactly 7 ScheduleDayTemplate children
has one ScheduleDayTemplate per Weekday
all child days reference WeeklyScheduleTemplate.id
all weekly observations reference WeeklyScheduleTemplate.id
```

Supported behavior:

```text
create_empty(user_id)
get_day(weekday)
replace_day(day)
add_observation(observation)
remove_observation(observation_id)
```

---

## ScheduleDayTemplate

Entity for one weekday inside a weekly template.

```text
ScheduleDayTemplate
  weekly_schedule_template_id: UUID
  weekday: Weekday
  time_blocks: list[TimeBlock]
  markers: list[DayMarker]
```

Identity:

```text
weekly_schedule_template_id + weekday
```

No separate UUID is needed for this entity. Inside one weekly template there can be exactly one Monday, one Tuesday, and so on.

Meaning:

```text
The ordinary structure of one weekday.
```

Collections:

```text
time_blocks
  Hard or semi-hard time-state blocks: sleep, free time, busy time, limited time, blocked time.

markers
  Soft preferred windows: meal, exercise, family, personal, custom.
```

Invariants:

```text
weekday is required
time_blocks inside one day template must not overlap
markers may overlap with time_blocks
markers may overlap with other markers
```

Supported behavior:

```text
add_time_block(block)
remove_time_block(block_id)
replace_time_blocks(blocks)
add_marker(marker)
remove_marker(marker_id)
replace_markers(markers)
```

---

## TimeBlock

Repeating weekly time-state block inside a day template.

```text
TimeBlock
  id: UUID
  start_time: LocalTime
  end_time: LocalTime
  kind: TimeBlockKind
  title: str
  description: str | None
```

Meaning:

```text
A time-state block in the ordinary weekly template.
```

Examples:

```text
00:00-07:30 SLEEP / Sleep
08:00-19:00 BUSY / Work
20:00-23:00 FREE / Evening free time
19:00-20:00 LIMITED / Commute
```

Important distinction:

```text
TimeBlock describes the state of time.
It does not describe a concrete planned action.
```

Concrete planned actions belong to `ScheduledActivity` in the execution subcontext.

Validation:

```text
start_time < end_time
kind is TimeBlockKind
title is required
description is optional
```

Supported behavior:

```text
time_range
overlaps(other)
rename(title)
change_description(description)
reschedule(start_time, end_time)
```

---

## DayMarker

Soft preferred weekly marker inside a day template.

```text
DayMarker
  id: UUID
  preferred_start_time: LocalTime
  preferred_end_time: LocalTime
  kind: DayMarkerKind
  title: str
  description: str | None
```

Meaning:

```text
A preferred or habitual activity window, not a hard time-state block.
```

Examples:

```text
MEAL / Lunch
EXERCISE / Gym
FAMILY / Family time
PERSONAL / Reading or reflection
CUSTOM / Any custom soft preference
```

Important distinction:

```text
DayMarker is not TimeBlock.
```

A meal marker does not mean the user is already free or blocked. It means the planner should consider the user's preference to eat around that time. The planner may later decide how to fit this into the actual day.

Overlap rule:

```text
DayMarker may overlap with TimeBlock.
DayMarker may overlap with other DayMarker entities.
```

This is intentional. A user may want lunch during work, exercise near office time, or family time around a busy evening. Whether that is realistic is planner reasoning, not a structural invariant.

Validation:

```text
preferred_start_time < preferred_end_time
kind is DayMarkerKind
title is required
description is optional
```

Supported behavior:

```text
preferred_range
rename(title)
change_description(description)
reschedule(preferred_start_time, preferred_end_time)
```

---

## WeeklyScheduleObservation

Stable narrative context attached to the whole weekly template.

```text
WeeklyScheduleObservation
  id: UUID
  weekly_schedule_template_id: UUID
  description: str
```

Meaning:

```text
Long-lived context that helps the planner interpret the user's ordinary week.
```

It is intentionally text-only. It is not a marker, not a block, not a structured constraint, and not a rule engine.

Examples of meaning:

```text
The user's gym is near work.
The user usually eats breakfast in a cafe.
The user prefers to cook breakfast at home.
The user's commute can be used for reading.
```

The model keeps only `description`. A separate `title` would usually duplicate the same idea and make agent-facing context noisier.

Validation:

```text
description is required
```

Supported behavior:

```text
change_description(description)
```

---

## Weekday

```text
Weekday
  MONDAY
  TUESDAY
  WEDNESDAY
  THURSDAY
  FRIDAY
  SATURDAY
  SUNDAY
```

Supported helper:

```text
all()
```

---

## DayMarkerKind

```text
DayMarkerKind
  MEAL
  EXERCISE
  FAMILY
  PERSONAL
  CUSTOM
```

Meaning:

```text
A soft marker type for preferred/habitual day activities.
```

---

# Subcontext: Execution

## Purpose

The `execution` subcontext represents concrete generated days and date-specific planning context.

It is not the weekly template. It is what the system creates for an actual date, usually by expanding the weekly template and considering commitments, date observations, course tasks, and recent user context.

Path:

```text
schedule/domain/execution
```

## Planning Strategy

The current preferred strategy is day-by-day generation:

```text
During the user's sleep, an async agent generates the next day's ScheduleDay.
```

Rationale:

```text
Planning too far ahead creates unnecessary re-planning.
If the user misses today's plan, future generated days may become wrong.
Future observations and commitments can wait until their date becomes relevant.
Day-by-day generation is cheaper and easier to adapt.
```

Future notes can exist long before the concrete day exists. When the target date is near, the generator reads the relevant future observations and commitments and creates a `ScheduleDay`.

## Entities

```text
ScheduleDay
ScheduledBlock
ScheduledActivity
ScheduleDayObservation
ScheduleDateObservation
```

## Value Objects / Enums

Execution uses shared types:

```text
ScheduleDate
LocalTime
LocalTimeRange
TimeBlockKind
```

---

## ScheduleDay

Aggregate root for one concrete generated user day.

```text
ScheduleDay
  user_id: UUID
  date: ScheduleDate
  title: str
  description: str
  blocks: list[ScheduledBlock]
  activities: list[ScheduledActivity]
  observations: list[ScheduleDayObservation]
```

Identity:

```text
user_id + date
```

No standalone UUID is required for `ScheduleDay`.

Meaning:

```text
A generated plan for one user on one concrete date.
```

The aggregate contains three main collections:

```text
blocks
  Snapshot of the user's day structure copied from template/planning inputs.

activities
  Concrete planned actions for the day.

observations
  Day-local narrative facts about what actually happened.
```

The fields `title` and `description` have different meanings:

```text
title
  Short generated theme of the day.
  Example meaning: Today is focused on Python.

description
  More detailed generated narrative of the intended day plan.
  It summarizes the plan so future agents do not need the entire detailed structure.
```

Important rule:

```text
ScheduleDay does not reference WeeklyScheduleTemplate after generation.
```

The template is an input used to produce the day. The generated day must remain stable even if the template changes later.

Invariants:

```text
title is required
description is required
activities inside one ScheduleDay must not overlap
all ScheduleDayObservation children must belong to the same user_id + date
```

Note:

```text
ScheduledBlock overlap is not currently validated by ScheduleDay.
The template already prevents overlapping TimeBlock instances, and execution stores blocks as snapshots.
```

Supported behavior:

```text
identity
add_block(block)
remove_block(block_id)
replace_blocks(blocks)
add_activity(activity)
remove_activity(activity_id)
replace_activities(activities)
add_observation(observation)
remove_observation(observation_id)
rename(title)
change_description(description)
```

---

## ScheduledBlock

Snapshot of a user's concrete day time context.

```text
ScheduledBlock
  id: UUID
  start_time: LocalTime
  end_time: LocalTime
  kind: TimeBlockKind
  title: str
  description: str | None
```

Meaning:

```text
A copied time-state block inside a concrete generated day.
```

Usually, `ScheduledBlock` is produced by expanding template `TimeBlock` into a concrete `ScheduleDay`.

Important rule:

```text
ScheduledBlock is a snapshot.
```

If the weekly template changes later, already generated days keep their copied blocks.

This prevents old generated days from changing meaning retroactively.

Validation:

```text
start_time < end_time
kind is TimeBlockKind
title is required
description is optional
```

Supported behavior:

```text
time_range
overlaps(other)
rename(title)
change_description(description)
reschedule(start_time, end_time)
```

---

## ScheduledActivity

Concrete planned user action inside a generated day.

```text
ScheduledActivity
  id: UUID
  start_time: LocalTime
  end_time: LocalTime
  title: str
  description: str | None
  course_task_id: UUID | None
```

Meaning:

```text
Something the user is expected to do on a concrete generated day.
```

Examples of meaning:

```text
Read a Python chapter.
Cook breakfast.
Prepare food.
Exercise.
Review course material.
Meditate.
```

Optional course link:

```text
course_task_id
  If present, the activity is connected to a CourseTask.
  If absent, the activity is standalone and not course-owned.
```

Important rules:

```text
ScheduledActivity is not a task tracker.
It has no status.
It has no source field.
It has no generic binding object.
```

Why no status:

```text
The system should not force the agent to update every activity as completed/skipped/missed.
```

If the user reports course progress, that should go to the course context.
If the user reports behavioral/day feedback, that should become ScheduleDayObservation or analytics input.

Validation:

```text
start_time < end_time
title is required
description is optional
course_task_id is optional
```

Supported behavior:

```text
time_range
overlaps(other)
rename(title)
change_description(description)
reschedule(start_time, end_time)
link_course_task(course_task_id)
unlink_course_task()
```

---

## ScheduleDayObservation

Day-local narrative observation about what actually happened.

```text
ScheduleDayObservation
  id: UUID
  user_id: UUID
  date: ScheduleDate
  description: str
```

Meaning:

```text
A short narrative fact or feedback record about a concrete generated day.
```

This is different from `ScheduleDay.description`:

```text
ScheduleDay.description
  What the system intended the day to be.

ScheduleDayObservation.description
  What the user later said actually happened.
```

The model keeps only `description`. A separate title would usually duplicate the same idea and make the observation noisy.

Examples of meaning:

```text
User did not manage to do anything in the morning.
User overslept in the evening.
User spent five hours unexpectedly and missed the plan.
User completed the main morning focus but skipped evening reading.
```

Validation:

```text
user_id is required
date is required
description is required
```

Supported behavior:

```text
change_description(description)
```

---

## ScheduleDateObservation

Future or date-specific schedule context.

```text
ScheduleDateObservation
  id: UUID
  user_id: UUID
  starts_on: ScheduleDate
  ends_on: ScheduleDate | None
  description: str
```

Meaning:

```text
Concrete-date or date-range context that should affect future day generation.
```

It can exist before a `ScheduleDay` has been generated.

Examples of meaning:

```text
In two weeks the user wants to go to the cinema.
Tomorrow the user wants to read more Python.
Next Friday morning the user will be away.
In a year the user plans to go to the dacha around noon.
```

Important distinction:

```text
ScheduleDateObservation
  Future/date-specific context before generation.

ScheduleDay.description
  Generated plan narrative for an already generated day.

ScheduleDayObservation
  Actual day feedback after or during the day.
```

Range semantics:

```text
starts_on is required.
ends_on is optional.
If ends_on is absent, the observation applies only to starts_on.
If ends_on is present, the observation applies to the inclusive date range.
```

Validation:

```text
starts_on is required
ends_on cannot be earlier than starts_on
description is required
```

Supported behavior:

```text
applies_to(date)
change_description(description)
```

---

# Subcontext: Commitment

## Purpose

The `commitment` subcontext stores small time commitments that are not weekly templates and are not generated day activities.

Path:

```text
schedule/domain/commitment
```

It contains:

```text
Reminder
Deadline
```

Both represent time-related obligations that may be considered by the planner or technical scheduler.

`Reminder` is about notifying the user at a time.

`Deadline` is about something that must be completed before a time.

## Entities

```text
Reminder
Deadline
```

## Value Objects / Enums

```text
CommitmentStatus
```

---

## CommitmentStatus

```text
CommitmentStatus
  ACTIVE
  CANCELLED
```

Meaning:

```text
ACTIVE
  The commitment is still relevant and should be considered.

CANCELLED
  The commitment is no longer relevant and should not be considered.
```

`CANCELLED` is intentionally broad. It may mean cancelled, completed, closed, or no longer relevant.

The model deliberately does not distinguish:

```text
completed
missed
expired
archived
```

Those states would turn commitments into a task/progress tracker, which is not needed in the first slice.

---

## Reminder

User-facing reminder.

```text
Reminder
  id: UUID
  user_id: UUID
  remind_at: datetime
  title: str
  description: str | None
  status: CommitmentStatus
```

Meaning:

```text
A request to remind the user at a concrete time.
```

Examples of meaning:

```text
Remind me today at 18:00 to call my friend.
Remind me tomorrow morning to bring documents.
```

Time rule:

```text
remind_at is stored as UTC.
```

Validation accepts:

```text
naive datetime
  Treated as UTC by convention.

aware UTC datetime
  Accepted.

aware non-UTC datetime
  Rejected.
```

Why:

```text
User timezone is stored in the user context.
Application services convert user local intent into UTC before creating Reminder.
The domain entity protects the storage invariant and does not perform timezone conversion.
```

Validation:

```text
remind_at must be datetime
remind_at must be UTC or naive UTC
title is required
description is optional
status is CommitmentStatus
```

Supported behavior:

```text
cancel()
reactivate()
reschedule(remind_at)
rename(title)
change_description(description)
```

Interaction with technical scheduler:

```text
Reminder itself is domain state.
The application layer may request a technical scheduled operation through ApiSchedulerPort.
```

---

## Deadline

User-facing deadline.

```text
Deadline
  id: UUID
  user_id: UUID
  due_at: datetime
  title: str
  description: str | None
  course_id: UUID | None
  course_task_id: UUID | None
  status: CommitmentStatus
```

Meaning:

```text
A time constraint saying that something should be done before a concrete time.
```

Examples of meaning:

```text
Homework is due on March 27.
Project submission must be completed by Friday.
A course-related task should be finished before a date.
```

Why Deadline belongs to schedule:

```text
A deadline is primarily a time constraint, not course content.
```

It may reference a course or course task, but it can also exist without any course connection.

Optional course relation:

```text
course_id
  Optional course reference.

course_task_id
  Optional task reference.
  If course_task_id is set, course_id must also be set.
```

Time rule:

```text
due_at is stored as UTC.
```

Validation accepts:

```text
naive datetime
  Treated as UTC by convention.

aware UTC datetime
  Accepted.

aware non-UTC datetime
  Rejected.
```

Validation:

```text
due_at must be datetime
due_at must be UTC or naive UTC
title is required
description is optional
status is CommitmentStatus
course_id is required when course_task_id is set
```

Supported behavior:

```text
cancel()
reactivate()
reschedule(due_at)
link_course_task(course_id, course_task_id)
unlink_course_task()
rename(title)
change_description(description)
```

How deadline affects planning:

```text
Deadline is input to day generation.
It is not itself a ScheduledActivity.
```

Example flow:

```text
Deadline exists: homework due March 27.
The planner generates activities on previous days to work toward that deadline.
```

---

# Cross-Subcontext Rules

## Template to Execution

The template is input to execution generation.

```text
WeeklyScheduleTemplate
  -> generate concrete ScheduleDay
```

But after generation:

```text
ScheduleDay does not depend on WeeklyScheduleTemplate.
```

Template `TimeBlock` instances are copied into execution as `ScheduledBlock` snapshots.

This protects generated days from later template changes.

---

## Execution and Course

Execution may reference course tasks:

```text
ScheduledActivity.course_task_id: UUID | None
```

But schedule does not own course tasks.

Correct:

```text
ScheduledActivity references course_task_id.
Application service may later send command/event to course if user reports progress.
```

Incorrect:

```text
Schedule directly mutates course task status/progress.
```

---

## Commitment and Course

Deadline may optionally reference course:

```text
Deadline.course_id
Deadline.course_task_id
```

But deadline remains schedule-owned because it is a time constraint.

A homework deadline can exist without a course. A course-related deadline can reference course/task IDs without becoming course-owned.

---

## Reminder and Technical Scheduling

Reminder is user-facing domain state.

Technical execution belongs elsewhere.

Expected application flow:

```text
1. User asks for a reminder.
2. schedule/commitment creates Reminder.
3. Application service asks ApiSchedulerPort to schedule a technical operation.
4. Technical scheduler later triggers delivery.
```

The `schedule` domain model does not depend on APScheduler or any runtime scheduler.

---

## Observations

There are three observation concepts, each with a different temporal scope:

```text
WeeklyScheduleObservation
  Stable context for the ordinary weekly template.

ScheduleDateObservation
  Future/date-specific context before day generation.

ScheduleDayObservation
  Actual narrative feedback about a generated day.
```

They are intentionally text-first and lightweight.

They do not replace:

```text
course progress
analytics profile signals
knowledge graph memory
```

Application services may later route meaningful information to those contexts.

---

# Persistence Shape

The domain model is not required to mirror database tables exactly, but the current natural table shape is:

## Template

```text
weekly_schedule_templates
  id
  user_id
```

```text
schedule_day_templates
  weekly_schedule_template_id
  weekday

PK:
  weekly_schedule_template_id + weekday
```

```text
time_blocks
  id
  weekly_schedule_template_id
  weekday
  start_time
  end_time
  kind
  title
  description
```

```text
day_markers
  id
  weekly_schedule_template_id
  weekday
  preferred_start_time
  preferred_end_time
  kind
  title
  description
```

```text
weekly_schedule_observations
  id
  weekly_schedule_template_id
  description
```

## Execution

```text
schedule_days
  user_id
  date
  title
  description

PK:
  user_id + date
```

```text
scheduled_blocks
  id
  user_id
  date
  start_time
  end_time
  kind
  title
  description
```

```text
scheduled_activities
  id
  user_id
  date
  start_time
  end_time
  title
  description
  course_task_id
```

```text
schedule_day_observations
  id
  user_id
  date
  description
```

```text
schedule_date_observations
  id
  user_id
  starts_on
  ends_on
  description
```

## Commitment

```text
reminders
  id
  user_id
  remind_at
  title
  description
  status
```

```text
deadlines
  id
  user_id
  due_at
  title
  description
  course_id
  course_task_id
  status
```

---

# Current File Layout

Recommended current layout:

```text
src/backend/context/schedule/
  __init__.py

  domain/
    __init__.py

    shared/
      __init__.py
      local_time.py
      schedule_date.py
      time_block_kind.py
      time_range.py

    template/
      __init__.py
      entities/
        __init__.py
        weekly_schedule_template.py
        schedule_day_template.py
        time_block.py
        day_marker.py
        weekly_schedule_observation.py
      value_objects/
        __init__.py
        weekday.py
        day_marker_kind.py

    execution/
      __init__.py
      entities/
        __init__.py
        schedule_day.py
        scheduled_block.py
        scheduled_activity.py
        schedule_day_observation.py
        schedule_date_observation.py

    commitment/
      __init__.py
      entities/
        __init__.py
        reminder.py
        deadline.py
      value_objects/
        __init__.py
        commitment_status.py
```

---

# Implementation Rules

Current implementation style:

```text
Pure dataclasses
kw_only=True
slots=True
No Direttore aggregate root base class
No Direttore Validatable
No Direttore StateMachine currently needed
```

Validation is performed directly in:

```text
__post_init__
entity methods that mutate fields
```

General text field rules:

```text
title is used when an entity needs a short user/agent-readable name.
description is used for longer narrative context.
observations use description only when title would be redundant.
```

Identifier rules:

```text
UUID is used for most entities.
ScheduleDay identity is user_id + date.
ScheduleDayTemplate identity is weekly_schedule_template_id + weekday.
```

Timestamp/datetime rules:

```text
Template and execution day times use LocalTime.
Reminder.remind_at and Deadline.due_at use datetime in UTC.
Naive datetime in commitment is accepted as UTC by convention.
Aware non-UTC datetime is rejected.
```

---

# Summary

The `schedule` domain is built around three layers:

```text
template
  Ordinary repeating weekly structure.

execution
  Concrete generated day snapshots and actual day context.

commitment
  Reminders and deadlines that should be remembered or planned around.
```

The most important design choices are:

```text
Generate days one day ahead, usually during user sleep.
Copy template blocks into ScheduleDay as ScheduledBlock snapshots.
Do not link ScheduleDay back to WeeklyScheduleTemplate after generation.
Do not track status on ScheduledActivity.
Use nullable course_task_id for optional course relation.
Keep Reminder/Deadline status minimal: ACTIVE/CANCELLED.
Use observations as lightweight narrative context, not structured analytics or graph memory.
Keep TimeBlockKind small and remove subtype.
```
