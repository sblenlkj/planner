# Planner Agent Server: Agents, Workflows and LLM Runtime

## 1. Purpose of this document

This document summarizes the current architectural discussion about the `agent` server in the Planner platform.

It is intended as a working context document for preparing a presentation about:

- how interactive agents are organized;
- which background agents exist;
- which non-agent workflows are needed;
- where one-shot LLM inference is used;
- how the LLM inference provider is accessed through the internal pool/orchestrator;
- how the agent server fits into the wider Planner architecture.

The main conclusion is:

```text
The agent server does not contain only chat agents.
It contains several classes of LLM-powered workloads:

1. synchronous conversation agents;
2. asynchronous background agents;
3. workflow-style LLM pipelines;
4. one-shot LLM inference calls;
5. batch/background LLM jobs.
```

All of these workloads should use the same LLM access layer instead of talking directly to GigaChat, LangChain, or any specific provider SDK.

---

## 2. High-level architecture

The Planner platform has three separate servers:

```text
Telegram Gateway Server
  Receives Telegram updates and sends Telegram messages.

Backend Server
  Modular monolith with domain contexts.
  Owns business state, domain logic, application services and persistence.

Agent Server
  Runs agents, workflows, one-shot LLM inference and background LLM processing.
```

The backend remains the owner of business domains. The agent server should not become the owner of schedule, courses, reminders, analytics, connectors, or users. It orchestrates reasoning and calls backend application services over stable interfaces.

In simplified form:

```text
Telegram user
  -> Telegram Gateway
  -> Agent Server
  -> Backend application services
  -> Backend domains / persistence
```

For asynchronous processing:

```text
Backend domain event / connector event / scheduled job
  -> queue/topic
  -> Agent Server workflow or background agent
  -> Backend application service / target domain
```

---

## 3. Main design principle

The key distinction is between:

```text
Agent
  A stateful or semi-stateful LLM-driven process that can reason, use tools,
  make decisions, hand off control, or run multiple steps.

Workflow
  A bounded LLM-powered pipeline with a specific input and output.
  It may use LangGraph, but it is not necessarily an interactive agent.

One-shot inference
  A single LLM call used for classification, extraction, summarization,
  normalization, or small interpretation tasks.

Deterministic runtime/router
  Ordinary application code that routes requests, loads state,
  invokes the correct agent/workflow/action, persists results and sends responses.
```

The agent server should not treat every LLM call as a full agent. Many operations are cheaper and clearer as workflows or one-shot inference calls.

---

## 4. Synchronous conversation graph

The main user-facing chat interaction is handled by a synchronous conversation graph.

This graph is not one giant supervisor LLM agent. It is a deterministic runtime with a single entry point.

Its responsibilities:

```text
1. receive incoming user message;
2. load conversation state;
3. check active_agent / current mode / metadata flags;
4. route the message to the selected specialized conversation agent;
5. execute the returned action, query, handoff or response;
6. persist updated state;
7. send response to Telegram if needed.
```

Important: this router is not an LLM call.

It is ordinary code:

```text
incoming message
  -> load conversation state
  -> check active_agent or routing flag
  -> route to concrete agent node
  -> execute result
  -> save state
```

LLM is invoked only inside the selected specialized agent if needed.

---

## 5. The main conversation agent as a composition of three agents

The main synchronous user-facing agent is conceptually composed of three specialized agents.

They do not need a separate “chief LLM agent”. They work under a deterministic conversation runtime and can hand off control to each other.

The handoff model is similar to “hot potato”: the currently active agent handles the message until it decides the task belongs to another specialized agent.

The three synchronous agents are:

```text
1. PlanningConfigurationAgent
2. ProgressReflectionAgent
3. ProgressCaptureAgent
```

---

## 6. PlanningConfigurationAgent

### Responsibility

This agent manages user-facing planning configuration.

It handles changes to the user’s operational planning setup: weekly templates, availability, reminders, language, timezone and other preferences that affect future planning.

### Typical user requests

```text
“Теперь по понедельникам я ничего не могу делать.”
“Удали всё свободное время в понедельник.”
“Поменяй мой язык на английский.”
“Напомни мне через три дня купить ...”
“Теперь ставь спортзал рядом с работой.”
“Не ставь математику вечером.”
```

