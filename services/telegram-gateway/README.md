# Telegram Gateway

Telegram Gateway — это отдельный FastAPI-сервис, который связывает Backend, Agent Server и Telegram.

Сейчас сервис поддерживает полноценное общение через Telegram-бота:

1. пользователь пишет боту `/start`;
2. Telegram Gateway создаёт пользователя в Backend;
3. Gateway получает `business_user_id`;
4. Gateway привязывает `business_user_id` к `telegram_user_id` и `telegram_chat_id`;
5. после этого пользователь может писать боту обычные сообщения;
6. Gateway передаёт сообщения в Agent Server и отправляет ответ обратно в Telegram.

Дополнительно сервис отвечает за:

1. отправку уведомлений и ответов пользователю в Telegram;
2. хранение текущей сессии общения пользователя с агентом в Redis;
3. синхронизацию Telegram binding между Postgres, Backend и Telegram chat.

## Зачем нужен Telegram Gateway

Telegram Gateway является транспортным шлюзом между внутренней системой и Telegram.

Он хранит связь:

```text
business_user_id <-> telegram_user_id <-> telegram_chat_id
```

Эта связь нужна, чтобы Backend и Runtime Context могли отправлять пользователю уведомления, напоминания и сообщения, не зная ничего о Telegram ID и Telegram Chat ID.

Backend работает только с `business_user_id`. Telegram Gateway сам резолвит, в какой Telegram chat нужно отправить сообщение.

## Текущий статус

Сервис проверен в локальном окружении:

```text
Telegram chat -> Telegram Bot API -> Telegram Gateway -> Backend / Agent Server / Redis
```

Также проверено, что:

1. binding пользователя сохраняется в Postgres;
2. сессия пользователя сохраняется и обновляется в Redis;
3. webhook регистрируется автоматически при старте, если `USE_TELEGRAM=true`.

## Основной пользовательский flow

### 1. Пользователь пишет боту `/start`

Telegram Gateway получает webhook update от Telegram и проверяет, есть ли уже binding для `telegram_user_id`.

Если binding ещё нет:

1. Gateway создаёт пользователя в Backend;
2. использует Telegram-поля для `login` и `name`;
3. создаёт пароль по умолчанию;
4. сохраняет binding между `business_user_id`, `telegram_user_id` и `telegram_chat_id`;
5. отвечает пользователю сообщением о том, что аккаунт создан и чат привязан.

Если пользователь пишет не `/start`, а binding ещё не создан, Gateway просит сначала отправить `/start`.

### 2. Пользователь пишет обычное сообщение

После привязки любой текст отправляется в Agent Server.

Что происходит внутри:

1. Telegram Gateway получает webhook update;
2. находит binding в Postgres;
3. добавляет сообщение пользователя в Redis-сессию;
4. передаёт историю сообщений в Agent Server;
5. получает ответ агента;
6. добавляет ответ в Redis-сессию;
7. отправляет ответ пользователю в Telegram.

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
POST /telegram/webhook
POST /auth
POST /telegram/attach
POST /agent/message
POST /agent/session/get
POST /agent/session/close
POST /telegram/notifications/send
```

## Запуск

Перед запуском должны быть подняты Postgres и Redis.

Для Telegram-бота также должен быть доступен публичный HTTPS URL, например через ngrok.

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
USE_TELEGRAM=true
TELEGRAM_WEBHOOK_PUBLIC_URL=https://example.ngrok-free.dev
TELEGRAM_WEBHOOK_SECRET=...
TELEGRAM_WEBHOOK_DELETE_ON_SHUTDOWN=true
INTERNAL_API_TOKEN=...

BACKEND_HOST=localhost
BACKEND_PORT=8001

AGENT_HOST=localhost
AGENT_PORT=8002
```

### Что важно знать про Telegram

1. `USE_TELEGRAM=true` включает регистрацию webhook и входящий Telegram flow.
2. `TELEGRAM_WEBHOOK_PUBLIC_URL` должен указывать на публичный HTTPS endpoint, который Telegram может достичь.
3. `TELEGRAM_WEBHOOK_DELETE_ON_SHUTDOWN=true` удаляет webhook при остановке сервиса.
4. `utc_offset_minutes` для создания пользователя сейчас берётся как `0`, потому что Telegram webhook не передаёт timezone пользователя напрямую.

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
