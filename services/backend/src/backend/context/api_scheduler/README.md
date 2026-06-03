

context/api_scheduler/
  владеет записями операций и логикой "можно ли запускать"

shared/api_scheduler/
  содержит порт, через который другие контексты могут попросить запланировать операцию

bootstrap/
  создаёт реальный APScheduler, подключает его к Direttore command execution

api_scheduler context = state + rules
APScheduler object = runtime infrastructure
shared port = интерфейс для других контекстов



8. Почему api_scheduler должен быть отдельным context

Например, connectors говорит: проверять YouTube канал каждые 6 часов
schedule говорит: отправить reminder завтра в 10:00
analytics говорит: пересчитать профиль пользователя раз в 24 часа

Все они не должны напрямую знать APScheduler.

Они должны пользоваться общим портом:

schedule_operation(...)
cancel_operation(...)
reschedule_operation(...)

А api_scheduler уже хранит operation records и знает, что реально запускать.