### Owns at agent level

The agent does not own backend business data directly. It orchestrates calls to backend application services.

It may call services related to:

```text
User settings
  - language
  - timezone

Planning configuration
  - weekly template
  - availability windows
  - template observations
  - planning preferences

Reminders
  - one-time reminders
  - recurring reminders
  - reminder constraints
```

### Important distinction

This agent should not be confused with the profile consolidation agent.

```text
PlanningConfigurationAgent
  Changes explicit operational planning settings.

UserProfileConsolidationAgent
  Derives and updates long-lived user model/profile from signals.
```

Example:

```text
User says: “On Mondays I cannot study.”
  -> PlanningConfigurationAgent updates weekly template.

System observes: “User repeatedly fails morning math sessions.”
  -> UserProfileConsolidationAgent may later update user profile or analytics.
```

---

## 7. ProgressReflectionAgent

### Responsibility

This is a mostly read-oriented agent for discussing progress with the user.

It answers analytical questions about what the user did, what is going well, what is difficult, and what should be changed.

### Typical user requests

```text
“Проанализируй мои последние три дня.”
“Почему я ничего не успеваю?”
“Как у меня идёт математика?”
“Что у меня получается лучше?”
“Что мне стоит поменять в расписании?”
```

### Behavior

This agent should usually read data and explain it. It can generate recommendations, but it should not directly mutate planning configuration unless the user explicitly wants a change.

If the user shifts from analysis to configuration change, it should hand off to `PlanningConfigurationAgent`.

Example:

```text
User: “Кажется, я плохо делаю математику. Давай меньше её ставить.”

ProgressReflectionAgent:
  1. understands that user is asking for planning change;
  2. creates handoff to PlanningConfigurationAgent;
  3. passes reason and proposed change payload.
```

### Read sources

It may read:

```text
recent generated days;
completed course times;
missed blocks;
course progress;
analytics observations and insights;
schedule feedback;
user profile;
planning configuration.
```

---

## 8. ProgressCaptureAgent

### Responsibility

This agent receives user reports about completed or missed work and turns natural language into structured progress events.

It is the user-facing reporting agent.

### Typical user messages

```text
“Сегодня прочитал 30 страниц.”
“Сделал 5 задач по математике.”
“Книгу закончил.”
“Python сегодня успел, математику нет.”
“Не сделал английский, потому что устал.”
```

### Main tasks

```text
1. parse natural-language progress report;
2. match reported work to planned schedule items or course times;
3. mark items completed, partially completed or missed;
4. summarize useful observations;
5. emit domain/application events for asynchronous processing;
6. respond briefly to the user.
```

### Possible outputs

```text
CourseTimeCompleted
CourseTimePartiallyCompleted
ScheduleBlockMissed
UserReportedProgress
UserReportedObstacle
ObservationCandidateCreated
```

The agent may emit events that are later consumed by asynchronous agents or workflows, such as graph ingestion or analytics/session analysis.

---

## 9. Handoff protocol between synchronous agents

The three synchronous agents know about each other and can hand off control.

A clean runtime-level result model can look like this:

```text
AgentTurnResult:
  - Respond
  - QueryAndContinue
  - CommandAndFinish
  - Handoff
  - AskClarification
```

Example handoff:

```json
{
  "kind": "handoff",
  "target_agent": "PlanningConfigurationAgent",
  "reason": "User wants to change Monday availability",
  "payload": {
    "change_type": "weekly_template_update",
    "day": "monday",
    "availability": "none"
  }
}
```

This makes routing debuggable and explicit.

The deterministic runtime stores:

```text
conversation_id
active_agent
handoff_reason
handoff_payload
last_intent
conversation metadata
```

---

## 10. Terminal actions vs interactive tools

A major optimization is to distinguish between two types of agent actions.

### 10.1 Interactive tool call

Used when the agent needs the result to continue reasoning.

Flow:

```text
Agent LLM
  -> tool call
  -> tool result
  -> Agent LLM continues
  -> final response
```

Examples:

