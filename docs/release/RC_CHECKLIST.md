# RC Checklist — BotMarketplace v0.1.0-rc1

**Purpose:** Единый список проверок перед пометкой релиза как Release Candidate.
Выполнять при каждом деплое на production и перед тегированием RC.

---

## 1. Infrastructure & Health

| # | Проверка | Команда / шаги | Критерий прохождения |
|---|---------|----------------|----------------------|
| 1.1 | API liveness | `curl -s https://botmarketplace.ru/api/v1/healthz \| jq .` | `{"status":"ok","uptime":<number>,"timestamp":"<ISO>"}` |
| 1.2 | API readiness (DB) | `curl -s https://botmarketplace.ru/api/v1/readyz \| jq .` | `{"status":"ok"}` |
| 1.3 | Web UI доступен | `curl -s -o /dev/null -w "%{http_code}" https://botmarketplace.ru/login` | `200` |
| 1.4 | Correlation ID | `curl -sI https://botmarketplace.ru/api/v1/healthz \| grep -i x-request-id` | Заголовок присутствует |
| 1.5 | systemd services | `systemctl is-active botmarket-api && systemctl is-active botmarket-web` | оба `active` |
| 1.6 | Bot worker online | `journalctl -u botmarket-api --no-pager -n 50 \| grep "botWorker.*started"` | Строка присутствует |

---

## 2. Auth / Register / Login

| # | Проверка | Критерий |
|---|---------|----------|
| 2.1 | `POST /auth/register` → 201, accessToken + workspaceId | Оба поля в ответе |
| 2.2 | `POST /auth/login` → 200, accessToken | Поле в ответе |
| 2.3 | `POST /auth/login` с неверным паролем → 401 | HTTP 401 |
| 2.4 | `GET /auth/me` с токеном → 200 | HTTP 200 |
| 2.5 | `GET /auth/me` без токена → 401 | HTTP 401 |
| 2.6 | Rate limiting: 6+ запросов к `/auth/register` → 429 | HTTP 429 появляется |
| 2.7 | Rate limit 429 не превращается в 500 (regression) | HTTP 429, не 500 |

---

## 3. Exchange Connections (demo-first)

| # | Проверка | Критерий |
|---|---------|----------|
| 3.1 | `POST /exchanges` → 201 | HTTP 201 |
| 3.2 | Ответ НЕ содержит `apiKey`, `secret`, `encryptedSecret` | Секретов нет |
| 3.3 | `GET /exchanges` → 200 + array | HTTP 200 |
| 3.4 | `GET /exchanges/:id` → 200 | HTTP 200, без секретов |
| 3.5 | `DELETE /exchanges/:id` → 204 | HTTP 204 |
| 3.6 | `GET /exchanges` без токена → 401 | HTTP 401 |

---

## 4. Terminal — Market Data

| # | Проверка | Критерий |
|---|---------|----------|
| 4.1 | `GET /terminal/ticker?symbol=BTCUSDT` → 200 + `lastPrice`, `symbol` | HTTP 200 + поля |
| 4.2 | `GET /terminal/candles?symbol=BTCUSDT&interval=15&limit=10` → 200 + OHLCV | HTTP 200 + `openTime`, `close` |
| 4.3 | Ticker без символа → 400 | HTTP 400 |
| 4.4 | Candles с неверным interval → 400 + "Allowed values" | HTTP 400 |
| 4.5 | Ticker несуществующий символ → 422 | HTTP 422 |
| 4.6 | Ticker без auth → 401 | HTTP 401 |
| 4.7 | Ответ тикера не содержит секретов | Нет `apiKey`/`secret` |

---

## 5. Strategy Authoring

| # | Проверка | Критерий |
|---|---------|----------|
| 5.1 | `POST /strategies` → 201 | HTTP 201 |
| 5.2 | `POST /strategies/validate` с валидным DSL → 200 + `ok:true` | HTTP 200 |
| 5.3 | `POST /strategies/validate` с невалидным DSL → 400 + `errors` | HTTP 400 |
| 5.4 | `POST /strategies/:id/versions` с валидным DSL → 201 | HTTP 201 |
| 5.5 | `POST /strategies/:id/versions` с невалидным DSL → 400 | HTTP 400 |
| 5.6 | `GET /strategies` без auth → 401 | HTTP 401 |

---

## 6. Bot Factory

