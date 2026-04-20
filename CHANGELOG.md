# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Policy:** every PR must append at least one entry to `[Unreleased]`.
Entries get promoted to a versioned section on release (see
[RUNBOOK §3.4](docs/runbooks/RUNBOOK.md#34-тегирование-rc)).

## [Unreleased]

### Added

- Lab: "Preview 24h" button in the Build context bar. Opens a popover with
  trades / win rate / max drawdown / net PnL + an inline SVG equity
  sparkline for the most recently compiled DSL. Enabled after a
  successful compile; surfaces RFC 9457 validation errors inline and
  reports data-freshness lag via the response's `dataAgeMs`. (§5.12)
- `deploy/rollback.sh` with auto-detected previous tag, `--dry-run`,
  `--to`, `--yes`; warns on forward-only DB migrations. RUNBOOK §3.5.
  (§5.1, #277)
- Startup `validateBybitEnv()` — logs `[BYBIT MODE: LIVE|DEMO]` and refuses
  to start in `NODE_ENV=production` + `BYBIT_ENV=live` unless
  `BYBIT_ALLOW_LIVE=true`. (§5.10, #276)
- Periodic reconciler (`lib/periodicReconciler.ts`): stale-PENDING sweep
  cancels PENDING intents older than 10m in RUNNING runs; orphan-lease
  reclaim transfers leases from dead workers to the live one. New
  counters `botmarket_stale_pending_cancelled_total` +
  `botmarket_orphan_leases_reclaimed_total`. (§4.5.2, §4.5.3, #274, #275)
- `/readyz` health probe with systemd timer + Telegram/Slack webhook
  alerts on 2 consecutive failures. `deploy/healthcheck.sh` + new
  RUNBOOK §10 "Мониторинг и алерты". (Action 3, #272)
- Optional Sentry integration via `SENTRY_DSN` — no-op when unset; 5xx
  errors emit `captureException` with `reqId` context. (Action 3, #271)
- Prometheus `/metrics` endpoint with `prom-client` — default process
  metrics, intent counters, and HTTP request-duration histogram.
  nginx restricts external access to loopback. (Action 3, #270)
- GitHub Actions CI (typecheck + test:api + check:stray) and Dependabot
  weekly security updates. (Action 2, #257)
- Production readiness audit `docs/37-production-readiness-audit.md` —
  11-axis review + prioritised action plan. (#255)

### Changed

- CSP is now split between nginx (web pages) and API (JSON responses).
  nginx no longer adds CSP on `/api/*`; the API's strict
  `default-src 'none'; frame-ancestors 'none'` is the single source of
  truth for JSON. (§5.8, #279)
- `stopWorker()` now releases `leaseUntil` on graceful shutdown so a
  restarting worker can claim immediately instead of waiting the 30s
  natural expiration window. (§4.5.1, #273)
- `DATABASE_URL` in `.env.example` now includes explicit
  `connection_limit=10` + `pool_timeout=10`. RUNBOOK §2 documents the
  sizing tradeoffs against Postgres `max_connections`. (§5.3, #278)

### Security

- Closed 12 prod-dep vulnerabilities (2 CRITICAL + 4 HIGH + 6 MODERATE)
  via `fastify ^5.8.4`, `next ^15.5.15`, and pnpm.overrides for
  `fast-jwt` / `defu`. (Action 1, #256)

### Docs

- RUNBOOK additions: §3.5 rollback procedure, §10 observability + alerts,
  §2 Prisma pool config + new env vars (`POOL_WAIT_THRESHOLD`,
  `BYBIT_ALLOW_LIVE`).

---

## Earlier history (pre-audit)

Condensed; see `git log --oneline` + referenced PRs for detail.

- #253 — block stray TS emission + add check/cleanup tooling
- #249, #250 — Lab Task 29 AI Explainability + hardening
- #245 — Lab Task pack 26 Governance / Provenance
- #228, #230–#235 — Roadmap V4 Batch 3: tests, security hardening, worker refactor
- #218 — server-side refresh token revocation
- #208 — worker extraction (#21) + WebSocket integration (#19)
- #207 — global React ErrorBoundary + client error reporting endpoint
- #206 — dead-letter queue for failed intents with retry logic
- #205 — optimistic locking for BotRun state transitions
- #204 — `/readyz` extended with worker health, encryption key, stuck runs
- #201 — JWT hardening: 1h access token, refresh rotation, prod secret enforce
- Initial documentation set — Bybit integration, Strategy DSL, bot runtime,
  API contracts, security, deployment, operations runbooks