```text
find free schedule slots;
read last 3 days of progress;
load current weekly template;
compare possible planning changes;
check existing reminders.
```

This is more expensive because it requires another LLM step after the tool result.

### 10.2 Terminal action / command node

Used when the agent has already decided what to do and does not need the result for further reasoning.

Flow:

```text
Agent LLM
  -> returns command + prepared success message
  -> runtime executes command
  -> runtime sends prepared message if command succeeds
```

Examples:

```text
create reminder;
change language;
change timezone;
update weekly template;
mark item completed;
add template observation;
emit async event.
```

The agent can generate the success message in advance, but the runtime sends it only after successful execution.

Example:

```json
{
  "kind": "command_and_finish",
  "command": {
    "type": "CreateReminder",
    "payload": {
      "text": "купить ...",
      "due_at": "2026-06-11T09:00:00+02:00"
    }
  },
  "success_message": "Готово, напомню тебе через три дня.",
  "failure_message": "Не получилось создать напоминание. Изменения не сохранены."
}
```

This avoids unnecessary second LLM calls.

---

## 11. Asynchronous background agents

Some agents should not run inside the user-facing synchronous conversation graph.

They are triggered by scheduled jobs, backend events, connector events or queue/topic messages.

The currently discussed asynchronous agents are:

```text
1. ScheduleProjectionAgent
2. KnowledgeGraphIngestionAgent
3. UserProfileConsolidationAgent
```

---

## 12. ScheduleProjectionAgent

### Responsibility

This agent generates future user days from long-lived planning state.

It may run at night or every 2–3 days, depending on the planning strategy.

### Input

```text
user profile;
analytics insights;
weekly schedule template;
planning preferences;
courses;
course times;
reminders;
constraints;
existing generated days;
recent performance signals.
```

### Output

```text
future daily schedule;
planned course blocks;
planned reminders;
regenerated affected days;
schedule generation explanation/log.
```

### Example trigger

```text
Nightly job:
  “Generate day for user U for date D+3.”
```

### Important property

This agent should be idempotent.

If the same message is processed twice, it should not create duplicate schedule days. It should either detect that the projection already exists or update the existing projection deterministically.

---

## 13. KnowledgeGraphIngestionAgent

### Responsibility

This agent consumes completed learning/activity events and decides whether they should update the knowledge graph.

It is not just a logger. It decides whether an event or observation is important enough to become graph structure.

### Input examples

```text
CourseTimeCompleted
CourseSessionSummarized
UserReportedProgress
ObservationAttached
BookFinished
TopicPracticed
```

### Output examples

```text
GraphVertexCreated
GraphVertexUpdated
GraphEdgeCreated
ObservationPromotedToKnowledge
NoGraphChangeNeeded
```

### Important distinction

Not every completed action should become a graph vertex.

Example:

```text
“User read 20 pages of book X.”
  Usually progress event.

“User repeatedly struggles with derivatives.”
  Candidate for analytics insight, graph relation or learning profile update.
```

This agent should focus on durable knowledge structure, not raw activity logging.

---

## 14. UserProfileConsolidationAgent

### Responsibility

This agent updates the long-lived user profile or user model from accumulated signals.

It should not react too strongly to one isolated event. It should aggregate multiple observations and assign confidence.

### Input

```text
recent performance;
missed sessions;
completed sessions;
analytics observations;
analytics insights;
schedule friction;
reported preferences;
learning difficulties;
communication preferences.
```

### Output

```text
UserProfilePatch
LearningPaceAdjusted
ScheduleBiasChanged
PreferenceUpdated
NoProfileChangeNeeded
```

### Example

Instead of immediately writing:

```text
User is bad at math.
```

it should produce something more careful:

```text
User currently struggles with math problem-solving under time pressure.
confidence: 0.65
basis: last 5 math sessions
stability: short_term
```

The profile can then influence future schedule generation.

---

## 15. Non-agent workflows in the agent server

The agent server also needs LLM-powered workflows that are not full agents.

These workflows are bounded, input/output-oriented processes.

Current important workflows:

```text
1. SessionAnalysisWorkflow
2. ConnectorInterpretationWorkflow
3. AnalyticsInsightDerivationWorkflow
4. BatchGraphUpdateWorkflow
```

