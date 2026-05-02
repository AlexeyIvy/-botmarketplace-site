# Operations (MVP)

Минимальные практики эксплуатации: логи, ротация, бэкапы, мониторинг.

## 1) Логи

MVP:
- systemd services пишут в stdout/stderr -> journald.
- Просмотр: `journalctl -u botmarket-api -f`, `journalctl -u botmarket-worker -f`.

SHOULD:
- Включить persistent journald, чтобы логи переживали reboot.
  - При `Storage=auto` journald пишет в `/var/log/journal/` только если каталог существует; иначе пишет неперсистентно в `/run/log/journal/`. [web:779]
  - Явный вариант: `Storage=persistent` в `journald.conf`, затем рестарт journald. [web:779]

## 2) Ротация логов

Если есть отдельные файлы логов (app/*.log), используем logrotate.

Смысл ключей (примерно):
- `missingok`: не ругаться, если файла нет.
- `daily`: ротация ежедневно.
- `compress`: сжимать старые логи (gzip по умолчанию).
Это соответствует описанию параметров logrotate. [web:780]

## 3) Бэкапы

MVP MUST:
- Бэкап БД (если PostgreSQL) минимум 1 раз в сутки + хранение N дней.
- Бэкап секретов не делаем “как есть”; секреты храним в менеджере секретов/в env, доступ ограничен.

MVP SHOULD:
- Проверять восстановление (restore test) хотя бы раз в неделю на отдельном окружении.

## 4) Мониторинг и алерты (минимум)

MVP SHOULD:
- Health endpoints: `/api/healthz` и `/api/readyz`.
- Алерты: недоступность API, падение worker, частые рестарты systemd.

## 5) Runbooks

MVP MUST:
- Инструкция “что делать если”: WS reconnection storm, частые rate limits, не выставляются SL/TP, зависли ордера.

## 6) Trading kill switches and incident response

These are the levers for stopping or scoping down trading activity. They
are referenced from the production go/no-go gate (`docs/54-T6 §3` —
"Ops runbook"). Every command below assumes the operator has
shell + DB access on the API host.

### 6.1) Stop the embedded bot worker

`server.ts` reads `DISABLE_EMBEDDED_WORKER`. Setting it to a non-empty
value and restarting the API process drains the in-flight tick and
prevents new ticks from running:

```bash
DISABLE_EMBEDDED_WORKER=true systemctl restart botmarket-api
```

Existing `BotIntent` rows in PENDING / PLACED states stay in their
current state; they will not progress until the worker resumes or a
standalone worker process is started.

### 6.2) Stop only the funding-arb hedge worker

`apps/api/src/lib/hedgeBotWorker.ts` is gated by `ENABLE_HEDGE_WORKER`.
Default is off, so funding-arb does not tick unless explicitly enabled.
To halt it without affecting the mainline DSL `botWorker`:

```bash
unset ENABLE_HEDGE_WORKER          # or set to "false"
systemctl restart botmarket-api    # if the hedge worker is in-process
```

Open `HedgePosition` rows are left as-is. Audit them via:

```sql
SELECT id, symbol, status, "createdAt", "closedAt"
FROM "HedgePosition"
WHERE status IN ('OPEN', 'OPENING', 'CLOSING')
ORDER BY "createdAt" DESC;
```

If any non-CLOSED row needs to be unwound, see §6.5.

### 6.3) Demo-only trading (force-no-live)

`apps/api/src/lib/bybitOrder.ts` reads `BYBIT_ENV`. Setting it to `demo`
(or unsetting it; demo is the default) routes every Bybit private call
to `https://api-demo.bybit.com`:

```bash
BYBIT_ENV=demo systemctl restart botmarket-api
```

A global `TRADING_ENABLED` admin flag is referenced by the go/no-go
gate template — it does NOT yet exist. Pre-production hardening must
add it before live is enabled. Until then, `BYBIT_ENV=demo` plus
`DISABLE_EMBEDDED_WORKER=true` are the documented levers.

### 6.4) Roll a preset back from PUBLIC to PRIVATE without deleting it

Use the `publishPreset.ts` admin CLI (does not delete the preset, just
hides it from non-admin `/presets` listings and `/presets/:slug`):

```bash
pnpm --filter @botmarketplace/api exec tsx scripts/publishPreset.ts \
  --slug <preset-slug> --visibility PRIVATE
```

Add `--dry-run` to preview the diff first. Existing bots already
instantiated from the preset are not affected — they keep running off
their copied DSL. Only new instantiations are blocked.

### 6.5) Diagnose a stuck bot run

A `botRun` is "stuck" when it has not advanced its `state` for longer
than `MAX_RUN_DURATION_MS` (4h default) or when it sits in a
non-terminal state with a stale `leaseUntil`.

```sql
-- Stale leases — worker likely crashed mid-tick
SELECT id, "botId", state, "leaseOwner", "leaseUntil", "startedAt"
FROM "BotRun"
WHERE state NOT IN ('STOPPED', 'FAILED', 'TIMED_OUT')
  AND "leaseUntil" < NOW() - INTERVAL '2 minutes'
ORDER BY "leaseUntil" ASC;

-- In-flight intents tied to a single run
SELECT "intentId", type, state, side, qty, "createdAt"
FROM "BotIntent"
WHERE "botRunId" = '<run-id>'
ORDER BY "createdAt" DESC;
```

`releaseOwnedLeases()` (worker shutdown path) clears the lease when
the worker exits cleanly. If it didn't run, manually clear the lease
via SQL and the next tick will pick the run up:

```sql
UPDATE "BotRun"
SET "leaseOwner" = NULL, "leaseUntil" = NULL
WHERE id = '<run-id>';
```

If the run itself should be stopped: transition it to STOPPING via the
HTTP API (`POST /runs/:id/stop`) — the worker honours the transition
on its next tick.

