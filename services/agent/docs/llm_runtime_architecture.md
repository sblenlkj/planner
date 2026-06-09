# Agent LLM Runtime Module

Этот модуль вводит единую точку доступа к LLM внутри `agent` сервиса.

Главная идея: агенты, LangGraph workflows и фоновые batch workers не работают с GigaChat/LangChain напрямую. Они получают доступ к LLM через `LlmOrchestrator`.

```text
Agent / LangGraph / Background worker
  → LlmOrchestrator
    → LlmProviderPool
      → LlmSession
        → LlmSlot
          → LlmProviderPort
            → GigaChatProvider
```

## Основные решения

### 1. Session-first model

LLM slot резервируется не только на один provider call, а на весь execution scope.

Execution scope может быть:

- `ONE_SHOT` — один короткий вызов `complete()`;
- `AGENT_RUN` — один интерактивный запуск агента;
- `WORKFLOW_RUN` — один LangGraph workflow;
- `BATCH_DRAIN` — один homogeneous batch chunk.

Это значит:

```text
agent starts
  acquire LlmSession
  use the same reserved provider slot for all model calls
  call backend tools over local gRPC
  produce final answer
  release LlmSession
agent ends
```

### 2. Slot is an exclusive provider runtime

`LlmSlot` — это не просто API key. Это:

```text
provider credential
provider client
model config
concurrency permit = 1
workload group
```

Если у команды 5 ключей GigaChat, можно создать 5 слотов.

### 3. Workload capacity

Слоты можно разделить по workload classes:

```text
interactive: key_1, key_2, key_3
background/graph_update: key_4, key_5
```

Для первой версии это проще и надёжнее, чем динамический scheduler.

### 4. Provider is hidden behind a port

`LlmOrchestrator` зависит от `LlmProviderPort`, а не от GigaChat или LangChain.

```python
class LlmProviderPort(Protocol):
    async def complete(self, request: LlmRequest) -> LlmResponse:
        ...
```

GigaChat/LangChain детали изолированы в:

```text
src/agent/llm/adapters/gigachat.py
```

## Файлы модуля

```text
src/agent/llm/
├── __init__.py
├── models.py          # DTO, workload, execution scope, request/response
├── ports.py           # provider protocols
├── errors.py          # runtime exceptions
├── slot.py            # LlmSlot
├── session.py         # LlmSession / reserved lease
├── pool.py            # in-process slot pool
├── orchestrator.py    # public entry point
├── adapters/
│   ├── __init__.py
│   └── gigachat.py    # LangChain GigaChat adapter
└── testing/
    ├── __init__.py
    └── fake_provider.py
```

## Bootstrap example

```python
import os

from agent.llm import LlmOrchestrator, LlmProviderPool, LlmSlot, LlmWorkload
from agent.llm.adapters import GigaChatProvider, GigaChatProviderConfig


def build_llm_orchestrator() -> LlmOrchestrator:
    interactive_credentials = [
        os.environ["GIGACHAT_CREDENTIALS_1"],
        os.environ["GIGACHAT_CREDENTIALS_2"],
        os.environ["GIGACHAT_CREDENTIALS_3"],
    ]
    background_credentials = [
        os.environ["GIGACHAT_CREDENTIALS_4"],
        os.environ["GIGACHAT_CREDENTIALS_5"],
    ]

    slots: list[LlmSlot] = []

    for index, credentials in enumerate(interactive_credentials, start=1):
        provider = GigaChatProvider(
            GigaChatProviderConfig(
                credentials=credentials,
                scope="GIGACHAT_API_PERS",
                model="GigaChat-Pro",
                verify_ssl_certs=False,
            )
        )
        slots.append(
            LlmSlot(
                slot_id=f"interactive-{index}",
                provider=provider,
                workloads={LlmWorkload.INTERACTIVE},
            )
        )

    for index, credentials in enumerate(background_credentials, start=1):
        provider = GigaChatProvider(
            GigaChatProviderConfig(
                credentials=credentials,
                scope="GIGACHAT_API_PERS",
                model="GigaChat-Pro",
                verify_ssl_certs=False,
            )
        )
        slots.append(
            LlmSlot(
                slot_id=f"background-{index}",
                provider=provider,
                workloads={LlmWorkload.BACKGROUND, LlmWorkload.GRAPH_UPDATE},
            )
        )

    return LlmOrchestrator(
        LlmProviderPool(slots, acquire_timeout_seconds=30.0)
    )
```

