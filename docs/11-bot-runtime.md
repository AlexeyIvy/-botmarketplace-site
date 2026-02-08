# Bot Runtime (MVP)

Документ описывает рантайм торгового бота: состояния, события, цикл исполнения, обработку ошибок и reconciliation.

## 1) Общая модель

MVP:
- Один бот = одна стратегия + один пользователь + один symbol (в MVP можно расширить, но ядро проектируем так, чтобы масштабировалось).
- Источники событий: webhook/ручной сигнал, таймер (polling), private WS события, ответы REST.

MVP MUST:
- Реализовать “одна позиция на symbol” (см. guards в Strategy DSL).
- Уметь восстановиться после рестарта: на старте делаем reconciliation через REST и приводим локальный state в соответствие бирже.

## 2) Состояния (state machine)

Состояния:
- `IDLE`: нет позиции, можно принимать сигналы.
- `ARMED`: сигнал получен, проходит pre-checks (лимиты/баланс/паузы).
- `ENTRY_PENDING`: отправили entry order, ждём подтверждения (WS/REST).
- `IN_POSITION`: позиция открыта, SL/TP установлены.
- `EXIT_PENDING`: отправили закрывающий ордер/сработал SL/TP, ждём подтверждения.
- `PAUSED`: остановлено из-за ошибок/лимитов.
- `DISABLED`: стратегия выключена.

Переходы MUST быть детерминированными и логироваться.

## 3) Core loop (упрощённо)

1) Load strategy config + validate (JSON Schema).
2) Reconciliation:
   - Получить текущие открытые позиции/ордера.
   - Если позиция есть, перейти в `IN_POSITION`, иначе `IDLE`.
3) Event loop:
   - OnSignal -> pre-checks -> place order -> confirm -> set SL/TP -> monitor.
   - OnWSDisconnect -> reconnect -> reconciliation -> continue.

## 4) Идемпотентность и трассировка

MVP MUST:
- Для всех создаваемых ордеров формировать `orderLinkId` из `clientOrderIdPrefix` + уникальная часть (например ULID/UUID).
- Хранить mapping “наш intent” -> “orderId/orderLinkId”.
- Любую операцию повторять безопасно (если предыдущий ответ потерян, бот не должен создать дубликат).

## 5) Подтверждение исполнения (confirm)

MVP MUST:
- Не полагаться только на ответ `place order`.
- Подтверждать факт открытия/закрытия позиции по данным account/order/position (WS/REST).
- После каждого reconnect всегда делать reconciliation (ордера/позиции).

## 6) SL/TP политика (MVP)

MVP MUST:
- SL и TP обязательны для каждой позиции.
- Если после открытия позиции SL/TP не выставились, бот обязан:
  - попытаться выставить ещё раз (retry),
  - при повторной неудаче — закрыть позицию market (failsafe) или перевести стратегию в `PAUSED` (выбор фиксируем конфигом).

## 7) Ошибки и ретраи

Классы ошибок:
- Network/timeout: ретраи с backoff.
- Exchange rejected (некорректные параметры): без ретраев, в `PAUSED`.
- Rate limit: ретраи с увеличенным backoff и глобальным троттлингом.

MVP MUST:
- Ограничение `maxOrdersPerMinute`.
- `pauseOnError`: после N ошибок за M минут переводить стратегию в `PAUSED`.

## 8) Наблюдаемость (logs/metrics)

MVP MUST логировать:
- intentId, strategyId, symbol, side.
- orderLinkId, orderId (если получен).
- transition state: from->to.
- ошибки: код/сообщение/stack.

SHOULD (если быстро):
- метрики: orders placed, fills, disconnects, retries, PnL (demo).

