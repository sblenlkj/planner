# Telegram Gateway

Telegram Gateway — это отдельный FastAPI-сервис, который связывает Backend, Agent Server и Telegram.

Сейчас сервис используется в упрощённом D2V/MVP-режиме. Мы временно отказались от полноценного Telegram webhook-flow, потому что во время локального тестирования через ngrok сообщения могли приходить с большой задержкой и было сложно отделять задержки Telegram/ngrok от задержек внутри приложения.

В текущей версии Telegram Gateway отвечает за две основные задачи:

1. отправлять сообщения пользователю в Telegram;
2. хранить текущую сессию общения пользователя с агентом в Redis.

## Зачем нужен Telegram Gateway

Telegram Gateway является транспортным шлюзом между внутренней системой и Telegram.

Он хранит связь:

```text
business_user_id <-> telegram_user_id <-> telegram_chat_id
```

Эта связь нужна, чтобы Backend и Runtime Context могли отправлять пользователю уведомления, напоминания и сообщения, не зная ничего о Telegram ID и Telegram Chat ID.

Backend работает только с `business_user_id`. Telegram Gateway уже сам резолвит, в какой Telegram chat нужно отправить сообщение.

## Текущий статус

Сервис проверен в локальном окружении:

```text
Swagger / API -> Telegram Gateway -> Telegram Bot API -> Telegram chat
```

Также проверено, что сессия пользователя сохраняется и обновляется в Redis.

## Что временно не используется

В текущей версии не используется полноценный входящий Telegram webhook-flow:

```text
Telegram -> ngrok -> Telegram Gateway
```

Этот flow был поднят и проверен, но в локальном тестировании сообщения могли идти слишком долго. Поэтому для MVP сейчас используется более контролируемая схема через Swagger/API.

В будущем webhook можно вернуть, когда будет готова стабильная продакшен-инфраструктура с публичным HTTPS endpoint.

## Основной пользовательский flow

### 1. Создать пользователя в Backend

Сначала пользователь создаётся на стороне Backend.

Backend возвращает `business_user_id`.

Пример:

```text
e670eed3-66ef-452b-b53a-509f69071250
```

Этот ID дальше используется в Telegram Gateway.

### 2. Проверить пользователя через Telegram Gateway

В Telegram Gateway есть ручка:

```http
POST /auth
```

Она принимает `business_user_id` и проверяет через Backend, что такой пользователь существует.

Пример body:

```json
{
  "business_user_id": "e670eed3-66ef-452b-b53a-509f69071250"
}
```

Ответ:

```json
{
  "access_token": "e670eed3-66ef-452b-b53a-509f69071250",
  "token_type": "bearer"
}
```

Сейчас `access_token` фактически равен `business_user_id`. Это сделано для простого MVP-тестирования.

### 3. Привязать Telegram аккаунт

После этого нужно привязать Telegram ID и Telegram Chat ID к `business_user_id`.

Ручка:

```http
POST /telegram/attach
```

Пример body:

```json
{
  "business_user_id": "e670eed3-66ef-452b-b53a-509f69071250",
  "telegram_user_id": 1171103388,
  "telegram_chat_id": 1171103388
}
```

Для личного чата с ботом `telegram_user_id` и `telegram_chat_id` часто совпадают.

После этого Gateway сохраняет binding в Postgres.

## Работа с агентом

Telegram Gateway умеет отправлять сообщение основному агенту.

Ручка:

```http
POST /agent/message
```

Пример body:

```json
{
  "business_user_id": "e670eed3-66ef-452b-b53a-509f69071250",
  "text": "Привет, помоги мне спланировать день"
}
```

Что происходит внутри:

1. Telegram Gateway получает `business_user_id`.
2. Достаёт Telegram binding из Postgres.
3. Добавляет сообщение пользователя в Redis-сессию.
4. Достаёт текущую историю сообщений из Redis.
5. Отправляет историю сообщений на Agent Server.
6. Получает ответ агента.
7. Добавляет ответ агента в Redis-сессию.
8. Отправляет ответ пользователю в Telegram.
9. Возвращает ответ в HTTP response.