Some of them may internally use LangGraph. Others may be a sequence of ordinary application steps and one or more LLM calls.

---

## 16. SessionAnalysisWorkflow

### Responsibility

After a user conversation session closes, this workflow analyzes the session transcript and extracts useful long-lived observations.

This keeps the realtime chat path lighter and avoids forcing every observation to be written during the conversation.

### Input

```text
conversation_id;
user_id;
session transcript;
agent decisions;
user statements;
completed actions;
possibly schedule/progress changes made during the session.
```

### Output

```text
AnalyticsObservation candidates;
possibly rejected/no-op results;
evidence text;
tags;
confidence;
importance;
stability;
source reference to conversation/session.
```

### Why it exists

The user may say many things during a session that are useful for personalization:

```text
“I prefer short answers.”
“I did Python today but skipped math.”
“I usually cannot study on Mondays.”
“I understand syntax but get confused by async.”
“I do not want long theoretical explanations.”
```

Not all of this should immediately mutate profile or planning state. Some of it should become analytics observations.

### Target domain

The workflow writes to the `analytics` context.

Analytics stores long-lived semantic memory about the user:

```text
what the user struggles with;
what the user prefers;
communication style;
productivity patterns;
planning-relevant tendencies;
learning-related observations.
```

It should not store raw chat transcript or ephemeral current states.

Correct analytics observation example:

```text
scope: education
description: User understands basic Python syntax but struggles with asyncio and event loop concepts.
evidence: User asked several questions about asyncio during the session.
confidence: 0.75
importance: 0.8
stability: short_term
tags: python, asyncio, event-loop
```

Incorrect analytics observation example:

```text
User is tired today.
```

This is ephemeral and should remain in current session/day context, not long-lived analytics.

---

## 17. ConnectorInterpretationWorkflow

### Responsibility

This workflow interprets external signals delivered by connectors.

The connectors context should only normalize and record external events. It should not decide their life-planning meaning.

Example:

```text
Gmail message received
  -> Gmail adapter reads message
  -> ConnectorEvent is recorded
  -> ConnectorInterpretationWorkflow is dispatched
  -> LLM/application logic classifies or extracts meaning
  -> target domain is updated if needed
```

### Input

```text
ConnectorEvent;
provider;
event_type;
external_event_id;
payload or payload reference;
user context;
optional existing connector/job metadata.
```

### Output examples

```text
IgnoreExternalEvent
ClassifyAsSpam
ClassifyAsUseful
ExtractDeadlineCandidate
ExtractReminderCandidate
ExtractScheduleConstraint
ExtractAnalyticsObservationCandidate
DispatchToSchedule
DispatchToReminders
DispatchToAnalytics
```

### Gmail example

A Gmail message arrives.

The connector records:

```text
ConnectorEvent:
  provider: gmail
  event_type: gmail_message_received
  status: received
  payload: normalized message payload or reference
```

The interpretation workflow decides:

```text
Is it spam?
Is it useful?
Does it contain a deadline?
Does it contain an event?
Does it affect schedule?
Should we ignore it?
Should we ask the user?
```

This may be a small workflow or a single LLM call.

---

## 18. AnalyticsInsightDerivationWorkflow

### Responsibility

This workflow derives higher-level analytics insights from multiple analytics observations.

Observation means:

```text
This was noticed.
```

Insight means:

```text
This is a derived user-level conclusion.
```

### Input

```text
active analytics observations;
previous insights;
recent user progress;
relevant tags/scopes;
possibly profile state.
```

### Output

```text
AnalyticsInsight created;
AnalyticsInsight superseded;
NoInsightChangeNeeded;
low-confidence candidate rejected.
```

### Example

Input observations:

```text
User skipped morning math twice.
User completed evening Python sessions successfully.
User said morning tasks feel heavy.
```

Possible derived insight:

```text
scope: productivity
description: User currently performs better on cognitively demanding tasks later in the day than in the morning.
confidence: 0.72
importance: 0.85
stability: short_term
tags: morning, focus, scheduling
```

This insight can later influence schedule generation.

---