| # | Проверка | Критерий |
|---|---------|----------|
| 6.1 | `POST /bots` с strategyVersionId → 201 | HTTP 201 |
| 6.2 | `POST /bots` без strategyVersionId → 400 | HTTP 400 |
| 6.3 | `POST /bots` с несуществующим strategyVersionId → 400 | HTTP 400 |
| 6.4 | `GET /bots/:id` → 200 + `strategyVersion` + `lastRun` | HTTP 200 + поля |
| 6.5 | `POST /bots/:id/runs` → 201 + `durationMinutes` | HTTP 201 |
| 6.6 | `POST /bots/:id/runs` повторно → 409 (уже активный run) | HTTP 409 |
| 6.7 | `GET /bots/:id/runs` → 200 + array | HTTP 200 |
| 6.8 | `POST /bots/:id/runs/:runId/stop` → 200 или 409 | HTTP 200 или 409 |
| 6.9 | `GET /runs/:runId/events` → 200 + events array | HTTP 200 |
| 6.10 | Events не содержат секретов | Нет `encryptedSecret`/`apiKey` |
| 6.11 | `POST /runs/stop-all` → 200 | HTTP 200 |
| 6.12 | `GET /bots` без auth → 401 | HTTP 401 |

---

## 7. Cross-Workspace Isolation

| # | Проверка | Критерий |
|---|---------|----------|
| 7.1 | Бот workspace 1 недоступен для workspace 2 | 403 или 404 |
| 7.2 | Нельзя запустить run на боте чужого workspace | 403 или 404 |
| 7.3 | Нельзя обратиться к ресурсам без X-Workspace-Id при нужности | 400 или 403 |

---

## 8. Bot Worker Internals

| # | Проверка | Критерий |
|---|---------|----------|
| 8.1 | Worker endpoint `PATCH /runs/:id/state` без BOT_WORKER_SECRET → 401 (в production) | HTTP 401 |
| 8.2 | Worker endpoint `POST /runs/:id/heartbeat` без секрета → 401 (в production) | HTTP 401 |
| 8.3 | `POST /runs/reconcile` без секрета → 401 (в production) | HTTP 401 |

---

## 9. Research Lab

| # | Проверка | Критерий |
|---|---------|----------|
| 9.1 | `POST /lab/backtest` → 202 + status PENDING | HTTP 202 |
| 9.2 | `GET /lab/backtests` → 200 + array | HTTP 200 |
| 9.3 | `GET /lab/backtest/:id` → 200 | HTTP 200 |
| 9.4 | `POST /lab/backtest` без auth → 401 | HTTP 401 |
| 9.5 | `POST /lab/backtest` без strategyId → 400 | HTTP 400 |
| 9.6 | `POST /lab/backtest` с fromTs >= toTs → 400 | HTTP 400 |

---

## 10. Observability

| # | Проверка | Критерий |
|---|---------|----------|
| 10.1 | `/healthz` содержит `uptime` и `timestamp` | Оба поля |
| 10.2 | Каждый ответ содержит `X-Request-Id` | Заголовок присутствует |
| 10.3 | Клиентский `X-Request-Id` возвращается без изменений | Echo корректен |
| 10.4 | 5xx ошибки не раскрывают stack trace в production | `detail` = общее сообщение |

---

## 11. Автоматизация: Smoke Suite

```bash
# Полный smoke suite (83+ тестов)
bash deploy/smoke-test.sh

# Против кастомного URL
BASE_URL=https://your-staging.example.com bash deploy/smoke-test.sh

# С BOT_WORKER_SECRET для проверки worker auth
BOT_WORKER_SECRET=your-secret bash deploy/smoke-test.sh
```

**Критерий прохождения:** `ALL TESTS PASSED` (exit code 0).

---

## 12. Критерии "GO / NO-GO"

| Условие | GO | NO-GO |
|---------|-----|-------|
| Smoke suite exit code | 0 (все пройдено) | > 0 (есть падения) |
| Утечка секретов | Нет | Есть |
| Нарушение workspace isolation | Нет | Есть |
| 5xx на health/auth endpoints | Нет | Есть |
| systemd services active | Оба active | Любой не active |
| Bot worker online | Да | Нет |

---

## Версия и тег

Перед пометкой RC создать git-тег:
```bash
git tag -a v0.1.0-rc1 -m "Release Candidate 1 — Stage 14 complete"
git push origin v0.1.0-rc1
```

Деплой по тегу:
```bash
# На VPS
cd /opt/-botmarketplace-site
git fetch --tags
git checkout v0.1.0-rc1
bash deploy/deploy.sh --ref v0.1.0-rc1
```

---

*Документ обновлён: Stage 14 — Release Candidate Pack*
