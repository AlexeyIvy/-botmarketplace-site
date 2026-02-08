# Интеграция Bybit (Demo-first, API V5)

Документ фиксирует, как мы подключаемся к Bybit, какие endpoint’ы используем в MVP и какие правила исполнения считаем обязательными.

## 1) Окружения Bybit (env)

MVP MUST:
- Торговые операции выполняются только в Bybit Demo Trading.
- Public market data берём из публичных источников Bybit (mainnet public), а private account/order/position — из demo private.

### 1.1 Demo endpoints
- REST demo: `https://api-demo.bybit.com`
- Private WS demo: `wss://stream-demo.bybit.com` (поддерживает только private streams; public data идентичны mainnet `wss://stream.bybit.com`; WS Trade в demo не поддерживается)
- В demo ордера хранятся 7 дней
Источник: Demo Trading Service. [web:321]

## 2) Категории рынков (category)

MVP:
- Default `category=linear` (USDT perpetual).

Post-MVP:
- `inverse`, затем `spot`.

## 3) Market Data (публичные данные)

MVP:
- Instruments/tickers/candles нужны для терминала и стратегии.

SHOULD:
- Кэшировать и ограничивать частоту запросов.

## 4) Order Management (MVP)

### 4.1 Place Order
Используем: `POST /v5/order/create` (Place Order). [web:358]

MUST:
- Задавать `orderLinkId` (до 36 символов, уникальный) для идемпотентности и трассировки. [web:358]
- Не считать ордер “исполненным” по факту успешного ответа Place Order: ответ означает, что запрос принят, статус подтверждаем через private WS/опрос. [web:358]

## 5) SL/TP через Trading Stop (дефолт MVP)

Используем: `POST /v5/position/trading-stop` (Set Trading Stop). [web:359]

MVP MUST:
- SL и TP обязательны для запуска бота и для ручной торговли (если позиция открыта).
- После выставления ордера — дождаться подтверждения позиции/ордера (через WS/REST), затем применить trading-stop.

Важно:
- Bybit отмечает, что trading-stop создаёт conditional orders внутри системы, отменяет их при закрытии позиции и “подгоняет” qty под размер открытой позиции. [web:359]

## 6) WebSocket (подписки и стабильность)

MUST:
- Heartbeat: отправлять ping каждые 20 секунд для поддержания соединения. [web:377]
- Авто-reconnect с backoff.
- После reconnect: reconciliation через REST (ордера/позиции), затем resubscribe.

