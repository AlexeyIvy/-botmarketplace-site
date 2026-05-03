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

### 6.3) Halt outbound order placement (TRADING_ENABLED)

`apps/api/src/lib/tradingKillSwitch.ts` reads the `TRADING_ENABLED` env
variable on every order-placement call. Setting it to a false-literal
value (`false` / `0` / `no` / `off`, case-insensitive) and restarting
the API process halts every outbound `bybitPlaceOrder` call at the
lowest layer of the stack:

```bash
TRADING_ENABLED=false systemctl restart botmarket-api
```

Behaviour:

- Read-only paths (status fetch, market data, balance reconciliation)
  are NOT guarded — operators can still diagnose during an incident.
- Pending intents are NOT auto-cancelled. The order placement throws
  `TradingDisabledError` (classified as `transient` by `errorClassifier`),
  so the worker retry loop picks the order up on the next tick once
  the flag flips back. No manual re-queuing required.
- For active funding-arb hedges this means **both legs park in
  PENDING** for the duration of the kill switch — `summariseLegStates`
  sees neither `bothFilled` nor a terminal failure and the hedge stays
  in `OPENING` / `CLOSING`. See §6.6 for inspection queries.
- Default is fail-open (env unset → enabled), so dev / demo
  environments keep working without an explicit setting.

If the goal is "demo-only trading" rather than full halt, prefer
`BYBIT_ENV=demo` instead — same restart command, different env
variable. `BYBIT_ENV` routes private calls to
`https://api-demo.bybit.com` while keeping the worker alive.

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

### 6.6) Diagnose a stuck hedge (funding-arb)

The hedge worker's state machine is more constrained than a DSL bot run
— a hedge passes through five persisted statuses, each driven by leg
intents emitted on the previous tick. Mapping (skeleton-stage ↔
`HedgePosition.status`):

| Skeleton stage  | Persisted `status` | Meaning |
|---|---|---|
| `PENDING`       | `PLANNED`  | Awaiting funding-window signal. |
| `ENTRY_PLACED`  | `OPENING`  | Both entry legs emitted, awaiting fills. |
| `ACTIVE`        | `OPEN`     | Both entry legs FILLED, awaiting funding payment. |
| `EXIT_PLACED`   | `CLOSING`  | Exit legs emitted, awaiting fills. |
| `CLOSED`        | `CLOSED`   | Both exit legs FILLED. Terminal. |
| `ERRORED`       | `FAILED`   | Partial fill / unrecoverable. Terminal. |

A hedge is "stuck" if it sits in a non-terminal status (`PLANNED`,
`OPENING`, `OPEN`, `CLOSING`) for materially longer than the next
funding event would take to clear (Bybit settles every 8h; budget 30
minutes either side). Most stuck cases are explainable by one of:

- `TRADING_ENABLED` flipped to off mid-hedge (§6.3) — legs park in
  PENDING, status stays `OPENING` / `CLOSING` until the flag flips back.
- `ENABLE_HEDGE_WORKER` was unset (§6.2) — the tick loop never runs.
- `FundingSnapshot.nextFundingAt` is missing or stale for the symbol —
  `windowDetector` returns `paymentReceived=false` indefinitely and a
  hedge in `OPEN` cannot transition to `EXIT_PLACED`. Check the funding
  ingestion cron.

**Inspection queries.** All three feed back into the same hedge id;
copy it once and reuse:

```sql
-- 1. List non-terminal hedges by age — oldest first
SELECT id, symbol, status, "createdAt", "closedAt"
FROM "HedgePosition"
WHERE status IN ('PLANNED', 'OPENING', 'OPEN', 'CLOSING')
ORDER BY "createdAt" ASC;

-- 2. Both leg intents for a single hedge — order is entry then exit
SELECT "intentId", type, state, side, qty, "metaJson"->>'category' AS category, "createdAt"
FROM "BotIntent"
WHERE "metaJson"->>'hedgeId' = '<hedge-id>'
ORDER BY "createdAt" ASC;

-- 3. Latest funding snapshot for the hedge symbol
SELECT symbol, "fundingRate", "nextFundingAt", timestamp
FROM "FundingSnapshot"
WHERE symbol = '<symbol>'
ORDER BY timestamp DESC LIMIT 1;
```

Query 1 lists candidates; query 2 reveals which leg is parked and why
(e.g. `state = PENDING` × `category = spot` ⇒ spot-leg never executed,
typically because 55-T2 wiring is not yet in place on this environment);
query 3 confirms the funding-window upstream is fresh.

**Log filter.** All hedge-worker output carries `module:
"hedgeBotWorker"`. Stage transitions are logged at `info`, errors and
balance-reconcile failures at `error`:

```bash
journalctl -u botmarket-api -o cat | jq 'select(.module == "hedgeBotWorker")'
```

**Manual unwind (last resort).** If a hedge must be retired without
waiting for the worker — e.g. the strategy spec changed and the
in-flight legs are wrong — first transition each leg's `BotIntent` to
`CANCELLED` via the existing intent-state endpoint:

```bash
# Repeat for both intentIds returned by query 2 above. The endpoint
# rejects already-terminal intents with 409 — that's fine, just skip.
curl -X PATCH https://api.example.com/api/v1/runs/<run-id>/intents/<intent-id>/state \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"state":"CANCELLED"}'
```

Then manually transition the hedge:

```sql
-- Mark a hedge as terminally failed without touching legs
UPDATE "HedgePosition" SET status = 'FAILED', "closedAt" = NOW()
WHERE id = '<hedge-id>' AND status IN ('PLANNED', 'OPENING', 'OPEN', 'CLOSING');
```

The hedge worker honours the terminal status on its next tick — once
`status IN ('CLOSED', 'FAILED')` it stops considering the row entirely.
Do **not** flip a hedge backward (e.g. `OPENING → PLANNED`); the worker
re-emits leg intents when it sees `PLANNED + fundingWindowOpen` and
will create duplicate orders.

