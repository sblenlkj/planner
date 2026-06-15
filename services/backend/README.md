# Backend Service

Backend — это основной сервис модульного монолита Planner. Он хранит доменные данные, поднимает внутренние HTTP endpoint'ы для других сервисов и исполняет application use cases через собственный фреймворк **Direttore**.

Сервис не содержит агентов. Агентская логика живет отдельно в `services/agent`, а Telegram-интеграция — в `services/telegram-gateway`. Backend предоставляет им доменные операции: создать пользователя, напоминание, дедлайн, курс, наблюдение, прочитать данные и т.д.

## Статус проекта

Этот backend сейчас является одновременно рабочим сервисом и площадкой для практики архитектуры:

- часть доменов уже написана и подключена;
- часть доменов пока не используется в основном сценарии;
- некоторые endpoint'ы подняты, но еще не привязаны к агенту;
- некоторые более сложные идеи были спроектированы, но сейчас MVP сознательно сужен;
- часть старых решений была оставлена как кодовая база для экспериментов с Direttore.

Главный текущий фокус MVP: дать агентскому серверу простой внутренний API для пользователя, курсов, analytics observations, reminders/deadlines и schedule observations.

## Как запустить

Из директории backend-сервиса:

```bash
uv run backend
```

Перед запуском должен быть поднят Postgres. В корне проекта есть `docker-compose.yml` с Postgres и Redis.

Обычно достаточно:

```bash
docker compose up -d postgres redis
```

Затем:

```bash
cd services/backend
uv sync
uv run backend
```

По умолчанию сервис стартует на host/port из `backend/bootstrap/settings.py`.

## Основная структура

```text
services/backend/
  src/backend/
    main.py
    bootstrap/
    context/
    shared/
```

## `main.py`

Точка входа FastAPI-приложения.

Здесь создается приложение, подключаются routers, выполняется startup/lifespan-логика и запускается backend через `uv run backend`.

## `bootstrap/`

Сборка приложения и инфраструктуры:

- `settings.py` — настройки backend-сервиса;
- `direttore.py` — сборка Direttore application;
- `contexts.py` — регистрация backend-контекстов;
- `coordinator.py` — Unit of Work coordinator;
- `container.py` — DI/container wiring;
- `execution_dependencies.py` — execution-scoped зависимости для Direttore;
- `models.py` — импорт SQLAlchemy models всех контекстов, чтобы `Base.metadata` видел все таблицы.

## `shared/`

Общий слой backend-сервиса:

- `shared/adapters/persistence/base.py` — общий SQLAlchemy `Base`;
- `shared/auth/` — backend auth и access checking;
- `shared/application/ports/` — общие application ports;
- `shared/security/` — password hashing;
- `shared/logging.py` — logging helpers.

## Контексты

Код организован вокруг bounded contexts в `backend/context`.

Каждый полноценный контекст обычно имеет:

```text
domain/
application/
adapters/
```

Где:

- `domain` — entities, value objects и доменные правила;
- `application` — commands, queries, handlers, ports, orchestration;
- `adapters` — inbound/outbound адаптеры: HTTP, SQLAlchemy repositories, in-process facades.

## User context

Пользовательский контекст.

Отвечает за:

- создание пользователя;
- аутентификацию;
- базовые user preferences;
- UTC offset;
- runtime status пользователя.

Используется backend'ом и другими контекстами, например schedule при создании reminders должен получить UTC offset пользователя.

## Course context

Контекст курсов и учебных задач.

Отвечает за:

- создание курса;
- чтение курсов;
- создание course task;
- обновление статусов;
- course/course-task observations.

В MVP используется агентом как простая долгосрочная структура целей и задач пользователя.

## Schedule context

Самый большой и экспериментальный контекст.

В нем были спроектированы:

- commitments: reminders/deadlines;
- template: weekly schedule template;
- execution: конкретные дни, activities, observations.

Для текущего MVP большая часть template/execution не является основной. Сейчас важнее:

- создать reminder;
- создать deadline;
- прочитать commitments;
- создать date observation;
- создать day observation;
- прочитать observations.

Некоторые более сложные use cases и queries остаются в коде как база для дальнейшего расширения.

## Analytics context

Контекст пользовательских observations/insights.

Используется для хранения компактных знаний о пользователе:

- коммуникационные предпочтения;
- продуктивность;
- обучение;
- устойчивые наблюдения.

В MVP может использоваться агентом как простая память о пользователе.

## Runtime context

Технический runtime-контекст.

Отвечает за системные операции:

- API scheduler;
- восстановление future reminders;
- runtime jobs;
- интеграцию с Telegram Gateway;
- интеграцию с agent server;
- дневные и утренние фоновые операции.

Часть runtime-логики сейчас используется как инфраструктурный слой, а не как бизнес-домен.

## Graph context

Экспериментальный контекст для knowledge graph.

Сейчас не является частью основного MVP. Оставлен как задел под будущую работу с knowledge nodes/fragments.

## Connectors context

Задел под внешние интеграции: Gmail, YouTube и другие connectors.

Сейчас не является частью основного backend MVP.

## Persistence

Для persistence используется SQLAlchemy.

Модели лежат в outbound adapters каждого контекста:

```text
context/*/adapters/outbound/models.py
```

Общий declarative base находится здесь:

```text
shared/adapters/persistence/base.py
```

Все модели импортируются при старте через:

```text
bootstrap/models.py
```

Это нужно, чтобы SQLAlchemy увидел все таблицы перед `Base.metadata.create_all`.

Коммиты не выполняются внутри репозиториев. Транзакционная граница находится выше — на уровне Unit of Work / Direttore execution.

## Direttore

Backend построен вокруг собственного фреймворка **Direttore**.

Direttore используется как шина исполнения:

- command handlers;
- query handlers;
- event handlers;
- modular monolith contexts;
- Unit of Work coordination;
- execution-scoped dependency injection.

Контексты регистрируются в `bootstrap/contexts.py`, а Unit of Work factories — в `bootstrap/coordinator.py`.

## HTTP API

Внутренние HTTP endpoint'ы находятся в inbound adapters:

```text
context/*/adapters/inbound/api.py
context/*/adapters/inbound/schemas.py
```

Часть endpoint'ов уже поднята, но не все из них используются агентским сервером прямо сейчас.

Текущий MVP ориентируется на простые internal endpoints для agent-server и workflows.

## Чего здесь нет

В этом сервисе нет:

- LLM-агентов;
- Telegram bot polling/webhook логики;
- полноценного agent runtime;
- UI;
- внешних OAuth/connectors в рабочем виде.

Агенты находятся в отдельном сервисе:

```text
services/agent
```

Telegram Gateway находится в отдельном сервисе:

```text
services/telegram-gateway
```

## Текущий смысл backend

Backend — это источник истины для данных Planner и место, где проверяются доменные правила.

Даже если агент принимает решение, он не пишет напрямую в базу. Он должен обращаться к backend API, а backend уже исполняет соответствующий command/query через Direttore.
