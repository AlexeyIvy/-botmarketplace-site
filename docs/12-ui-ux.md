# UI/UX (MVP v1)

Документ описывает структуру интерфейса, основные страницы, user flows и компонентную модель MVP.

## 1) Общие принципы

- Mobile-last: MVP оптимизирован под десктоп (1280px+), адаптив — post-MVP.
- Язык: RU + EN (i18n через next-intl).
- Тема: тёмная по умолчанию (trading convention), light — post-MVP.
- Design tokens отделены от бизнес-логики (для будущего редизайна).

## 2) Структура страниц (роуты)

| Route | Название | Назначение |
|---|---|---|
| `/terminal` | Terminal | Ручная торговля: график, ордера, позиции |
| `/lab` | Research Lab | Strategy DSL редактор, backtest, AI-чат |
| `/factory` | Bot Factory | Список ботов, создание, запуск, логи |
| `/settings` | Settings | Exchange connections, профиль |
| `/login` | Login | Аутентификация |

## 3) Terminal (ручная торговля)

### Layout
- **Левая панель**: список инструментов (search + filter по `linear`).
- **Центр**: свечной график (lightweight-charts), переключение таймфреймов (1m/5m/15m/1h).
- **Правая панель**: форма ордера (Market/Limit), поля SL/TP (обязательны).
- **Нижняя панель**: таблицы открытых ордеров, позиций, истории.

### User flow: ручная сделка
1. Выбрать инструмент из списка.
2. Увидеть график + текущую цену.
3. Заполнить форму ордера (side, type, qty, price, SL, TP).
4. Нажать «Place Order».
5. Увидеть ордер в таблице открытых ордеров.
6. Увидеть обновление статуса (accepted → filled / rejected).

### Компоненты
- `InstrumentList` — список инструментов с поиском
- `CandleChart` — свечной график
- `OrderForm` — форма создания ордера
- `OrdersTable` — открытые ордера
- `PositionsTable` — текущие позиции
- `TradeHistory` — история сделок

## 4) Research Lab

### Layout
- **Левая панель**: список стратегий (CRUD).
- **Центр**: редактор Strategy DSL (JSON) + валидация в реальном времени.
- **Правая панель**: AI-чат (генерация/правка стратегии).
- **Нижняя панель**: результаты backtest (если запущен).

### User flow: создание стратегии через AI
1. Открыть Lab, нажать «New Strategy».
2. Описать идею в AI-чате (текстом).
3. AI генерирует Strategy Spec (JSON) + объяснение.
4. Пользователь видит JSON в редакторе, может отредактировать.
5. Нажать «Validate» — проверка по schema.
6. Нажать «Save» — стратегия сохраняется.

### User flow: backtest (MVP minimum)
1. Выбрать сохранённую стратегию.
2. Нажать «Run Backtest» (исторический replay по свечам).
3. Увидеть отчёт: trades, winrate, PnL, max drawdown.

### Компоненты
- `StrategyList` — список стратегий
- `DslEditor` — JSON-редактор с подсветкой и валидацией
- `AiChat` — чат-панель (input + history + strategy output)
- `BacktestReport` — отчёт бэктеста (таблица + метрики)

## 5) Bot Factory

### Layout
- **Список ботов**: карточки/таблица со статусом (draft/ready/running/stopped/error).
- **Детали бота**: конфиг, стратегия, risk params, event log.
- **Управление**: Start (duration) / Stop / Delete.

### User flow: запуск бота
1. Создать бота: выбрать стратегию, задать risk-параметры.
2. Увидеть превью: symbol, strategy, SL/TP, risk limits.
3. Нажать «Start» с указанием duration (минуты).
4. Бот переходит в `running`, UI показывает live-лог событий.
5. По timeout или по кнопке «Stop» — бот останавливается.
6. Просмотр журнала событий (BotEvents).

### Компоненты
- `BotList` — список ботов с фильтром по статусу
- `BotCard` — карточка бота (summary)
- `BotDetail` — полная информация + управление
- `EventLog` — реалтайм лог событий бота
- `RiskBadge` — индикатор текущей риск-политики (strict/pause-only)

## 6) Settings

- `ExchangeConnectionForm` — добавить/проверить demo API ключ
- `ConnectionStatus` — статус подключения (OK/Error + last check)
- Секрет не отображается после сохранения (только masked)

## 7) Общие компоненты

- `AppLayout` — shell с навигацией (Terminal / Lab / Factory / Settings)
- `Navbar` — top bar с текущим разделом и user info
- `ErrorBoundary` — обработка ошибок рендера
- `ProblemToast` — отображение Problem Details ошибок от API
- `ConfirmDialog` — подтверждение опасных действий (Stop All, Delete)
