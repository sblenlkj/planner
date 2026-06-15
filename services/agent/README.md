# Planner Agent Service

Agent Service — это отдельный сервис платформы Planner, который отвечает за LLM-логику, агентские сценарии, workflow и обращение к backend-контекстам через HTTP-адаптеры.

Сервис не хранит основную доменную модель сам. Его задача — принять пользовательскую сессию от Telegram Gateway, загрузить актуальный контекст пользователя из Backend, вызвать LLM-агента или workflow и выполнить нужные доменные действия через backend API.

## Зачем нужен Agent Service

В проекте Planner агент — это не просто чат-бот. Это слой оркестрации между естественным языком пользователя и доменной моделью приложения.

Пользователь пишет обычным языком:

```text
Создай курс Python для backend-разработки.
Добавь туда задачу разобрать async context managers.
Напомни завтра повторить FastAPI.
Запомни, что я лучше учусь маленькими практическими задачами.
Завтра у меня мало времени на учебу.
```

Agent Service преобразует такие запросы в вызовы конкретных backend-контекстов: Course, Schedule, Analytics, User. За счет этого LLM не работает напрямую с базой данных и не содержит бизнес-логику внутри себя. Она выбирает подходящий инструмент, а реальные изменения выполняются через типизированные порты и HTTP-адаптеры.

## Место сервиса в архитектуре

Общий поток выглядит так:

```text
Telegram Gateway
  -> Agent Service
      -> LLM Agent / Workflow
      -> Backend HTTP adapters
          -> Backend contexts
```

Telegram Gateway отвечает за Telegram-интеграцию, хранение активной conversation session и привязку Telegram-пользователя к business user id.

Agent Service отвечает за:

- запуск conversational agent;
- загрузку пользовательского контекста перед ответом;
- регистрацию и исполнение tools;
- запуск workflow;
- работу с LLM slot pool;
- трассировку LLM-вызовов и tool calls;
- валидацию пользовательского ввода перед передачей в LLM.

Backend отвечает за доменную модель, persistence и бизнес-операции.

## Запуск

Из директории `services/agent`:

```bash
uv run agent
```

После запуска сервис поднимает FastAPI-приложение и регистрирует internal endpoints для Telegram Gateway и внутренних workflow.

## Основные endpoints

### Conversation agent

```http
POST /internal/conversations/respond
```

Используется Telegram Gateway для отправки активной conversation session в Agent Service.

На вход приходит история сообщений, а business user id передается через internal header. Agent Service:

1. проверяет internal token;
2. проверяет пользовательский ввод через input guard;
3. загружает контекст пользователя из Backend;
4. получает LLM slot;
5. создает LangChain/LangGraph agent;
6. регистрирует tools;
7. запускает агента;
8. возвращает `assistant_text`.

### Session close workflow

```http
POST /internal/workflows/session-close/run
```

Используется при закрытии пользовательской сессии.

Этот workflow читает transcript сессии и формирует одно итоговое наблюдение о дне пользователя. Если в сессии есть полезные факты о том, что пользователь делал, изучал, планировал или не успел сделать, workflow создает `schedule day observation` в Backend.

### Morning briefing workflow

```http
POST /internal/workflows/morning-briefing/run
```

Заготовка для утреннего workflow. Идея — запускать отдельный сценарий утром, чтобы подготовить сообщение пользователю на основе его контекста, расписания и наблюдений.

В текущем MVP основной рабочий workflow — `session-close`.

## Conversation session

Активная conversation session хранится в Telegram Gateway. Agent Service не является session storage.

Это сделано осознанно:

- Telegram Gateway знает Telegram chat/user;
- Gateway управляет открытием и закрытием пользовательской сессии;
- Agent Service получает уже собранную историю сообщений;
- Agent Service остается stateless относительно Telegram-сессии.

При обычном сообщении Gateway передает историю сообщений в `/internal/conversations/respond`. Если Agent Service успешно обработал запрос, Gateway сохраняет user message и assistant response в session storage.

Если input guard блокирует сообщение, Agent Service возвращает ошибку, и Gateway не должен добавлять это сообщение в активную сессию.