Таким образом Redis хранит текущую сессию пользователя.

## Получить текущую сессию

Для отладки есть ручка:

```http
POST /agent/session/get
```

Пример body:

```json
{
  "business_user_id": "e670eed3-66ef-452b-b53a-509f69071250"
}
```

Ответ содержит сообщения, которые сейчас лежат в Redis-сессии пользователя:

```json
{
  "ok": true,
  "messages": [
    {
      "role": "user",
      "content": "Привет"
    },
    {
      "role": "assistant",
      "content": "Ответ агента"
    }
  ]
}
```

## Закрыть сессию

Ручка:

```http
POST /agent/session/close
```

Пример body:

```json
{
  "business_user_id": "e670eed3-66ef-452b-b53a-509f69071250"
}
```

Что происходит:

1. Telegram Gateway достаёт текущую Redis-сессию пользователя.
2. Если сессия пустая — возвращает `closed=false`.
3. Если сообщения есть — отправляет их в Agent Server на endpoint закрытия сессии.
4. Agent Server запускает workflow обработки закрытой сессии.
5. Telegram Gateway очищает Redis-сессию.

Эта ручка нужна, чтобы закрывать накопленный диалог и передавать его в workflow анализа.

## Отправить уведомление в Telegram

Для Runtime Context и Backend есть endpoint отправки уведомлений и напоминаний:

```http
POST /telegram/notifications/send
```

Пример body:

```json
{
  "business_user_id": "e670eed3-66ef-452b-b53a-509f69071250",
  "text": "Напоминание: пора сделать домашнее задание по Python"
}
```

Что происходит:

1. Telegram Gateway находит Telegram chat по `business_user_id`.
2. Отправляет сообщение в Telegram.
3. Добавляет это сообщение в Redis-сессию как сообщение ассистента.

Это важно, потому что пользователь может ответить на напоминание. Например:

```text
А что это за домашнее задание?
```

Агент увидит предыдущее уведомление в сессии и сможет ответить в контексте.

## Хранилища

### Postgres

Postgres хранит только persistent binding:

```text
telegram_gateway.telegram_bindings
```

Поля:

```text
business_user_id
telegram_user_id
telegram_chat_id
```

### Redis

Redis хранит текущую сессию пользователя.

Ключ строится по `business_user_id`.

Пример:

```text
telegram_gateway:session:{business_user_id}
```

Значение — список сообщений:

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

## API endpoints

Текущие основные endpoints:

```http
GET  /health
POST /auth
POST /telegram/attach
POST /agent/message
POST /agent/session/get
POST /agent/session/close
POST /telegram/notifications/send
```

## Запуск

Перед запуском должны быть подняты Postgres и Redis.

Из директории сервиса:

```bash
uv run telegram-gateway
```

После запуска Swagger доступен по адресу:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## Переменные окружения

Основные переменные:

```env
SERVER_HOST=localhost
SERVER_PORT=8000

DATABASE_URL=postgresql+asyncpg://planner:planner@localhost:5432/planner
REDIS_URL=redis://localhost:6379/0

TELEGRAM_BOT_TOKEN=...
INTERNAL_API_TOKEN=...

BACKEND_HOST=localhost
BACKEND_PORT=8001

AGENT_HOST=localhost
AGENT_PORT=8002
```

## Роль сервиса в системе

Telegram Gateway не владеет бизнес-логикой пользователя, расписанием, runtime jobs или агентскими workflow.

Он отвечает только за:

```text
- связь business_user_id с Telegram chat;
- отправку сообщений в Telegram;
- хранение текущей Redis-сессии пользователя;
- передачу сообщений и закрытых сессий в Agent Server.
```

Backend остаётся владельцем пользователя, runtime status, расписания и бизнес-данных.

Agent Server остаётся владельцем логики обработки сообщений, анализа сессий и генерации ответов.
