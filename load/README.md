# Load tests (k6)

Addresses `docs/37` §5.2. Small set of [k6](https://k6.io/) scenarios so
we can measure latency + capacity rather than guess. Not wired into CI
by default — the audit suggests "optional, only on main push"; run
locally or on a dedicated load-gen VPS when capacity planning or before
a major release.

## Install k6

macOS: `brew install k6`. Linux: see
[k6.io/docs/getting-started/installation](https://k6.io/docs/getting-started/installation/).

## Scenarios

| File                | Endpoint                | Purpose                                                     |
|---------------------|-------------------------|-------------------------------------------------------------|
| `healthz.js`        | `GET /healthz`          | Baseline — p99 floor, pure Fastify handler, no DB           |
| `auth-login.js`     | `POST /api/v1/auth/login` | Bcrypt-heavy path; invalid path validates rate-limit 429s  |
| `bots-list.js`      | `GET /api/v1/bots`      | Auth'd read — JWT verify + Prisma findMany, typical dashboard |

## Run

```bash
# Baseline
BASE_URL=http://localhost:4000 k6 run load/healthz.js

# Auth — seed a test user first
curl -s http://localhost:4000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"seed@example.com","password":"Seed1234!"}'

BASE_URL=http://localhost:4000 \
  LOAD_EMAIL=seed@example.com LOAD_PASS=Seed1234! \
  k6 run load/auth-login.js

# Dashboard polling
BASE_URL=http://localhost:4000 \
  LOAD_EMAIL=seed@example.com LOAD_PASS=Seed1234! \
  k6 run load/bots-list.js
```

## Thresholds

Each scenario defines its own `options.thresholds`. Summary of baselines
we've committed to:

- `/healthz`: p95 < 100 ms, p99 < 250 ms at 50 rps
- `/auth/login` (valid): p95 < 1000 ms, p99 < 2000 ms (bcrypt is
  deliberately slow; this is a soft ceiling under ~10 rps)
- `/api/v1/bots`: p95 < 300 ms, p99 < 500 ms up to 50 concurrent VUs

If a threshold fails, k6 exits non-zero and prints the failing
metric — use the failure as a signal to investigate before release, not
as a hard merge gate.

## Interpreting output

- `http_req_duration` — total latency including network; best single
  metric for user-facing responsiveness.
- `http_req_failed` — share of non-2xx responses. Rate-limit scenarios
  expect some 429s and filter them via tags.
- `custom Trend metrics` — per-endpoint view (e.g. `bots_list_latency_ms`)
  so you can compare regressions over time.

## Capacity planning

Current rate-limit baseline (API):

- `/auth/login`: 5 req / 15 min per IP
- global default: 100 req / min per IP
- `/terminal/*`, `/funding/*`, `/hedges/*`: 30 req / min
- `/client-errors`: 3 req / min

Use the scenarios to confirm headroom after tuning any of these.