## Security и input guard

Перед запуском LLM Agent Service проверяет последнее сообщение пользователя.

Input guard блокирует:

- попытки prompt injection;
- просьбы игнорировать системные правила;
- просьбы раскрыть системный prompt;
- пользовательские строки, похожие на UUID.

Это важно, потому что LLM может работать с UUID, которые были получены из trusted context или из результатов tools, но пользователь не должен вручную передавать внутренние идентификаторы и просить достать чужие данные.

Модель безопасности:

```text
user-supplied UUID -> blocked
system/tool UUID -> allowed
backend ownership/business rules -> final validation
```

## LLM runtime

Agent Service использует LLM slot pool.

Это позволяет централизованно управлять LLM-клиентами, выбирать тип модели и контролировать доступ к LLM runtime. В текущем MVP для основного агента и workflow используется сильная модель.

LLM-вызовы и tool calls трассируются через Langfuse. В trace видно:

- model calls;
- tool calls;
- LangGraph nodes;
- latency;
- token usage;
- результат выполнения tools.

Это делает поведение агента наблюдаемым и пригодным для демонстрации.

## Main conversational agent

Основной агент создается через современный LangChain agent runtime, который работает поверх LangGraph.

Агент получает:

- LLM model из slot pool;
- system context;
- историю сообщений;
- список tools;
- загруженный planner context пользователя.

Он не содержит бизнес-логику напрямую. Его задача — понять намерение пользователя и выбрать нужный tool.

Например, пользователь может попросить:

```text
Создай курс Python для backend-разработки и добавь туда задачу разобрать async context managers.
```

Агент может выполнить два tool call подряд:

1. `create_course`
2. `create_course_task`

При этом `create_course_task` использует `course_id`, который вернул предыдущий tool call.

## Tools агента

Tools — это тонкий agent-facing слой над backend adapters. Они не работают с базой данных напрямую. Каждый tool вызывает соответствующий application port, а port реализован HTTP-адаптером к Backend.

В текущем MVP предусмотрены следующие tools.

### create_course

Создает новый курс пользователя.

Пример пользовательского намерения:

```text
Создай курс Python для backend-разработки.
```

Backend context: Course.

### create_course_task

Создает задачу внутри существующего курса.

Tool принимает `course_id`, полученный из системного контекста или результата `create_course`.

Пример:

```text
Добавь в этот курс задачу разобрать async context managers.
```

Backend context: Course.

### read_course_details

Читает подробности курса: задачи и наблюдения.

Пример:

```text
Покажи детали курса Python.
```

Backend context: Course.

### create_course_observation

Сохраняет наблюдение по курсу: прогресс, сложность, заметку или важный факт.

Пример:

```text
Запомни по этому курсу, что мне сложно дается async programming.
```

Backend context: Course.

### create_reminder

Создает напоминание.

Пример:

```text
Напомни завтра в 10:00 повторить FastAPI dependency injection.
```

Backend context: Schedule.

### create_deadline

Создает дедлайн.

Пример:

```text
Поставь дедлайн до пятницы закончить первую часть курса.
```

Backend context: Schedule.

### create_date_observation

Сохраняет контекст или ограничение на конкретную дату/период.

Пример:

```text
Запомни, что завтра у меня мало времени на учебу, максимум один час вечером.
```

Backend context: Schedule.

### remember_user_observation

Сохраняет долговременное наблюдение о пользователе.

Пример:

```text
Запомни, что я лучше учусь маленькими практическими задачами, а не длинной теорией.
```

Backend context: Analytics.

## Backend adapters

Agent Service ходит в Backend по HTTP.

Внутри Agent Service есть application ports и infrastructure adapters:

```text
application/ports
  -> CourseContextPort
  -> ScheduleContextPort
  -> AnalyticsContextPort
  -> UserContextPort

infrastructure/backend
  -> HTTP adapters
  -> BackendHttpClient
  -> backend settings
```

Это позволяет не привязывать agent logic к конкретной реализации Backend API. Agent и workflow используют порты, а не прямые HTTP-запросы.

## Agent context loading

