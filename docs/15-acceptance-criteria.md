# Acceptance Criteria (MVP v1)

Документ фиксирует критерии приёмки MVP v1. Каждый критерий имеет конкретную проверку.

## 1) Platform bootstrap (Stage 1)

- [ ] Backend стартует без ошибок (`docker compose up`).
- [ ] `GET /api/healthz` → 200.
- [ ] `GET /api/readyz` → 200.
- [ ] `POST /api/auth/login` → stub response (access + refresh token).
- [ ] Frontend отображает 3 роута: Terminal, Lab, Factory.
- [ ] Миграции БД применяются локально (`pnpm prisma migrate deploy`).
- [ ] README содержит инструкцию запуска dev-окружения.

## 2) Terminal (Stage 2)

- [ ] Пользователь видит список `linear` инструментов из instruments-info.
- [ ] Свечной график отображает данные (минимум 1m таймфрейм).
- [ ] Текущая цена и 24h изменение отображаются.
- [ ] Пользователь подключает demo API ключ в Settings.
- [ ] `Market` ордер создаётся и отображается в таблице.
- [ ] `Limit` ордер создаётся и отображается в таблице.
- [ ] SL/TP обязательны — форма не позволяет отправить ордер без них.
- [ ] Статус ордера обновляется по WS (accepted → filled/rejected).
- [ ] Невалидный ввод возвращает Problem Details с понятным сообщением.

## 3) Strategy (Stage 3)

- [ ] Стратегия создаётся через UI (JSON-редактор) или AI-чат.
- [ ] Стратегия валидируется по `strategy.schema.json` до сохранения.
- [ ] Невалидная стратегия отклоняется с указанием поля (`pointer`).
- [ ] Версионирование: новая версия не затирает предыдущую.
- [ ] AI-чат генерирует Strategy Spec и текстовое объяснение.
- [ ] AI не получает API secrets и не инициирует торговых действий.

## 4) Bot runtime (Stage 4)

- [ ] Бот создаётся из сохранённой стратегии.
- [ ] Start: бот переходит в `running`, события пишутся в лог.
- [ ] Stop: бот корректно останавливается по кнопке.
- [ ] Timeout: бот останавливается автоматически по истечении duration.
- [ ] Reconciliation: после restart/reconnect бот восстанавливает состояние через REST.
- [ ] Idempotency: повторная отправка intent не создаёт дубль ордера.
- [ ] SL/TP выставляются после открытия позиции; при неудаче — failsafe (market close или PAUSED).
- [ ] Event log содержит: signal, order_sent, order_update, position_update, risk_blocked, error.

## 5) Research Lab (Stage 5)

- [ ] Исторический replay по свечам генерирует отчёт.
- [ ] Отчёт содержит: количество сделок, winrate, PnL, max drawdown.
- [ ] Отчёт детерминированный (одинаковые данные → одинаковый результат).
- [ ] Demo-forward прогон стратегии записывает события в журнал.

## 6) Safety & security (сквозное)

- [ ] Все ID ресурсов проверяются на принадлежность userId (BOLA).
- [ ] API secrets шифруются at-rest, не попадают в логи/UI/AI.
- [ ] Rate limiting на backend: create order, start bot, AI generate.
- [ ] Max concurrent BotRuns: 1.
- [ ] Max duration run: ограничен конфигом.
- [ ] Stop All: останавливает все активные боты.
- [ ] Cookies: HttpOnly, Secure, SameSite=Lax (если cookie-based).
- [ ] CSRF защита активна.
- [ ] AI markdown санитизируется перед рендером (XSS).

## 7) Operations (сквозное)

- [ ] Логи структурированные (pino JSON) с botId, runId, intentId.
- [ ] Health endpoints работают под нагрузкой.
- [ ] БД бэкапится ежедневно.
- [ ] Runbooks документированы: WS storm, rate limit, SL/TP failure.

## 8) Definition of Done (общее)

MVP считается готовым когда:
1. Все чекбоксы Stages 1–6 пройдены на demo.
2. Smoke-тест на demo-среде пройден без ошибок.
3. Документация актуальна и не содержит битых ссылок.
4. Security checklist из `docs/05-security.md` выполнен.
5. Нет критических ошибок в логах за последние 24 часа demo-прогона.
