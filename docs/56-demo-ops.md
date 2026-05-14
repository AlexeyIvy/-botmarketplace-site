# 56. Demo Environment — Ops Runbook

> **Status:** authoritative for the demo VPS (`/opt/-botmarketplace-site`).
> **Last updated:** 2026-05-14.
> **Scope:** day-to-day operations on the demo box — what each
> component is, how to start an acceptance run from scratch, how to
> diagnose common failures. Complementary to `docs/14-deployment.md`
> (initial deploy + privilege model), `docs/15-operations.md` (kill
> switches, generic diagnostics) and
> `docs/53-baseline-results.md` / `docs/54-baseline-results.md`
> (preset acceptance via the `demoSmoke.ts` harness).

---

## 1) Architecture summary

Three systemd units run on the demo VPS:

- `botmarket-api` — Fastify HTTP API on `127.0.0.1:4000`. **Not**
  `:3000` — that port belongs to the web tier.
- `botmarket-web` — Next.js front-end on `127.0.0.1:3000`. Does not
  proxy `/api/*` — direct API calls must hit `:4000` (or go through
  nginx).
- `botmarket-worker` — the dedicated worker unit exists for a future
  split; today the bot worker runs in-process inside `botmarket-api`
  (see `DISABLE_EMBEDDED_WORKER` in `docs/15 §6.1`).

External plumbing:

- `nginx` — reverse proxy, `/` → web, `/api/` → api. See
  `docs/14 §3` for header forwarding requirements.
- PostgreSQL — local, connection in `/opt/-botmarketplace-site/.env`
  as `DATABASE_URL`.

Repo path: `/opt/-botmarketplace-site`, tracking `main`. Deploy
through `sudo bash /opt/-botmarketplace-site/deploy/deploy.sh`
(`docs/14 §6` covers the privilege model — script runs as root and
contains no internal `sudo` calls).

## 2) Connection cheat-sheet

| Resource | Value |
| --- | --- |
| Repo path | `/opt/-botmarketplace-site` |
| Env file | `/opt/-botmarketplace-site/.env` |
| API host:port (internal) | `127.0.0.1:4000` |
| Web host:port (internal) | `127.0.0.1:3000` |
| API base path | `/api/v1` |
| Health probe | `GET http://127.0.0.1:4000/api/v1/readyz` |
| systemd units | `botmarket-api`, `botmarket-web`, `botmarket-worker` |
| Logs | `journalctl -u botmarket-api --since "..." --no-pager` |
| Deploy command | `sudo bash /opt/-botmarketplace-site/deploy/deploy.sh` |
| Rollback tags | `git tag -l 'vps-pre-deploy-*'` (newest first) |

## 3) Market data: candle ingest model

The demo environment has **no realtime candle ingest**.
`MarketCandle` rows are inserted only via the admin `POST /datasets`
route (`apps/api/src/routes/datasets.ts:151`); there is no scheduled
fetch from Bybit on this stack. Tracked in #400.

Practical consequences:

- An acceptance run executes against a fixed candle window. DSL
  evaluation is deterministic across reruns until the next admin
  upload — re-running the same bot on the same candles produces the
  same intent ladder.
- `MarketCandle` rows go stale between uploads; freshness must be
  checked before every acceptance session.
