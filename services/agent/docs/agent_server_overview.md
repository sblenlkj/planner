# Agent Server Overview

## Purpose

This document describes the initial architecture of the Planner Agent Server.

The Agent Server is the reasoning/runtime service of Planner. It exposes FastAPI endpoints for conversational agent turns, one-shot LLM tasks, and internal system agent jobs.

It does not own durable domain state. It does not own Telegram transport. It does not own long-term memory as source of truth.

---

## Core Formula

```text
Telegram Gateway owns Telegram transport and short-term conversation cache.
Backend owns canonical domain state.
Agent Server owns reasoning, workflows, native tools, LLM calls, and agent orchestration.
```

The Agent Server receives already resolved business identity:

```text
business_user_id
session_id
channel
message
history
metadata
```

It should not resolve Telegram users itself.

It should call Backend through typed capabilities, preferably gRPC.

It should not read Backend database tables directly.

---

## Main Responsibilities

The Agent Server owns:

```text
agent routing
user-facing agent orchestration
system agent jobs
one-shot LLM tasks
prompt/context assembly
native Python tools
Backend gRPC client usage
LLM provider calls
provider key pool / execution slots
input/output security guards
tool permission policy
LLM task caching where safe
tracing/correlation metadata
```

The Agent Server does not own:

```text
Planner domain tables
Telegram webhook handling
Telegram Bot API delivery
Telegram session cache
canonical user identity
schedule source of truth
graph source of truth
analytics source of truth
connectors source of truth
```

---

## External Endpoints

The Agent Server should expose separate endpoints for different classes of work.

Recommended initial endpoints:

```text
POST /agent/turn
POST /llm/task
POST /agent/jobs/run
```

These should not be collapsed into one endpoint because they have different semantics, security rules, retry behavior, timeouts, tracing, and schemas.

---

## Endpoint: POST /agent/turn

### Purpose

Main user-facing conversational endpoint.

Called by Telegram Gateway after the gateway has:

```text
resolved telegram_user_id -> business_user_id
loaded short-term message history from Redis
normalized the current user message
```

### Input concept

```json
{
  "business_user_id": "uuid",
  "session_id": "telegram:123456789",
  "channel": "telegram",
  "mode": "default",
  "message": {
    "role": "user",
    "content": "Привет",
    "created_at": "..."
  },
  "history": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ],
  "metadata": {
    "correlation_id": "...",
    "telegram_chat_id": "...",
    "telegram_user_id": "..."
  }
}
```

### Output concept

```json
{
  "assistant_message": {
    "role": "assistant",
    "content": "..."
  },
  "agent_run_id": "...",
  "metadata": {
    "correlation_id": "..."
  }
}
```

### Internal flow

```text
run_agent_turn
  -> create request/run context
  -> run input guard
  -> resolve requested mode or route automatically
  -> select agent module
  -> assemble prompt/context
  -> allow only permitted tools
  -> call LLM provider through provider pool
  -> call Backend tools if needed
  -> run output guard
  -> return assistant message
```

---

## Endpoint: POST /llm/task

### Purpose

Backend-facing endpoint for one-shot LLM tasks.

This is not a conversational agent turn. It is a stateless task.

Examples:

```text
classify whether a YouTube video is relevant
summarize text
extract tags
classify a note
answer yes/no based on strict criteria
produce a short structured summary
```

### Important Rules

One-shot tasks should have strict input/output schemas.

They should not receive full Telegram conversation history.

They should not have broad access to tools unless explicitly needed.

They are good candidates for deterministic caching.

### Internal flow

```text
run_llm_task
  -> validate task type
  -> run input guard
  -> build task-specific prompt
  -> check task cache if safe
  -> call LLM provider through provider pool
  -> parse structured response
  -> run output guard
  -> cache result if safe
  -> return structured result
```

---

## Endpoint: POST /agent/jobs/run

### Purpose

Backend-facing endpoint for internal system agent jobs.

These are agent workflows started by Backend or API Scheduler.

Examples:

```text
update user profile from accumulated events/notes
update graph from feedback/notes/materials
generate daily or weekly reflection
compact knowledge cards
cluster notes
```

### Important Rules

System jobs are not interactive.

They can be longer than user-facing turns.

They should have lower priority than interactive user messages.

They should use explicit job types and explicit tool permissions.

### Internal flow

```text
run_system_job
  -> validate job type
  -> create system run context
  -> select system agent module
  -> load required data from Backend through tools/gRPC
  -> execute workflow
  -> write results back to Backend through tools/gRPC
  -> return job result
```

---