## 19. BatchGraphUpdateWorkflow

### Responsibility

This is a batch-oriented workflow for processing homogeneous chunks of graph update tasks.

It may be used by the graph ingestion path when many similar items need to be processed with the same agent definition, same system prompt, same tool definitions and many different user payloads.

### Why batch matters

Batching can improve provider efficiency and prompt-cache locality when the provider supports caching repeated prefixes.

Example:

```text
same provider slot
same agent definition
same system prompt
same output schema
many dynamic user payloads
```

This maps well to the `BATCH_DRAIN` execution scope in the LLM runtime.

---

## 20. One-shot LLM inference calls

Some tasks do not need an agent or workflow.

They need a single structured LLM call.

### Examples

```text
classify email as spam / not spam;
classify connector event relevance;
extract possible deadline from short text;
summarize a short event payload;
normalize user preference statement;
classify user message intent for routing fallback;
extract language/timezone from explicit user statement;
generate compact title for conversation/session;
```

### Execution model

```text
caller
  -> LlmOrchestrator.complete(...)
  -> structured response
  -> deterministic application logic continues
```

This should use execution scope:

```text
ONE_SHOT
```

and workload depending on purpose:

```text
INTERACTIVE
BACKGROUND
GRAPH_UPDATE
```

---

## 21. Connectors and interpretation boundary

The connectors bounded context is integration-oriented.

It owns:

```text
external provider connection state;
connector job lifecycle;
incoming external event lifecycle;
provider-specific integration rules only when stable;
normalized handoff into application services/workflows.
```

It should not own:

```text
schedule blocks;
deadlines;
courses;
observations;
reminders;
user semantic interpretation;
life-planning meaning of external messages.
```

The principle:

```text
connectors delivers external signals;
target domains and application/agent workflows decide what those signals mean.
```

Therefore, Gmail/YouTube/etc. events are first normalized as connector events, then dispatched to workflows or application services for interpretation.

---

## 22. Analytics and session observations

The analytics context stores semantic user memory.

It is description-first, not subject/predicate/value based.

It owns two main record types:

```text
AnalyticsObservation
  A concrete observed signal about the user.

AnalyticsInsight
  A derived conclusion built from one or more observations.
```

Analytics records include:

```text
scope;
description;
evidence;
confidence;
importance;
stability;
status;
tags;
valid_until.
```

Supported scopes:

```text
education;
food;
sport;
productivity;
communication.
```

This fits session analysis well, because session analysis can extract records like:

```text
User prefers direct short answers.
User struggles with Python asyncio.
User works better when tasks are split into small concrete steps.
User currently avoids difficult math tasks in the morning.
```

Analytics should not store:

```text
raw chat transcript;
technical agent traces;
ephemeral current mood;
schedule blocks;
course progress;
reminders.
```

---

## 23. LLM runtime architecture

All LLM-powered components should access models through the internal LLM runtime module.

They should not access GigaChat, LangChain provider clients, API keys or raw provider SDKs directly.

The access path is:

```text
Agent / LangGraph / Background worker
  -> LlmOrchestrator
    -> LlmProviderPool
      -> LlmSession
        -> LlmSlot
          -> LlmProviderPort
            -> concrete provider adapter, e.g. GigaChatProvider
```

---

## 24. LlmOrchestrator

`LlmOrchestrator` is the public entry point for model access inside the agent server.

It supports:

```text
one-shot complete calls;
session acquisition for longer execution scopes;
provider-slot reservation;
workload-specific capacity;
provider abstraction through ports.
```

Agents and workflows depend on `LlmOrchestrator`, not on GigaChat directly.

---

## 25. Session-first model

The LLM runtime uses a session-first model.

A provider slot is reserved for the whole execution scope, not only for one provider call.

Execution scopes:

```text
ONE_SHOT
  One short complete() call.

AGENT_RUN
  One interactive agent execution.

WORKFLOW_RUN
  One bounded workflow execution.

BATCH_DRAIN
  One homogeneous batch chunk.
```

Example:

```text
agent starts
  -> acquire LlmSession
  -> use same reserved provider slot for all model calls
  -> call backend tools over local gRPC
  -> produce final answer
  -> release LlmSession
agent ends
```