Перед каждым запуском conversational agent сервис загружает planner context пользователя.

В context входят:

- профиль пользователя;
- курсы;
- активные observations;
- commitments;
- date observations на ближайшие даты;
- другая минимально нужная информация для принятия решения агентом.

Это важно, потому что агент не должен каждый раз начинать с пустого состояния. Он получает срез доменной картины пользователя и может принимать решения на основе уже существующих данных.

## Session close workflow

Session close workflow — отдельный LangGraph workflow.

Он нужен потому, что не каждую задачу стоит решать interactive agent-ом. Interactive agent отвечает пользователю и выполняет явные команды. Но есть фоновые задачи, которые лучше выполнять после завершения сессии.

Пример: пользователь в течение дня пишет:

```text
Сегодня я учил Python.
Потом разобрал FastAPI.
SQL не успел, перенесу на завтра.
```

Если interactive agent будет сохранять day observation на каждом сообщении, появятся дубли и разрозненные записи. Поэтому session close workflow агрегирует всю сессию и создает одно итоговое наблюдение дня.

Workflow устроен как граф:

```text
START
  -> build_context
  -> call_llm
  -> save_day_observation
  -> END
```

### build_context

Собирает prompt и transcript сессии для LLM.

### call_llm

Просит LLM извлечь краткое итоговое наблюдение о дне пользователя.

Результат проходит через JSON parsing и Pydantic validation. Workflow не сохраняет произвольный текст модели напрямую.

### save_day_observation

Если извлечение показало, что в сессии есть полезная информация, workflow вызывает Schedule backend context и создает `day observation`.

## Почему одного агента недостаточно

Основной агент хорошо подходит для интерактивных команд:

- создать курс;
- добавить задачу;
- создать напоминание;
- сохранить предпочтение;
- прочитать детали курса.

Но workflow лучше подходит для bounded post-processing задач:

- обработать всю сессию целиком;
- сделать итоговую агрегацию;
- не отвечать пользователю;
- выполнить один контролируемый side effect;
- избежать дублей.

Поэтому в сервисе есть оба механизма:

```text
Agent -> interactive user-facing actions
Workflow -> bounded background/post-processing logic
```

Такое разделение делает систему понятнее и надежнее.

## Observability

Сервис интегрирован с Langfuse.

В trace можно увидеть:

- вызов основного агента;
- какие tools были доступны;
- какие tools были реально вызваны;
- вход и выход tool call;
- latency model calls;
- token usage;
- LangGraph workflow nodes;
- результат session-close workflow.

Это особенно важно для агентской системы, потому что качество агента определяется не только финальным текстом, но и тем, какие инструменты он выбрал, какие данные изменил и сколько стоил запуск.

## Что уже работает в MVP

На текущем этапе реализован вертикальный slice:

```text
Telegram Gateway
  -> Agent Service
  -> LangChain/LangGraph Agent
  -> Tool calls
  -> Backend contexts
  -> Langfuse tracing
```

Проверены сценарии:

- создание курса;
- создание задачи курса после создания курса;
- чтение деталей курса;
- session-close workflow;
- сохранение day observation через workflow;
- security block для подозрительного пользовательского ввода.

## Что планировалось дальше

В планах было добавить еще один workflow для утреннего сценария: morning briefing.

Идея этого workflow — утром собирать контекст пользователя, ближайшие ограничения, напоминания, дедлайны и формировать краткое стартовое сообщение на день.

До текущего дедлайна основной фокус был сделан на рабочем conversational agent и session-close workflow, потому что они лучше демонстрируют ключевую архитектуру: интерактивный агент + отдельный bounded workflow.

## Почему проект интересен

Главная идея Agent Service — показать, что агентская система — это не просто LLM-чат.

В этом сервисе агент:

- работает поверх доменных backend-контекстов;
- использует tools вместо прямого доступа к данным;
- получает контекст пользователя перед запуском;
- работает в рамках internal security;
- трассируется через Langfuse;
- дополняется workflow для задач, которые не должны жить внутри диалога.

Такой подход делает проект ближе к production architecture: LLM используется как orchestration layer, а не как место хранения бизнес-логики.