## User-Facing Agents

Agents should not be implemented as single large `.py` files. Each agent should be a package/module directory.

Each agent folder should contain the files needed to understand that agent locally:

```text
definition.py
prompts.py
schemas.py
workflow.py
tools.py
README.md later if needed
```

The exact content can grow later, but the folder boundary should exist early.

Recommended user-facing agents:

```text
agents/
  router_agent/
  default_assistant_agent/
  profile_setup_agent/
  schedule_setup_agent/
  notes_capture_agent/
```

---

## Agent: router_agent

### Responsibility

Routes a user turn to the correct user-facing agent.

It may use:

```text
explicit mode from Telegram buttons
current conversation context
message intent classification
simple deterministic rules
LLM-based routing later
```

### Owns

```text
mode resolution
agent selection
fallback decision
routing metadata
```

### Does not own

```text
profile setup workflow
schedule setup workflow
note interpretation workflow
Backend writes
LLM provider implementation
```

### Suggested files

```text
agents/router_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
```

### Example modes

```text
default
profile_setup
schedule_setup
notes_capture
```

---

## Agent: default_assistant_agent

### Responsibility

General user-facing assistant for normal conversation.

It can answer general questions about the Planner system, help the user decide what to do next, and delegate to more specialized agents when needed.

### Owns

```text
default conversation behavior
high-level user assistance
fallback responses
delegation suggestions
```

### Does not own

```text
deep profile setup
detailed schedule setup
long-term graph update jobs
system profile reflection jobs
```

### Suggested files

```text
agents/default_assistant_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
  tools.py
```

---

## Agent: profile_setup_agent

### Responsibility

Helps the user configure their profile.

This agent can ask questions and convert answers into structured profile/preference updates.

Canonical storage remains in Backend:

```text
user context
analytics context
```

### Owns

```text
profile onboarding conversation
preference extraction
basic personalization questions
profile update proposals
```

### Possible data collected

```text
name
main goals
work/study context
preferred learning style
productive time windows
activities user likes/dislikes
constraints
```

### Suggested files

```text
agents/profile_setup_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
  tools.py
```

---

## Agent: schedule_setup_agent

### Responsibility

Helps the user configure availability, schedule constraints, deadlines, and routine.

Canonical storage remains in Backend `schedule` context.

### Owns

```text
availability setup conversation
schedule constraint extraction
deadline clarification
activity type constraints
schedule update proposals
```

### Possible data collected

```text
working hours
sleep time
commute time
gym time
reading-friendly slots
coding-friendly slots
deadlines
recurring constraints
```

### Suggested files

```text
agents/schedule_setup_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
  tools.py
```

---

## Agent: notes_capture_agent

### Responsibility

Interprets user notes and daily updates.

Examples:

```text
"I read 10 pages today."
"I did not do anything."
"The chapter about Unit of Work was useful."
"I want to remember this idea."
```

This agent converts free-form user text into structured updates for Backend.

### Owns

```text
note interpretation
progress extraction
feedback extraction
graph note candidate creation
analytics event proposal
```

### Possible outputs

```text
plan feedback
plan progress event
analytics behavior event
graph note candidate
knowledge card suggestion
```

### Suggested files

```text
agents/notes_capture_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
  tools.py
```

---

## System Agents

System agents are not directly exposed to Telegram conversation.

They are triggered by Backend or API Scheduler through:

```text
POST /agent/jobs/run
```

Recommended system agents:

```text
agents/system/
  profile_reflection_agent/
  graph_update_agent/
```

---

## System Agent: profile_reflection_agent

### Responsibility

Periodically updates user profile and analytics insights from accumulated events, notes, schedule behavior, plan feedback, and other signals.

Canonical storage remains in Backend `analytics` context.

### Owns

```text
profile reflection workflow
behavior signal interpretation
preference/profile update proposals
periodic reflection output
```

### Suggested files

```text
agents/system/profile_reflection_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
  tools.py
```

---

## System Agent: graph_update_agent

### Responsibility

Updates long-term semantic memory from notes, feedback, completed plan items, and materials.

Canonical storage remains in Backend `graph` context.

### Owns

```text
knowledge extraction
knowledge card proposal
semantic relation suggestion
note clustering
graph update proposal
```

### Suggested files

```text
agents/system/graph_update_agent/
  __init__.py
  definition.py
  prompts.py
  schemas.py
  workflow.py
  tools.py
```

---

## LangGraph / Workflows

The Agent Server may use LangGraph for complex workflows.

LangGraph-specific code should not be mixed directly into FastAPI routes.

Recommended placement:

```text
workflows/
```

Possible usage:

```text
workflows/common/
workflows/user_turn/
workflows/system_jobs/
```

Agent modules can call workflow builders from `workflows/`, or each agent can own a small `workflow.py` file if the workflow is local to that agent.

Rule of thumb:

```text
If workflow is agent-specific, keep it inside that agent folder.
If workflow is shared/reused, place it under workflows/.
```

---

## Native Tools

Internal Agent Server tools should be native Python tools, not MCP tools.

Tool flow:

```text
agent/workflow
  -> native Python tool
  -> Backend gRPC client
  -> Backend capability
```

Tools should not access Backend database tables directly.

Recommended structure:

```text
tools/
  __init__.py
  registry.py
  backend/
    __init__.py
    user_tools.py
    schedule_tools.py
    plan_tools.py
    graph_tools.py
    analytics_tools.py
```

Possible tools:

```text
get_user_profile
update_user_profile
get_current_schedule
save_availability
create_plan_feedback
search_graph
suggest_knowledge_card
emit_analytics_event
```

---

## Backend Client

Backend communication should be isolated behind a client.

Recommended structure:

```text
clients/
  __init__.py
  backend_grpc.py
```

Later generated protobuf code can live under a generated directory, but it should not leak into every agent module.

Agent modules should call tools.

Tools should call `backend_grpc.py`.

---

## LLM Provider Layer

The Agent Server should not call the provider directly from agents.

Recommended structure:

```text
llm/
  __init__.py
  provider_client.py
  provider_pool.py
  slot_router.py
  task_cache.py
```

### provider_client.py

Low-level adapter for the concrete LLM provider.

Responsible for provider-specific request/response shape.

### provider_pool.py

Manages multiple provider slots/API keys.

If there are four keys, the pool can expose four execution slots.

Conceptual model:

```text
slot 1 -> API_KEY_1
slot 2 -> API_KEY_2
slot 3 -> API_KEY_3
slot 4 -> API_KEY_4
```

### slot_router.py

Chooses which slot to use for a given request.

Possible policies:

```text
round_robin
priority
user_affinity
agent_type_affinity
```

Recommended first policy:

```text
priority + round_robin
```

Possible future policy:

```text
slot = hash(business_user_id) % slot_count
```

This may help provider-side cache affinity, but it can also create uneven load.

### task_cache.py

Optional Redis-backed or in-memory cache for safe deterministic tasks.

Good candidates:

```text
source relevance classification
text summarization by text hash
tag extraction
note classification
```

Bad candidates:

```text
normal conversational turns
dynamic multi-turn user responses
tool-using agent runs
```

---

## Provider Slot Priorities

Interactive user requests should not be blocked by long system jobs.

Recommended priority model:

```text
highest:
  /agent/turn

medium:
  /llm/task

lowest:
  /agent/jobs/run
```

If system jobs are long, they should use background execution or lower-priority slots.

---

## Security Layer

Security should be a separate layer, not scattered across agents.

Recommended structure:

```text
security/
  __init__.py
  input_guard.py
  output_guard.py
  tool_permissions.py
```

### input_guard.py

Runs before LLM call.

Checks for obvious malicious or unsafe input patterns:

```text
"ignore previous instructions"
"show system prompt"
"give me API keys"
"print secrets"
```

This is useful but not sufficient.

### output_guard.py

Runs after LLM call.

Prevents returning:

```text
secrets
internal prompts
raw tool errors
stack traces
internal implementation details
```

### tool_permissions.py

Most important part of security.

Defines which tools are available for each:

```text
endpoint
agent
mode
user/system request type
```

Example:

```text
profile_setup_agent:
  can update user profile/preferences

schedule_setup_agent:
  can read/write schedule availability

notes_capture_agent:
  can create plan feedback and graph note candidates

default_assistant_agent:
  limited writes unless confirmation exists

llm/task:
  no tools by default

system jobs:
  explicit tools per job type
```

Important principle:

```text
Do not rely only on prompt instructions.
Limit what the model is technically allowed to do.
```

---

## Tracing and Run Context

Recommended structure:

```text
tracing/
  __init__.py
  context.py
  spans.py
```

Every request should have:

```text
correlation_id
business_user_id
session_id
agent_run_id
request_type
agent_name
provider_slot_id
```

Trace metadata should propagate to Backend gRPC calls.

Potential systems:

```text
OpenTelemetry / Jaeger for distributed system tracing
LangSmith for LLM/agent traces
```

The two should be correlated with metadata:

```text
correlation_id
agent_run_id
otel_trace_id
langsmith_run_id
```

