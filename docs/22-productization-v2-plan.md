# Productization v2 — execution plan (post-Foundation)

Документ фиксирует следующий этап после завершения Foundation (Stage 0–6).
Цель этапа — превратить Foundation baseline в удобный, устойчивый, demo-first продуктовый контур,
сохранив принцип коротких, проверяемых и контекстно-ограниченных шагов для CloudCode.

## 1) Контекст и исходная точка

Завершённый этап:
- Foundation baseline (Stage 0–6):
  - governance/docs baseline;
  - platform bootstrap;
  - terminal core;
  - strategy core;
  - bot runtime core;
  - research lab minimum;
  - hardening/release readiness (baseline).

Принцип продолжения:
- Stage framework сохраняется;
- каждый stage — отдельная задача с чётким scope;
- один stage должен помещаться в контекстное окно CloudCode;
- следующий stage детализируется только после приёмки текущего.

## 2) Цель Productization v2

Сделать из Foundation baseline рабочий demo-first продуктовый контур с акцентом на:
- реальную пользовательскую работу (а не только каркас);
- безопасность и управляемость;
- воспроизводимость сценариев;
- наблюдаемость и удобство поддержки.

## 3) Принципы планирования (обязательные)

### 3.1 Размер шага

Каждый stage должен:
- иметь начало и конец;
- иметь однозначный артефакт результата;
- иметь воспроизводимые команды/проверки;
- не выходить за пределы контекстного окна CloudCode.

Рекомендуемый размер:
- 0.5–1 рабочий день на один stage/task pack.

### 3.2 Scope discipline

На каждом stage:
- делаем только заявленный scope;
- не уходим в "удобные доработки рядом";
- фиксируем deferred items отдельно (если всплыли).

### 3.3 Contract-first и docs-first

При изменениях API / flow:
- сначала обновить/сверить контракты;
- затем код;
- документация обновляется в том же PR.

## 4) Этапы Productization v2 (Stage 7–14)

### Stage 7 — Auth Hardening & Workspace Enforcement

Цель:
- закрыть security gap в workspace isolation;
- enforсить проверку членства пользователя в workspace на всех приватных роутах.

Результат stage:
- `workspaceId` из запроса проверяется против membership текущего `userId`;
- доступ к чужому workspace возвращает `403`;
- user/workspace context логируется безопасно (без утечки секретов);
- подготовлен handover по deferred auth-задачам (refresh/logout/RBAC).

Обязательные проверки:
- запрос к приватному endpoint с чужим `X-Workspace-Id` → 403;
- запрос с корректным `X-Workspace-Id` → success;
- проверка воспроизводима на двух пользователях (user A / user B);
- в логах есть `userId` + `workspaceId` без утечки `passwordHash`/секретов/JWT.

Task pack: `docs/steps/07-stage-7-auth-workspace.md`

---

### Stage 8 — Exchange Connections (demo-first)

Цель:
- сделать нормальное управление подключениями к бирже как отдельной сущностью;
- зафиксировать минимально безопасное хранение API-секретов для demo-first режима.

Результат stage:
- CRUD exchange connections;
- секрет хранится в зашифрованном виде (`encryptedSecret`, AES-256 через Node `crypto`);
- ключ шифрования берётся из `SECRET_ENCRYPTION_KEY` (env);
- endpoint проверки подключения;
- UI-отображение статуса подключения;
- API никогда не возвращает секреты (только безопасные поля).

Обязательные проверки:
- создание demo-подключения;
- test connection → success/fail с понятным ответом;
- в API-ответах отсутствуют секреты/ключи;
- UI показывает статус подключения.

Task pack: `docs/steps/08-stage-8-exchange-connections.md` _(создаётся после приёмки Stage 7)_

---

### Stage 9a — Terminal Market Data Flow (read-only)

Цель:
- собрать стабильный read-only сценарий Terminal для выбора инструмента и просмотра рынка.

Результат stage:
- выбор инструмента;
- отображение ticker/candles;
- UI корректно обрабатывает loading/error/success состояния;
- контракты ошибок согласованы (Problem Details, где применимо).

Обязательные проверки:
- happy path: выбор инструмента → ticker/candles отображаются;
- invalid symbol/input → корректная ошибка;
- UI корректно показывает состояния запроса.

Task pack: `docs/steps/09a-stage-9a-terminal-market-data.md` _(создаётся после приёмки Stage 8)_

---

### Stage 9b — Terminal Manual Order Flow (demo)

Цель:
- реализовать ручной ордерный flow в Terminal поверх Stage 8 (Exchange Connections).

Результат stage:
- ручной ордер `Market/Limit`;
- базовая валидация ввода;
- отображение статуса ордера/позиции;
- ошибки возвращаются в стабильном формате (Problem Details).

Scope boundaries:
- SL/TP deferred (если не существует простого и уже поддержанного пути без расширения scope).

Обязательные проверки:
- happy path: инструмент → ордер → статус;
- invalid input → корректная ошибка;
- UI показывает состояние запроса/ошибки/успеха.

Task pack: `docs/steps/09b-stage-9b-terminal-order-flow.md` _(создаётся после приёмки Stage 9a)_

---

### Stage 10 — Strategy Authoring UX

Цель:
- довести Strategy Core до удобного сценария создания/редактирования стратегии.

Результат stage:
- перед реализацией editor UX зафиксирована и задокументирована схема `StrategyVersion.body` (DSL contract freeze);
- редактор/форма Strategy DSL;
- schema validation с понятными pointers;
- сохранение и обновление стратегии;
- versioning (минимальный UX списка/версий).

