# Planner

Planner — это multi-service платформа персонального помощника для планирования, обучения, задач, напоминаний и личной эффективности.

Проект начинался как идея личного ассистента, который помогает пользователю управлять задачами, сроками и продуктивностью. В текущей реализации фокус сделан на агентской архитектуре: пользователь пишет обычным языком, Agent Service интерпретирует намерение, вызывает типизированные tools, а Backend сохраняет изменения в доменной модели.

Это не просто чат-бот. Planner демонстрирует production-like подход к LLM-приложению:

```text
Telegram Gateway
  -> Agent Service
      -> LLM Agent / LangGraph Workflow
      -> Backend HTTP adapters
          -> Backend contexts
              -> Postgres
```

## Что умеет проект

В текущем MVP пользователь может через агента:

- создавать учебные курсы;
- добавлять задачи в курс;
- читать детали курса;
- создавать напоминания;
- создавать дедлайны;
- сохранять наблюдения о пользователе;
- сохранять контекст на конкретные даты;
- закрывать сессию и запускать workflow, который создает итоговое наблюдение дня.

Примеры пользовательских запросов:

```text
Создай курс Python для backend-разработки.

Добавь в этот курс задачу разобрать async context managers.

Напомни завтра в 10:00 повторить FastAPI dependency injection.

Запомни, что я лучше учусь маленькими практическими задачами.

Завтра у меня мало времени на учебу, максимум один час вечером.
```

Agent Service превращает такие сообщения в конкретные backend operations через tools.

## Архитектура

Проект состоит из трех основных сервисов:

```text
services/
  backend/
  agent/
  telegram-gateway/
```

Также в корне проекта используется `docker-compose.yml` для инфраструктуры: Postgres и Redis.

## Backend

Backend — основной сервис доменной модели Planner.

Он отвечает за:

- пользователей;
- курсы;
- задачи курса;
- напоминания;
- дедлайны;
- schedule observations;
- analytics observations;
- runtime jobs;
- внутренние HTTP endpoint'ы для Agent Service и Telegram Gateway.

Backend построен как модульный монолит вокруг собственного фреймворка **Direttore**. Direttore используется для command/query/event handlers, Unit of Work coordination и связки bounded contexts.

Важная идея: даже если решение принимает агент, он не пишет напрямую в базу. Агент вызывает backend API, а Backend уже исполняет доменные use cases.

Подробнее: `services/backend/README.md`.

## Telegram Gateway

Telegram Gateway — транспортный шлюз между внутренней системой и Telegram.

Он отвечает за:

- привязку `business_user_id` к Telegram user/chat;
- отправку сообщений пользователю в Telegram;
- хранение активной conversation session в Redis;
- передачу сообщений в Agent Service;
- передачу закрытой сессии в workflow Agent Service.

Telegram Gateway не владеет бизнес-логикой. Он знает только transport-level информацию: Telegram ID, Telegram Chat ID и текущую Redis-сессию.

Активная сессия хранится в Redis примерно так:

```text
telegram_gateway:session:{business_user_id}
```

Сессия содержит список сообщений:

```json
[
  {
    "role": "user",
    "content": "..."
  },
  {
    "role": "assistant",
    "content": "..."
  }
]
```

Подробнее: `services/telegram-gateway/README.md`.

## Agent Service

Agent Service — центральная агентская часть проекта.

Он отвечает за:

- запуск conversational agent;
- загрузку пользовательского контекста из Backend;
- регистрацию и исполнение tools;
- запуск workflow;
- LLM slot pool;
- Langfuse observability;
- input guard;
- внутренние endpoints для Gateway и runtime-сценариев.

Agent Service не хранит основную доменную модель и не является session storage. Он получает сообщения от Telegram Gateway, загружает актуальный контекст пользователя из Backend и решает, какой tool или workflow нужно запустить.

Подробнее: `services/agent/README.md`.

## Основной flow сообщения

Обычное сообщение пользователя проходит такой путь:

```text
1. Пользователь отправляет сообщение через Telegram Gateway.
2. Gateway достает текущую Redis-сессию.
3. Gateway отправляет историю сообщений в Agent Service.
4. Agent Service проверяет security/input guard.
5. Agent Service загружает planner context пользователя из Backend.
6. Agent Service получает LLM slot.
7. Agent запускается с набором tools.
8. Если нужно, agent вызывает один или несколько tools.
9. Tools обращаются к Backend через HTTP adapters.
10. Backend исполняет доменные use cases.
11. Agent Service возвращает assistant_text.
12. Gateway сохраняет user/assistant messages в Redis-сессию.
13. Gateway отправляет ответ пользователю.
```

Пример сложного агентского поведения:

```text
Пользователь:
Создай курс Python для backend-разработки и добавь туда задачу разобрать async context managers.

Agent:
1. вызывает create_course;
2. получает course_id;
3. вызывает create_course_task с этим course_id;
4. возвращает пользователю итоговый ответ.
```

## Tools агента

Tools — это тонкий agent-facing слой над backend adapters. Они не работают с базой данных напрямую.

В текущем MVP есть tools для:

- создания курса;
- создания задачи курса;
- чтения деталей курса;
- создания наблюдения по курсу;
- создания напоминания;
- создания дедлайна;
- создания date observation;
- сохранения долговременного наблюдения о пользователе.

Tools позволяют LLM быть не просто генератором текста, а orchestration layer над доменной системой.

## Workflow

В проекте есть отдельный `session-close` workflow.

Он запускается при закрытии пользовательской сессии:

```text
POST /internal/workflows/session-close/run
```

Зачем он нужен:

- interactive agent хорошо подходит для прямых команд пользователя;
- но анализ всей сессии лучше делать отдельным bounded workflow;
- workflow не отвечает пользователю;
- workflow делает одну контролируемую постобработку;
- workflow помогает избежать дублей в observations.

Пример:

```text
Сегодня я учил Python.
Потом разобрал FastAPI.
SQL не успел, перенесу на завтра.
```

Если сохранять day observation на каждом сообщении, получится несколько разрозненных записей. Поэтому session-close workflow анализирует весь transcript и создает одно итоговое `day observation`.

Граф workflow:

```text
START
  -> build_context
  -> call_llm
  -> save_day_observation
  -> END
```

LLM-ответ в workflow дополнительно проходит JSON parsing и Pydantic validation. Workflow не сохраняет произвольный текст модели напрямую.

## Почему одного агента недостаточно

В проекте разделены две категории LLM-логики:

```text
Agent
  -> интерактивные действия пользователя
  -> tool calling
  -> ответ пользователю

Workflow
  -> bounded post-processing
  -> работа с transcript
  -> один контролируемый side effect
  -> без прямого ответа пользователю
```

Это важное архитектурное решение. Не все нужно помещать внутрь conversational agent. Часть сценариев надежнее и понятнее делать отдельными workflow.

## Observability

Для Agent Service подключена observability через Langfuse.

В traces видно:

- LLM model calls;
- tool calls;
- входные параметры tools;
- результаты tools;
- LangGraph nodes;
- latency;
- token usage;
- workflow execution.

Это позволяет анализировать не только финальный текст ответа, но и фактическое поведение агента: какие tools были доступны, какие были вызваны и какие данные изменились.

Также в Agent Service предусмотрены runtime/slot-level метрики. Они больше относятся к техническому слою LLM runtime: занятость слотов, выбранный тип модели, успешность вызовов и observability вокруг исполнения.

## Security

Перед передачей пользовательского сообщения в LLM Agent Service выполняет input guard.

Он блокирует:

- попытки prompt injection;
- просьбы игнорировать системные инструкции;
- просьбы раскрыть system prompt;
- пользовательские UUID-like строки.

Модель безопасности:

```text
UUID, который написал пользователь -> blocked
UUID из system context или tool result -> allowed
Backend domain rules -> final validation
```

Это позволяет агенту использовать внутренние идентификаторы, которые пришли из доверенного контекста, но не позволяет пользователю вручную подставлять чужие id.

## Запуск проекта

Сначала нужно поднять инфраструктуру из корня проекта:

```bash
docker compose up -d postgres redis
```

Затем для каждого сервиса выполнить `uv sync`, а потом запустить сервис.

### Backend

```bash
cd services/backend
uv sync
uv run backend
```

### Telegram Gateway

```bash
cd services/telegram-gateway
uv sync
uv run telegram-gateway
```

### Agent Service

```bash
cd services/agent
uv sync
uv run agent
```

## Swagger endpoints

После запуска сервисов Swagger обычно доступен по локальным адресам сервисов:

```text
Backend:          http://localhost:8001/docs
Agent Service:    http://localhost:8002/docs
Telegram Gateway: http://localhost:8000/docs
```

Порты могут отличаться в зависимости от локальных настроек.

## Типичный локальный demo-flow

1. Поднять Postgres и Redis.
2. Запустить Backend.
3. Запустить Agent Service.
4. Запустить Telegram Gateway.
5. Создать пользователя в Backend.
6. Привязать пользователя к Telegram Gateway через `/telegram/attach`.
7. Отправить сообщение в `/agent/message`.
8. Посмотреть ответ агента.
9. Проверить Backend state.
10. Проверить Langfuse trace.
11. Закрыть сессию через `/agent/session/close`.
12. Проверить, что session-close workflow создал `day observation`.

## Что уже проверено

В MVP проверены сценарии:

- создание курса через агента;
- создание задачи курса после создания курса;
- чтение деталей курса;
- запуск session-close workflow;
- сохранение day observation через workflow;
- хранение conversation session в Redis;
- security block для подозрительного пользовательского ввода;
- Langfuse tracing для agent и workflow.

## Roadmap - что не успелось...

Ближайшие направления развития:

- усилить routing rules для tools;
- добавить больше read/update tools;
- доработать morning briefing workflow;
- вернуть полноценный Telegram webhook-flow в стабильном окружении;
- расширить runtime jobs;
- добавить больше пользовательских метрик и аналитики;
- подключить дополнительные внешние connectors.

Morning briefing workflow планировался как следующий bounded workflow: утром собирать контекст пользователя, ближайшие дедлайны, reminders, observations и формировать короткое сообщение на день.

## Почему проект интересен

Planner показывает, что LLM-приложение может быть не просто чат-интерфейсом.

В проекте есть:

- сервисные границы;
- модульный backend;
- Telegram transport layer;
- Redis session storage;
- LLM agent;
- typed tools;
- HTTP adapters;
- LangGraph workflow;
- Langfuse observability;
- security/input guard;
- доменная модель для курсов, задач, расписания и наблюдений.

Главная идея: LLM используется как orchestration layer, а не как место хранения бизнес-логики. Данные и правила остаются в Backend, транспорт — в Telegram Gateway, агентская логика — в Agent Service.

Такой подход делает проект ближе к реальной production architecture и показывает, как можно строить расширяемую агентскую систему поверх обычных backend-сервисов.