---

## Schemas

Recommended structure:

```text
schemas/
  __init__.py
  agent_turn.py
  llm_task.py
  jobs.py
  messages.py
```

### agent_turn.py

DTOs for:

```text
POST /agent/turn request
POST /agent/turn response
agent mode
channel
metadata
```

### llm_task.py

DTOs for one-shot LLM task requests/responses.

### jobs.py

DTOs for system agent jobs.

### messages.py

Common message DTOs:

```text
role
content
created_at
metadata
```

---

## Application Layer

Recommended structure:

```text
application/
  __init__.py
  run_agent_turn.py
  run_llm_task.py
  run_system_job.py
```

Application layer responsibilities:

```text
validate request
create run context
invoke security guards
select agent/workflow
control tool permissions
call LLM/tool layer
normalize response
```

Application layer should not contain provider-specific low-level code.

---

## Entrypoints

Recommended structure:

```text
entrypoints/
  __init__.py
  fastapi.py
  routes_agent.py
  routes_llm.py
  routes_jobs.py
```

### fastapi.py

Creates FastAPI app and includes routers.

### routes_agent.py

Defines:

```text
POST /agent/turn
```

### routes_llm.py

Defines:

```text
POST /llm/task
```

### routes_jobs.py

Defines:

```text
POST /agent/jobs/run
```

Routes should stay thin and delegate to application services.

---

## Proposed Directory Tree

```text
services/agent/
  src/
    agent/
      __init__.py
      main.py
      settings.py

      entrypoints/
        __init__.py
        fastapi.py
        routes_agent.py
        routes_llm.py
        routes_jobs.py

      application/
        __init__.py
        run_agent_turn.py
        run_llm_task.py
        run_system_job.py

      agents/
        __init__.py

        router_agent/
          __init__.py
          definition.py
          prompts.py
          schemas.py
          workflow.py

        default_assistant_agent/
          __init__.py
          definition.py
          prompts.py
          schemas.py
          workflow.py
          tools.py

        profile_setup_agent/
          __init__.py
          definition.py
          prompts.py
          schemas.py
          workflow.py
          tools.py

        schedule_setup_agent/
          __init__.py
          definition.py
          prompts.py
          schemas.py
          workflow.py
          tools.py

        notes_capture_agent/
          __init__.py
          definition.py
          prompts.py
          schemas.py
          workflow.py
          tools.py

        system/
          __init__.py

          profile_reflection_agent/
            __init__.py
            definition.py
            prompts.py
            schemas.py
            workflow.py
            tools.py

          graph_update_agent/
            __init__.py
            definition.py
            prompts.py
            schemas.py
            workflow.py
            tools.py

      workflows/
        __init__.py
        common/
          __init__.py

      tools/
        __init__.py
        registry.py
        backend/
          __init__.py
          user_tools.py
          schedule_tools.py
          plan_tools.py
          graph_tools.py
          analytics_tools.py

      clients/
        __init__.py
        backend_grpc.py

      llm/
        __init__.py
        provider_client.py
        provider_pool.py
        slot_router.py
        task_cache.py

      security/
        __init__.py
        input_guard.py
        output_guard.py
        tool_permissions.py

      schemas/
        __init__.py
        agent_turn.py
        llm_task.py
        jobs.py
        messages.py

      tracing/
        __init__.py
        context.py
        spans.py
```

---

## Initial Implementation Order

Recommended order later:

```text
1. FastAPI app and health endpoint.
2. /llm/task with one trivial task.
3. LLM provider client.
4. Provider pool with slots.
5. /agent/turn with default_assistant_agent.
6. Telegram Gateway integration.
7. Backend gRPC client skeleton.
8. Tool registry and first backend tool.
9. profile_setup_agent.
10. schedule_setup_agent.
11. notes_capture_agent.
12. system jobs endpoint.
13. profile_reflection_agent.
14. graph_update_agent.
```

This order keeps the system testable while preserving the intended architecture.

---

## Current Conclusion

The Agent Server should be a FastAPI reasoning/runtime service with three main surfaces:

```text
POST /agent/turn
POST /llm/task
POST /agent/jobs/run
```

Internally it should be organized around explicit agent packages, not single large files.

The important architecture rules are:

```text
Agent Server stays stateless per Telegram turn.
Telegram Gateway provides conversation history.
Backend remains the canonical domain state.
Agent tools are native Python tools.
Tools call Backend through gRPC.
MCP is not used internally.
LLM provider access goes through provider pool and slots.
Security is implemented through guards and tool permissions.
```