- The `dataset_insufficient` BotEvent (#397) only fires when the
  candle window holds fewer than 2 rows
  (`apps/api/src/lib/botWorker.ts:1445-1446`). With backfilled
  historical data (typical for `BTCUSDT`: ~8640 M5 rows / ~1854 H1
  rows over ~30 days) this condition does not arise from staleness
  alone — it requires either a misconfigured TF or an intentionally
  pruned table.

Refresh procedure (operator):

1. Identify the symbol(s) and interval(s) needed by the bots that
   will run.
2. Use the lab dataset upload flow (`docs/55-T6`) or
   `POST /datasets` directly to ingest a recent window from Bybit.
3. Confirm via the SQL in §6.1 (`MarketCandle` freshness) before
   instantiating bots.

## 4) Acceptance run from scratch — direct POST flow

For preset acceptance via the canonical harness, see
`docs/53-baseline-results.md §2` — `apps/api/scripts/demoSmoke.ts`
wraps preset instantiation, run-start, monitoring, and writes a
report file. The harness is the right tool for go/no-go gates.

This section documents the **lower-level direct flow** instead:
useful for re-running an existing already-instantiated bot, for
ad-hoc diagnostic runs that bypass the harness, and as the building
block for the harness itself.

### 4.1) Pre-check (read-only)

Run all of the following before any write:

```bash
# 1. HEAD matches the deployed commit (compare against the last
#    deploy log in /tmp/deploy-*.log or your deploy notes)
git -C /opt/-botmarketplace-site rev-parse HEAD

# 2. API + worker health
curl -fsS http://127.0.0.1:4000/api/v1/readyz | jq

# 3. systemd units
systemctl is-active botmarket-api botmarket-web botmarket-worker
```

SQL through `psql "$DATABASE_URL"`:

```sql
-- Bot state in the target workspace
SELECT b.id, b.symbol, b.timeframe, b.status, b."datasetBundleJson",
       (SELECT state FROM "BotRun" r WHERE r."botId" = b.id
         ORDER BY r."createdAt" DESC LIMIT 1) AS last_run_state
FROM "Bot" b
WHERE b."workspaceId" = '<WORKSPACE_ID>'
ORDER BY b."createdAt";

-- Candle freshness for the bot's primary TF + each bundle TF
SELECT symbol, interval, COUNT(*) AS rows,
       MAX("openTimeMs") AS max_ts,
       ((EXTRACT(EPOCH FROM NOW())*1000)::bigint - MAX("openTimeMs"))
         / 60000 AS lag_min
FROM "MarketCandle"
WHERE symbol = '<SYMBOL>' AND interval IN ('M5', 'H1')
GROUP BY symbol, interval
ORDER BY interval;
```

Gates before proceeding to §4.2:

- `HEAD` matches the expected deployed commit.
- All three systemd units `active`.
- `/api/v1/readyz` returns 200 with every component `ok`.
- Target bot is `ACTIVE` with no active `BotRun` — `last_run_state`
  is `STOPPED` / `FAILED` / `TIMED_OUT` or NULL.
- `MarketCandle` row count is at least the engine lookback (200 by
  default — `apps/api/src/lib/botWorker.ts:1419`) for every TF in
  the bot's `datasetBundleJson`.

If candles are stale but row-count-sufficient, the run executes
deterministically against the stale window — that is by design
(see §3). Re-upload only when fresh data matters for the test.

### 4.2) Generate a JWT (HS256)

The API uses `@fastify/jwt` (`apps/api/src/app.ts:125`) with
`JWT_SECRET` from env. `node:crypto` is enough — no `jsonwebtoken`
dependency needed:

```bash
set -a; . /opt/-botmarketplace-site/.env; set +a
JWT=$(SUB='<USER_ID>' node -e '
const c = require("crypto");
const s = process.env.JWT_SECRET, sub = process.env.SUB;
const now = Math.floor(Date.now() / 1000);
const h = { alg: "HS256", typ: "JWT" };
const p = { sub, iat: now, exp: now + 3600 };
const b = (o) => Buffer.from(JSON.stringify(o)).toString("base64url");
const si = b(h) + "." + b(p);
const sig = c.createHmac("sha256", s).update(si).digest("base64url");
console.log(si + "." + sig);
')
```

Verify before using for anything else:

```bash
curl -fsS -H "Authorization: Bearer $JWT" \
  http://127.0.0.1:4000/api/v1/auth/me | jq '.id, .email'
```

Expected: HTTP 200 with `id` equal to `<USER_ID>`. A 401 means the
`JWT_SECRET` loaded in the shell does not match the one the API
process started with — typically because the env file was edited
after the last `systemctl restart botmarket-api`.

### 4.3) Start the run

```bash
WORKSPACE='<WORKSPACE_ID>'
BOT_ID='<BOT_ID>'

curl -sS -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "X-Workspace-Id: $WORKSPACE" \
  -H "Content-Type: application/json" \
  -d '{"durationMinutes":5}' \
  "http://127.0.0.1:4000/api/v1/bots/$BOT_ID/runs" | jq
```

Expected: HTTP 201 returning the new `BotRun` with `state="QUEUED"`.
The in-process worker picks it up within one poller tick (~3–5 s) and
transitions `CREATED → QUEUED → STARTING → SYNCING → RUNNING`.

`durationMinutes` ∈ `[1, 1440]`. The worker enforces termination via
`timeoutExpiredRuns` (`apps/api/src/lib/botWorker.ts:505-516`) —
terminal state is `TIMED_OUT`, **not** `STOPPED`. `STOPPED` only
results from an explicit
`POST /api/v1/bots/:botId/runs/:runId/stop`.

A 409 on the POST means there is already an active run for this bot
or for the workspace + symbol pair — see §5.2.

### 4.4) Monitor

Wait `durationMinutes * 60` seconds plus ~10 s for the poller cycle,
then read state and events:

```sql
SELECT id, state, "startedAt", "endedAt",
       EXTRACT(EPOCH FROM ("endedAt" - "startedAt")) AS duration_sec
FROM "BotRun" WHERE id = '<RUN_ID>';

SELECT ts, type, "payloadJson"
FROM "BotEvent"
WHERE "botRunId" = '<RUN_ID>'
ORDER BY ts;

SELECT type, COUNT(*) FROM "BotEvent"
WHERE "botRunId" = '<RUN_ID>' GROUP BY type ORDER BY 2 DESC;

SELECT id, "intentId", state, side, qty, "createdAt"
FROM "BotIntent" WHERE "botRunId" = '<RUN_ID>'
ORDER BY "createdAt";
```

Logs for the run window:

```bash
journalctl -u botmarket-api --since "<START_AT_UTC>" --no-pager \
  > /tmp/run-<RUN_ID>.log
```

### 4.5) Acceptance gates

For a typical multi-TF bundle run, expect:

- `BotRun.state = TIMED_OUT` (or `STOPPED` if manually stopped).
- `duration_sec ≈ durationMinutes * 60` (±20 s for the poller cycle).
- Zero occurrences in the log of any of:
  - `"datasetBundleJson failed validation"` — bundle parse failure
    (`Bot.datasetBundleJson` round-trip; this is the #398 hot path).
  - `"loadCandleBundle failed"` — runtime candle loader error.
  - `"MtfBundleRequiredError"` — a DSL ref carries `sourceTimeframe`
    but the runtime `mtfContext` is `null` or missing that TF.
  - `"evaluateStrategies.*error"` — uncaught strategy-engine
    exception.
- Zero `BotEvent.type='dataset_insufficient'` rows. (Expected zero
  on any run started against a candle window with ≥ 2 rows; a
  non-zero count indicates either runtime starvation or a config
  pointing at a TF with no data — see §5.3.)

Informational, not gating:

- `BotIntent` count — can legitimately be 0 on a flat market or a
  short run.
- `signal_entry` / `signal_exit` BotEvent counts — these feed into
  `strategyActivityCount` if reconciling with `demoSmoke.ts`-style
  reports (`apps/api/scripts/demoSmoke.ts:589`).

## 5) Troubleshooting

### 5.1) `/api/v1/readyz` returns 503 or a component is not `ok`

Read the last ~200 lines of `botmarket-api` logs:

```bash
journalctl -u botmarket-api -n 200 --no-pager
```

Common causes: DB connection error (network / credentials), missing
env var raised at startup, partial migration. The readyz JSON
breakdown identifies the failing component — fix that first.

### 5.2) `409 ActiveRunExists` on `POST /runs`

A `BotRun` row for this bot, or for another bot in the same
workspace on the same symbol, sits in a non-terminal state. The
single-active-run partial index in the DB enforces the symbol-level
side of this invariant.

Inspect:

```sql
SELECT id, state, "leaseUntil", "startedAt"
FROM "BotRun"
WHERE "botId" = '<BOT_ID>'
  AND state NOT IN ('STOPPED', 'FAILED', 'TIMED_OUT')
ORDER BY "startedAt" DESC;
```

If the run is genuinely stuck, prefer
`POST /api/v1/bots/:botId/runs/:runId/stop` over direct DB edits —
the worker honours the transition on its next tick. For lease-only
stalls see `docs/15 §6.5`.

### 5.3) `dataset_insufficient` BotEvent during a run

Emitted by `botWorker.evaluateStrategies` when the candle window for
the run's primary TF holds < 2 rows
(`apps/api/src/lib/botWorker.ts:1445-1446`). De-duplicated per
`(runId, symbol, interval)` — one event per sufficient →
insufficient transition (#397).

Inspect:

```sql
SELECT "payloadJson"
FROM "BotEvent"
WHERE "botRunId" = '<RUN_ID>' AND type = 'dataset_insufficient'
ORDER BY ts;
```

Payload: `{ symbol, interval, candleCount, requiredCount }`. On the
demo environment (manual ingest only — §3) this is most often
caused by either:

- Pointing a bot at a TF with no uploaded data (configured `M5` but
  only `H1` rows exist for the symbol), or
- A bundle TF (`H1`) being empty while the primary TF (`M5`) has
  data — runtime `mtfContext` build may still proceed but multi-TF
  refs will produce `NaN` (see `docs/52-multi-interval-dataset-bundle.md`).

Fix by re-uploading the missing TF (§3 procedure).

### 5.4) `loadCandleBundle failed` in the log

Logged at `error` by `botWorker.evaluateStrategies` when
`loadCandleBundle` throws. The bundle is skipped for that tick
(`continue`); the run does not crash but it also makes no progress
and emits no signals.

Common causes:

- `Bot.datasetBundleJson` has a TF key absent from the allowed set
  (UPPER: `M1` / `M5` / `M15` / `H1` / `H4` / `D1` — see
  `apps/api/src/types/datasetBundle.ts`).
- Bundle requests more lookback than exists for one of the TFs.

The error object carries `field` and `message` — pull the full log
line for the runId.

### 5.5) `MtfBundleRequiredError` from a DSL ref

A DSL signal/exit references an indicator with `sourceTimeframe`,
but the runtime `mtfContext` is `null` — usually because the bot's
primary TF (`Bot.timeframe`) is absent from `TIMEFRAME_TO_INTERVAL`
(`apps/api/src/lib/mtf/intervalAlignment.ts`). `M30` is the canonical
"allowed-but-unaligned" case today.

If the strategy was authored before the multi-TF refactor, check
that `Bot.datasetBundleJson` is populated **and** that the primary
TF is one of the aligned set.

### 5.6) JWT 401 against `/auth/me`

`JWT_SECRET` mismatch between the shell-loaded env and the API
process. The API loads its env at startup; rotating the secret
requires `systemctl restart botmarket-api` to pick up the new
value. Regenerate the JWT after the restart completes.

## 6) Common diagnostic queries

### 6.1) `MarketCandle` freshness per symbol/TF

```sql
SELECT symbol, interval,
       COUNT(*) AS rows,
       MAX("openTimeMs") AS max_ts,
       to_timestamp(MAX("openTimeMs")/1000.0) AT TIME ZONE 'UTC'
         AS max_at_utc,
       ((EXTRACT(EPOCH FROM NOW())*1000)::bigint - MAX("openTimeMs"))
         / 60000 AS lag_min
FROM "MarketCandle"
GROUP BY symbol, interval
ORDER BY symbol, interval;
```

### 6.2) Recent `BotRun`s across all bots in a workspace

```sql
SELECT r.id, b.symbol, r.state, r."createdAt", r."endedAt"
FROM "BotRun" r
JOIN "Bot" b ON b.id = r."botId"
WHERE b."workspaceId" = '<WORKSPACE_ID>'
ORDER BY r."createdAt" DESC
LIMIT 20;
```

### 6.3) Last-N `BotEvent`s for a bot

```sql
SELECT r.id AS "runId", e.ts, e.type, e."payloadJson"
FROM "BotEvent" e
JOIN "BotRun" r ON r.id = e."botRunId"
WHERE r."botId" = '<BOT_ID>'
ORDER BY e.ts DESC
LIMIT 50;
```

### 6.4) Active leases (worker health proxy)

```sql
SELECT id, "botId", state, "leaseOwner", "leaseUntil"
FROM "BotRun"
WHERE state NOT IN ('STOPPED', 'FAILED', 'TIMED_OUT')
ORDER BY "leaseUntil" ASC NULLS LAST;
```

## 7) Related docs

- `docs/14-deployment.md` — VPS deploy, systemd units, nginx,
  `deploy.sh` privilege model (#3, #399).
- `docs/15-operations.md` — kill switches, stuck-run / stuck-hedge
  runbooks, log conventions.
- `docs/52-multi-interval-dataset-bundle.md` — multi-TF data model
  used by §4.5 acceptance gates.
- `docs/53-baseline-results.md` / `docs/54-baseline-results.md` —
  preset acceptance harness (`demoSmoke.ts`).
- #397 — runtime `dataset_insufficient` BotEvent.
- #398 — `datasetBundleJson` materialization at instantiate.
- #400 — demo candle ingest gap (open).