Обязательные проверки:
- валидная стратегия сохраняется;
- невалидная отклоняется с понятной ошибкой;
- создание новой версии работает без порчи предыдущей.

Task pack: `docs/steps/10-stage-10-strategy-authoring.md` _(создаётся после приёмки Stage 9b)_

---

### Stage 11 — Bot Factory Launch Flow

Цель:
- реализовать рабочий flow запуска бота из стратегии.

Scope note:
- bot execution в рамках stage работает в demo/simulation режиме (без real-money execution) до отдельного решения.

Результат stage:
- создание бота из версии стратегии;
- настройка risk/execution параметров;
- старт/стоп/timeout;
- event log и отображение состояния runtime.

Обязательные проверки:
- happy path: strategy → bot → start;
- stop/timeout сценарии корректно отражаются в state/event log;
- UI показывает актуальный runtime state.

Task pack: `docs/steps/11-stage-11-bot-factory.md` _(создаётся после приёмки Stage 10)_

---

### Stage 12 — Research Lab Results & Reproducibility

Цель:
- сделать Research Lab воспроизводимым и пригодным для практической работы.

Результат stage:
- запуск replay/backtest;
- детерминированный результат на одинаковом наборе данных;
- сохранение результатов прогона;
- минимальный UI-отчёт (PnL, winrate, drawdown, trades).

Обязательные проверки:
- повторный запуск на том же датасете → совпадающие ключевые метрики;
- результаты прогона сохраняются и открываются;
- UI-отчёт отображается без ручных доработок.

Task pack: `docs/steps/12-stage-12-research-lab.md` _(создаётся после приёмки Stage 11)_

---

### Stage 13 — Observability & Ops Baseline

Цель:
- сделать систему наблюдаемой и удобной для диагностики/поддержки.

Примечание:
- структурированные логи (Fastify/pino baseline) считаются уже существующим базисом;
- scope stage — это улучшение наблюдаемости: correlation IDs, traceability, ops/audit слой и runbook delta.

Результат stage:
- correlation/request IDs;
- базовые health/ops метрики;
- audit/error trail;
- минимальные runbook'и на типовые инциденты.

Обязательные проверки:
- по одному запросу можно проследить цепочку по correlation ID;
- ошибка фиксируется в логах с достаточным контекстом;
- runbook воспроизводим на локальном/dev окружении.

Task pack: `docs/steps/13-stage-13-observability.md` _(создаётся после приёмки Stage 12)_

---

### Stage 14 — Release Candidate Pack

Цель:
- собрать релиз-кандидат (RC) с проверенным качеством, а не просто набор фич.

Результат stage:
- smoke/regression checklist;
- e2e happy-path сценарии;
- обновлённая документация запуска/обновления;
- финальная приемка по чек-листу.

Обязательные проверки:
- smoke checklist проходит полностью;
- e2e happy paths проходят без ручных фиксов;
- release notes / handover заполнены.

Task pack: `docs/steps/14-stage-14-release-candidate.md` _(создаётся после приёмки Stage 13)_

---

## 5) Порядок исполнения

| # | Stage | Task pack |
|---|-------|-----------|
| 1 | Stage 7 — Auth Hardening & Workspace Enforcement | `docs/steps/07-stage-7-auth-workspace.md` |
| 2 | Stage 8 — Exchange Connections | `docs/steps/08-stage-8-exchange-connections.md` |
| 3 | Stage 9a — Terminal Market Data Flow | `docs/steps/09a-stage-9a-terminal-market-data.md` |
| 4 | Stage 9b — Terminal Manual Order Flow | `docs/steps/09b-stage-9b-terminal-order-flow.md` |
| 5 | Stage 10 — Strategy Authoring UX | `docs/steps/10-stage-10-strategy-authoring.md` |
| 6 | Stage 11 — Bot Factory Launch Flow | `docs/steps/11-stage-11-bot-factory.md` |
| 7 | Stage 12 — Research Lab Results & Reproducibility | `docs/steps/12-stage-12-research-lab.md` |
| 8 | Stage 13 — Observability & Ops Baseline | `docs/steps/13-stage-13-observability.md` |
| 9 | Stage 14 — Release Candidate Pack | `docs/steps/14-stage-14-release-candidate.md` |

Причина порядка:
- сначала identity/security foundation;
- затем пользовательские потоки (Terminal / Strategy / Bot / Lab);
- затем ops/observability;
- затем RC-сборка.

## 6) Scope boundaries (что НЕ делаем в Productization v2 без отдельного решения)

- production-grade multi-tenant архитектуру (полноценную);
- сложную оптимизацию/parameter search в Research Lab;
- расширенную RBAC-модель;
- high-availability/cluster orchestration;
- глубокий UI/brand redesign (если не влияет на сценарий stage).

Если такие задачи всплывают:
- фиксируем как deferred;
- не включаем в текущий stage без явного решения.

## 7) Stage acceptance rule (для всех stage в Productization v2)

Stage считается закрытым только если:

1. выполнены все обязательные результаты stage;
2. проверки воспроизводимы командами/шагами;
3. PR и commit history без scope creep;
4. документация обновлена в том же PR;
5. подготовлен handover для следующего stage.

## 8) Формат task pack для CloudCode (на каждый stage отдельно)

Для каждого stage создаётся отдельный документ в `docs/steps/` со структурой:

1. Scope
2. Scope boundaries
3. Required references
4. Required output format (Plan / Implementation / Verification / Handover)
5. Acceptance checks
6. Review checklist
7. Exit criteria