This gives the runtime control over concurrency and provider capacity.

---

## 26. LlmSlot

`LlmSlot` is an exclusive provider runtime.

It is not just an API key.

It contains:

```text
provider credential;
provider client;
model config;
concurrency permit = 1;
workload group.
```

If there are five provider keys, the system can create five slots.

Slots can be assigned to workload classes.

Example:

```text
interactive:
  key_1, key_2, key_3

background / graph_update:
  key_4, key_5
```

This gives a simple first-version capacity model without implementing a complex dynamic scheduler.

---

## 27. Workload classes

Possible workload classes:

```text
INTERACTIVE
  User-facing chat and synchronous agent turns.

BACKGROUND
  Scheduled workflows, session analysis, connector interpretation, batch processing.

GRAPH_UPDATE
  Graph ingestion, knowledge consolidation, long-running graph-related workflows.
```

This avoids background tasks starving user-facing conversation capacity.

---

## 28. Provider abstraction

The runtime hides concrete providers behind a port.

Conceptually:

```python
class LlmProviderPort(Protocol):
    async def complete(self, request: LlmRequest) -> LlmResponse:
        ...
```

Provider-specific details live in adapters, for example:

```text
src/agent/llm/adapters/gigachat.py
```

This makes it possible to replace or add providers later without changing agents and workflows.

---

## 29. Safety limits

Every LLM workload should have explicit safety bounds.

Important limits:

```text
max_duration_seconds on LlmSession;
max_agent_steps inside LangGraph/LangChain agents;
timeout on backend tools;
timeout on provider calls;
bounded queues;
workload-specific capacity;
retry/cooldown policy for failed slots;
idempotency for async handlers.
```

For the first version, the pool is in-process and should run in a single FastAPI process unless replaced with distributed leases.

---

## 30. How all pieces fit together

### Interactive user request

```text
Telegram message
  -> Telegram Gateway
  -> Agent Server conversation runtime
  -> deterministic router checks active_agent
  -> selected synchronous agent runs
  -> agent may query backend tools or return command
  -> backend application services mutate/read domains
  -> response sent to user
```

### User reports progress

```text
User: “Сегодня сделал Python, но математику не успел.”
  -> ProgressCaptureAgent
  -> parse report
  -> match planned items
  -> mark Python completed
  -> mark math missed or partially completed
  -> emit progress/observation events
  -> respond to user
  -> later SessionAnalysisWorkflow / UserProfileConsolidationAgent may consume signals
```

### User asks for analysis

```text
User: “Проанализируй последние три дня.”
  -> ProgressReflectionAgent
  -> read progress/schedule/analytics context
  -> explain patterns
  -> optionally recommend changes
  -> handoff to PlanningConfigurationAgent if user wants to mutate planning settings
```

### User changes planning settings

```text
User: “По понедельникам я больше не могу учиться.”
  -> PlanningConfigurationAgent
  -> command_and_finish: update weekly template
  -> runtime executes backend command
  -> success message sent
  -> ScheduleProjectionAgent may later regenerate affected days
```

### Session closes

```text
Conversation session closed
  -> SessionAnalysisWorkflow
  -> analyze transcript
  -> extract AnalyticsObservation candidates
  -> write useful long-lived observations to analytics
  -> ignore ephemeral states
```

### Gmail message arrives

```text
Gmail provider
  -> Gmail adapter
  -> connectors context records ConnectorEvent
  -> dispatch ConnectorInterpretationWorkflow
  -> one-shot or small workflow classifies/extracts meaning
  -> possible target actions:
       ignore;
       create reminder candidate;
       extract deadline;
       create analytics observation;
       ask user;
       dispatch to schedule/reminders.
```

### Future day generation

```text
Scheduled job / topic message
  -> ScheduleProjectionAgent
  -> load user profile + analytics + weekly template + courses + reminders
  -> generate or regenerate future schedule day
  -> persist projection through backend services
```

### Completed course time processed into graph

```text
CourseTimeCompleted event
  -> KnowledgeGraphIngestionAgent
  -> inspect summary and observations
  -> decide whether graph should change
  -> create/update graph nodes or return no-op
```