## FastAPI lifespan example

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from agent.bootstrap_llm import build_llm_orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm_orchestrator = build_llm_orchestrator()
    yield


app = FastAPI(lifespan=lifespan)
```

Important: this pool is in-process. Do not run it with multiple Uvicorn worker processes unless you replace the pool with Redis/Postgres distributed leases.

```bash
uvicorn agent.main:app --workers 1
```

## One-shot complete example

```python
from agent.llm import LlmMessage, LlmRequest, LlmWorkload

response = await llm_orchestrator.complete(
    LlmRequest(
        messages=[
            LlmMessage(role="system", content="Ты краткий ассистент."),
            LlmMessage(role="user", content="Ответь одной фразой: API работает?"),
        ]
    ),
    workload=LlmWorkload.INTERACTIVE,
    purpose="smoke_test",
    prompt_template="smoke_test_v1",
)

print(response.content)
```

## LangGraph / LangChain agent run example

Идея: агент получает `LlmSession`, а не ключ и не GigaChat client напрямую.

```python
from agent.llm import LlmExecutionScope, LlmWorkload


async def run_default_assistant_turn(state, tools, llm_orchestrator):
    async with llm_orchestrator.session(
        workload=LlmWorkload.INTERACTIVE,
        scope=LlmExecutionScope.AGENT_RUN,
        purpose="default_assistant_turn",
        prompt_template="default_assistant_agent_v1",
        max_duration_seconds=180,
    ) as session:
        chat_model = session.require_langchain_chat_model()

        graph = build_default_assistant_graph(
            llm=chat_model,
            tools=tools,
        )

        return await graph.ainvoke(state)
```

## Batch drain example

Для `observation → user graph update` можно держать одну session на homogeneous batch chunk.

```python
from agent.llm import LlmExecutionScope, LlmWorkload


async def drain_user_graph_batch(user_batches, llm_orchestrator, graph_tools):
    async with llm_orchestrator.session(
        workload=LlmWorkload.GRAPH_UPDATE,
        scope=LlmExecutionScope.BATCH_DRAIN,
        purpose="user_graph_update_batch",
        prompt_template="graph_update_agent_v1",
        max_duration_seconds=600,
        metadata={"items": len(user_batches)},
    ) as session:
        graph_update_agent = build_graph_update_agent(
            llm=session.require_langchain_chat_model(),
            tools=graph_tools,
        )

        results = []
        for user_batch in user_batches:
            result = await graph_update_agent.ainvoke(
                {
                    "user_id": user_batch.user_id,
                    "observations": user_batch.observations,
                    "current_graph": user_batch.current_graph,
                }
            )
            results.append(result)

        return results
```

Почему это выгодно:

```text
same provider slot
same agent definition
same system prompt
same tool definitions
same output schema
many dynamic user payloads
```

Это повышает prompt-cache locality у провайдера, если он поддерживает кэширование повторяющегося prefix.

## Safety limits

Даже при локальном быстром backend/gRPC стоит держать защитные лимиты:

- `max_duration_seconds` на session;
- `max_agent_steps` внутри LangGraph/LangChain agent;
- timeout на backend tools;
- timeout на provider calls;
- bounded queues;
- workload-specific capacity.

## Current limitations

- Pool is in-memory and intended for one FastAPI process.
- No distributed lease yet.
- No retry/cooldown policy except slot-level placeholder.
- No streaming API yet.
- `LlmToolSpec` is a placeholder for future provider-neutral tools; LangGraph agents should bind LangChain tools directly to the reserved chat model.