### Profile consolidation

```text
Accumulated observations and progress signals
  -> UserProfileConsolidationAgent
  -> derive profile patch with confidence
  -> update user model
  -> future schedule generation uses updated profile
```

---

## 31. Proposed terminology

Recommended names:

```text
Synchronous runtime:
  ConversationRuntime
  ConversationRouter
  MainConversationGraph

Synchronous agents:
  PlanningConfigurationAgent
  ProgressReflectionAgent
  ProgressCaptureAgent

Asynchronous agents:
  ScheduleProjectionAgent
  KnowledgeGraphIngestionAgent
  UserProfileConsolidationAgent

Workflows:
  SessionAnalysisWorkflow
  ConnectorInterpretationWorkflow
  AnalyticsInsightDerivationWorkflow
  BatchGraphUpdateWorkflow

LLM runtime:
  LlmOrchestrator
  LlmProviderPool
  LlmSession
  LlmSlot
  LlmProviderPort
```

---

## 32. Architectural summary

The current architecture should be described as follows:

```text
Planner uses the agent server as a controlled LLM execution environment.

The user-facing chat is handled by a deterministic conversation runtime,
which routes messages to one of three specialized synchronous agents.

Long-running or event-driven reasoning is handled by asynchronous background agents.

Bounded non-conversational LLM tasks are implemented as workflows or one-shot inference calls.

All LLM access goes through LlmOrchestrator and LlmProviderPool,
which reserve provider slots by workload and execution scope.

The backend modular monolith remains the owner of business domains.
The agent server orchestrates interpretation, reasoning and personalization,
but business state is changed through backend application services.
```

---

## 33. Key ideas for presentation

The presentation can emphasize five points:

### 1. One agent server, multiple LLM workload types

```text
interactive agents;
background agents;
workflows;
one-shot inference;
batch jobs.
```

### 2. No giant supervisor LLM

```text
Routing is deterministic.
Specialized agents do the reasoning.
The runtime controls state, handoff and command execution.
```

### 3. Three-agent synchronous conversation model

```text
PlanningConfigurationAgent
ProgressReflectionAgent
ProgressCaptureAgent
```

Together they cover configuration, analysis and reporting.

### 4. Asynchronous agents build long-term intelligence

```text
ScheduleProjectionAgent generates future days.
KnowledgeGraphIngestionAgent updates durable knowledge structure.
UserProfileConsolidationAgent updates user model from accumulated signals.
```

### 5. LLM runtime is centralized and capacity-aware

```text
LlmOrchestrator
  -> LlmProviderPool
    -> reserved LlmSession
      -> exclusive LlmSlot
        -> provider adapter
```

This makes provider usage controlled, testable and replaceable.

---

## 34. Open questions for next design iteration

The following topics still need more precise design:

```text
1. Exact ConversationState schema.
2. Exact AgentTurnResult DTO and command/query/handoff contracts.
3. Which backend services are exposed to each agent as tools or command nodes.
4. How session closing is detected.
5. How SessionAnalysisWorkflow avoids duplicate observations.
6. How connector events are dispatched to workflows.
7. Which workflows are LangGraph and which are simple one-shot calls.
8. How analytics observations are reviewed, deduplicated or promoted to insights.
9. How async agents guarantee idempotency.
10. Whether LLM slot pool later needs distributed leases.
```

---

## 35. Minimal first implementation slice

A pragmatic first implementation could be:

```text
1. Implement LlmOrchestrator / LlmProviderPool / LlmSession / LlmSlot.
2. Implement deterministic ConversationRuntime with active_agent routing.
3. Implement one synchronous agent first: ProgressCaptureAgent.
4. Add command_and_finish support for simple terminal actions.
5. Add SessionAnalysisWorkflow as a background workflow writing AnalyticsObservation.
6. Add ConnectorInterpretationWorkflow as one-shot classification for Gmail message events.
7. Later add PlanningConfigurationAgent and ProgressReflectionAgent.
8. Later add ScheduleProjectionAgent, KnowledgeGraphIngestionAgent and UserProfileConsolidationAgent.
```

This keeps the first version small while preserving the final architecture.
