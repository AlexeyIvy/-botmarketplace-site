# Production Readiness Audit

**Status:** Audit complete (docs-only, no code changes)
**Date:** 2026-04-12
**Author role:** Senior Software Engineer (audit-only output)
**Change type:** Docs-only. No fixes applied in this PR — каждый gap становится отдельной follow-up задачей.

---

## 1. Purpose & scope

Проект закрыл крупные roadmap-вехи (Stage 1–9, Phase 2B, Phase 6 lab, DSL↔graph feasibility spike в `docs/36`), и на бумаге статус выглядит как "MVP complete". Этот документ отвечает на один узкий вопрос:

> **Может ли живой пользователь запустить demo-бота на нашей инфраструктуре, оставить его работать 24/7 и быть уверенным, что:**
> **(а) его данные и ключи в безопасности,**
> **(б) об инцидентах мы узнаем раньше него,**
> **(в) после перезагрузки/сбоя система восстановится без ручного вмешательства?**

Аудит фиксирует разрыв между "roadmap done" и "production-ready" в текущем виде кодовой базы (HEAD `0db6677`). Он не ставит новых целей продукта — только перечисляет, чего не хватает для честного production-режима.

**In scope:**
- CI/CD, security posture, observability, backups, graceful lifecycle, deploy/rollback, runbooks, tests, secrets, runtime safety, doc hygiene.
- Только факты из репозитория и вывода `pnpm audit`. Никаких предположений о внешних системах.

**Out of scope:**
- Дизайн исправлений (effort-sizing — да; technical design — нет).
- Новые фичи продукта.
- Решение о приоритезации — оно остаётся за владельцем проекта.
- Пенетрейшн-тестирование, аудит криптопримитивов. Упоминаем только то, что видно по коду и версиям.

---

## 2. Methodology

Аудит выполнен по следующему протоколу:

1. **Inventory.** Перечислить, что уже сделано, по 11 функциональным осям (см. §7). Исходники — `deploy/*`, `apps/api/src/*`, `docs/runbooks/*`, `docs/README.md`, `package.json`, `pnpm-lock.yaml`.
2. **Gap detection.** Для каждой оси ответить: "что ломается, если A/B/C произойдёт завтра?" (A = критическая уязвимость в зависимости; B = VPS перезагрузка; C = флап exchange API; D = жалоба пользователя на пропавший ордер).
3. **Ranking.** Каждый gap получает severity: CRITICAL (блокирует реальное использование / риск потери средств / CVE в trading path), HIGH (увеличивает MTTR инцидента в разы, но не блокирует), MEDIUM (качество жизни, debt).
4. **Top-5 cut.** Самые критичные 5 выносим в §4 с effort estimate. Остальное — в §5.
5. **Next actions.** Рекомендация по первым трём шагам с обоснованием порядка (§6).

Audit не перепроверяет корректность fix-скриптов (`scripts/clean-stray-ts-artifacts.sh`), acceptance тесты или работоспособность lab — все они считаются green по результату PR #252–#254.

---

## 3. Current state inventory

Короткий срез по 11 осям — подробности в §7.

| # | Ось | Что есть | Ключевой gap |
|---|---|---|---|
| 1 | **CI/CD** | Скрипты `pnpm test:api`, `pnpm check:stray`, `tsc --noEmit`, `deploy/smoke-test.sh` | Нет `.github/workflows/` — ни один PR не проверяется автоматически |
| 2 | **Security (deps)** | `@fastify/jwt`, AES-256-GCM для exchange keys, bcryptjs для паролей | `pnpm audit --prod`: 2 CRITICAL + 4 HIGH + 6 MODERATE, включая CVE в fast-jwt |
| 3 | **AuthN/AuthZ** | JWT через `@fastify/jwt@^10`, rate limit 100/min + targeted, `BOT_WORKER_SECRET` | Зависимость `fast-jwt` уязвима (см. §4.2); rotation SECRET_ENCRYPTION_KEY не документирован |
| 4 | **Observability** | Pino logs в journalctl, `/healthz`, `/readyz` (DB + worker + pool + stuck runs + enc key) | Нет `/metrics` (Prometheus), нет Sentry/error-tracking, нет alerting |
| 5 | **Backups & DR** | `deploy/backup.sh` + systemd-таймер на 03:00, retention 7 дней, `/var/backups/botmarketplace/` | Локальный диск только, нет S3/GCS реплики, restore-drill не проводился |
| 6 | **Lifecycle** | systemd-юниты, `startupRecovery.ts`, `stateReconciler.ts` | Нет graceful shutdown для открытых positions, periodic reconciliation отсутствует |
| 7 | **Deploy/rollback** | `deploy/deploy.sh` (7 шагов, `--ref` для pin к тегу/SHA), `deploy/smoke-test.sh` | Нет `deploy/rollback.sh`, шаги не в транзакции (migrate→build→restart раздельно) |
| 8 | **Runbooks** | `docs/runbooks/RUNBOOK.md` (335 строк, 7 диагностических кейсов 6.1–6.7) | Не покрыты: key rotation, "бот завис в RUNNING", exchange outage, DR drill |
| 9 | **Tests** | vitest + `pnpm test:api`, smoke-test hits healthz/readyz/auth/rate-limit/worker auth | Нет e2e "создал бота → пополнил demo → получил fill", нет load-tests |
| 10 | **Secrets** | `.env`, `SECRET_ENCRYPTION_KEY`, `BOT_WORKER_SECRET`, JWT secret | Rotation-процедура не документирована, нет periodic audit |
| 11 | **Doc hygiene** | `docs/` хорошо структурирована, `docs/README.md` актуален, роадмапы v1-v4 + spike | `CHANGELOG.md` заброшен (12 строк, только "Initial documentation set") |

Строки из таблицы раскрыты в §7 с точными путями и номерами строк.

---

## 4. Gap analysis — Top 5 critical findings

Каждый пункт: severity, описание, evidence, impact, effort. Effort — порядок величины, не план реализации.

### 4.1. [CRITICAL] Нет CI pipeline

**Severity:** CRITICAL.

**Описание.** В репозитории отсутствует директория `.github/workflows/`. Это значит, что ни один PR не проверяется автоматически: `pnpm test:api`, `pnpm check:stray`, `tsc --noEmit`, `pnpm build:api`, `pnpm build:web` — всё есть в корневом `package.json`, но запускается только вручную (или, в случае deploy, уже на проде через `deploy/deploy.sh`). Регрессии пропадают в main, если автор забыл прогнать тесты локально. ESLint/Prettier не настроены — согласованность стиля не enforced.

**Evidence:**
- `ls -la .github/` → `no .github`
- `package.json:13-15` — `test:api`, `check:stray` объявлены, но никем не вызываются до merge
- Нет файлов `.eslintrc*`, `.prettierrc*`, `eslint.config.*` ни в root, ни в `apps/api/`, ни в `apps/web/`

**Impact.** Любой PR, добавляющий синтаксически ломающий `tsc --noEmit`, проходит до review. PR #252 чинил Prisma module resolution в тестах — это чинилось руками потому, что тесты не запускаются в CI. Риск регрессий растёт линейно с темпом мержей.

**Effort.** 1 короткая сессия: один workflow `ci.yml` с job'ами install → typecheck → test → check:stray на Node 20 + PNPM 10.29. Secrets не требуются (тесты против SQLite/mocks, не против внешних API).

---

### 4.2. [CRITICAL] Уязвимости в prod-зависимостях (включая JWT)

**Severity:** CRITICAL.

**Описание.** `pnpm audit --prod` показывает **12 vulnerabilities**: 2 CRITICAL + 4 HIGH + 6 MODERATE. Самые опасные — в `fast-jwt`, транзитивной зависимости `@fastify/jwt@^10.0.0` (см. `apps/api/package.json:19`):

- **CRITICAL:** *Incomplete fix for CVE-2023-48223: JWT Algorithm Confusion via Whitespace* — `fast-jwt <= 6.1.0`. Позволяет подобрать токен с неожиданным алгоритмом через whitespace-эксплойт.
- **CRITICAL:** *Cache Confusion via cacheKeyBuilder Collisions* — `fast-jwt < 6.2.0`. Коллизии в кэше могут привести к ошибкам идентификации.
- **HIGH/MODERATE:** `effect`, `defu`, `next` (×2), `fastify` (×2), `fast-jwt` (×2).

Для trading API (где JWT — единственный механизм authN перед операциями с ключами биржи) это blocker, не "потом поправим".

**Evidence:**
- `apps/api/package.json:19` — `@fastify/jwt: ^10.0.0` (pin'ит уязвимую `fast-jwt`)
- `pnpm audit --prod` (верифицировано в задаче аудита)
- Зависимости от `next`, `fastify` — ещё 6 записей в audit

**Impact.** Сценарий эксплуатации JWT-algorithm-confusion, если обнаружится публично — прямой путь к логину под чужим пользователем; оттуда — удаление бота, вывод ключей биржи (расшифровка serverside, но отдаётся maskedApiKey при получении connection'а), отключение safety guards. Даже без active exploitation — compliance-риск.

**Effort.** 15-минутная PR, замыкается на `pnpm up @fastify/jwt fastify next` + прогон тестов. Если `@fastify/jwt@11` ломает API — отдельная задача, но наиболее вероятно minor-bump (patch fastify major). Не чинить в этой аудит-PR: docs-only.

---

### 4.3. [CRITICAL] Нет observability-стека (metrics + alerting)

**Severity:** CRITICAL.

**Описание.** Единственный источник сигнала о проблеме сегодня — либо жалоба пользователя, либо оператор, который вручную читает `journalctl -u botmarket-api -f`. Конкретно отсутствуют:
- `/metrics` endpoint (Prometheus) — ни на API, ни на worker-процессе
- Error tracking (Sentry/Bugsnag/GlitchTip) — unhandled exceptions теряются в логах
- Alerting — нет интеграции с email/Slack/Telegram/PagerDuty
- Dashboards — нет Grafana, нет даже простого `/admin/status` UI

`/readyz` выводит снимок состояния (см. `apps/api/src/routes/readyz.ts`), но его никто не опрашивает регулярно, и он не накапливает историю.

**Evidence:**
- `apps/api/src/routes/` — `healthz.ts`, `readyz.ts` есть, `metrics.ts` нет
- Нет зависимостей вида `prom-client`, `@sentry/node`, `pino-sentry` в `apps/api/package.json`
- `deploy/nginx.conf` не проксирует `/metrics`
- `docs/runbooks/RUNBOOK.md` в §6 описывает диагностику только через `journalctl`

**Impact.** Среднее time-to-detect инцидента = время до жалобы пользователя. Для торгового бота, где окно между "стратегия молча стоит" и "пользователь потерял средства на неисполненном SL" исчисляется минутами, это неприемлемо. Текущее обещание "demo-first" смягчает impact (live-торговли нет), но это не снимает с операторов обязанности знать о сбоях.

**Effort.** 2–3 сессии:
1. `/metrics` + `prom-client` на API/worker (одна сессия).
2. Sentry или self-hosted аналог + sourcemap upload (одна сессия).
3. Alert rules (readyz failure > 2 min, worker stale > 1 min, error rate > 1%) + webhook в Slack/Telegram (одна сессия).

Каждая независима, можно делать по одной за PR.

---

### 4.4. [HIGH] Бэкапы локальные, restore не тестируется

**Severity:** HIGH.

**Описание.** `deploy/backup.sh` делает `pg_dump` в `/var/backups/botmarketplace/` по таймеру `deploy/botmarket-backup.timer` (ежедневно 03:00, retention 7 дней). Это локальный диск той же VPS, где живёт база. Сценарии, в которых все бэкапы теряются вместе с prod-данными:
- Хост-провайдер теряет диск (hardware failure, filesystem corruption).
- `rm -rf` ошибки оператора.
- Ransomware / скомпрометированный root.

Плюс — нет **tested** restore drill. `docs/runbooks/RUNBOOK.md §7` описывает `pg_restore` шаги, но никто не проверял, что они работают end-to-end на актуальном дампе.

**Evidence:**
- `deploy/backup.sh:7` — `BACKUP_DIR="/var/backups/botmarketplace"` (локально)
- `deploy/backup.sh:8` — `KEEP_DAYS=7`
- `deploy/botmarket-backup.timer:15` — `OnCalendar=03:00`
- В скрипте нет `aws s3 cp`, `gsutil cp`, `rsync` в offsite
- `docs/runbooks/RUNBOOK.md:238-272` — секция "Backup и восстановление" описывает команды, но не drill-процедуру

**Impact.** Потеря пользователей, botов, ключей, истории ордеров при single-disk failure. RTO неопределён (зависит от наличия более ранних ручных дампов у оператора). Для demo-периода это терпимо; для платного tier (если откроется) — блокер compliance.

**Effort.** 1–2 сессии:
1. `deploy/backup.sh` расширить: после `pg_dump` — `aws s3 cp` (или `rclone copy`) в удалённый bucket с versioning. Отдельный IAM-ключ, write-only, бюджет <$1/мес для MVP.
2. `docs/runbooks/RUNBOOK.md` дополнить чек-листом DR drill (quarterly): восстановить в staging, прогнать smoke-test, отчёт в CHANGELOG.

---

### 4.5. [HIGH] Нет graceful shutdown + нет periodic reconciliation

**Severity:** HIGH.

**Описание.** При `systemctl restart botmarket-api` (или `systemctl restart botmarket-worker`) процесс получает SIGTERM, и systemd по умолчанию ждёт 90 секунд до SIGKILL. Что происходит с открытыми позициями и in-flight intent'ами в этот момент:
- `BotRun` остаётся в состоянии `RUNNING`, `leaseUntil` не обновляется.
- `PLACED` intent'ы, которые были отправлены на биржу, но ещё не получили fill — зависают.
- `PENDING` intent'ы, ещё не отправленные, теряют контекст сигнала.

После рестарта `startupReconciliation` (`apps/api/src/lib/stateReconciler.ts`) подхватывает — но только **на старте**. Если внутри runtime (не старт) exchange API флапнул на 30 секунд, бот пропустил 2 polling cycle'а — никто не проверит расхождение state'а с биржей до следующего рестарта.

**Evidence:**
- `apps/api/src/lib/botWorker.ts:188` — `leaseUntil: new Date(Date.now() + 30_000)` (30-секундный TTL)
- `apps/api/src/lib/stateReconciler.ts` — весь модуль завязан на "startup only" (комментарий в шапке: "startup intent reconciliation after worker restart")
- Нет cron/setInterval, вызывающего reconciliation периодически
- Нет SIGTERM handler в `apps/api/src/server.ts` / `apps/api/src/worker.ts`, который бы (а) перестал брать новые signals, (б) дождался закрытия in-flight intents, (в) снял lease
- Нет orphan-worker reclaim: если процесс умер без обновления `leaseUntil`, run остаётся с leaseOwner=dead_worker_id до ручного сброса

**Impact.** Окно несогласованности 30–90 сек при каждом deploy. В 99% случаев startup-reconciler починит, но:
- Если deploy идёт в момент fill'а — возможен "двойной ордер" (биржа исполнила, PENDING не отменили).
- Если exchange API флапает между рестартами — стратегия молча пропускает сигналы, пока не случится рестарт.

**Effort.** 1–2 сессии:
1. SIGTERM handler в worker: снять leaseUntil=now, пометить run как "gracefully stopped", bail polling loop (одна сессия).
2. Periodic reconciliation job через `node-cron` (уже в depsах) — раз в 5 минут вызывать тот же reconciler для всех `RUNNING` runs (одна сессия).
3. Orphan reclaim: в startup-reconciler — если `leaseUntil < now - 60s`, сбросить leaseOwner и запустить с чистого листа (полсессии).

---

## 5. Additional findings (MEDIUM severity)

Не-топ-5, но каждый — заметный долг. Порядок — от операционных к документационным.

### 5.1. [MEDIUM] Нет `deploy/rollback.sh`

`deploy/deploy.sh` умеет деплоить конкретный ref через `--ref <tag>` (`deploy/deploy.sh:9`, `deploy/deploy.sh:46-52`), что де-факто даёт ручной rollback: `bash deploy/deploy.sh --ref v0.1.0-rc1`. Но:
- Нет обёртки `deploy/rollback.sh`, которая бы нашла предыдущий тег и задеплоила его.
- Deploy шаги (migrate → build → restart) не идут в транзакции — если `pnpm run db:migrate` прошёл, а build упал, откатить миграцию автоматически нельзя.
- `docs/runbooks/RUNBOOK.md` не содержит явной процедуры rollback.

**Effort:** 30 минут — один shell-скрипт + абзац в RUNBOOK.

### 5.2. [MEDIUM] Нет load-test сценариев

Нет `k6/`, `artillery/`, или аналогов. Неясно, сколько botRun'ов держит один worker до деградации, сколько RPS выдерживает `/api/v1/auth/login` до p99 > 1s. Текущий rate limit 100/min (`withRateLimit` helper) выбран без замеров.

**Effort:** 1 сессия — минимальный k6 script на `/auth/login`, `/bots`, `/runs/:id/state`; запуск в CI (optional, только при push в `main`).

### 5.3. [MEDIUM] Prisma connection pool не сконфигурирован явно

`apps/api/src/lib/prisma.ts` использует дефолты (обычно 10 connections на instance). API и worker — два процесса, это 20 коннектов. Postgres default `max_connections=100`. Запас есть, но нет явного `connection_limit` в `DATABASE_URL` и нет метрик о pool wait time (упоминается `getPoolMetrics()` в `readyz.ts` — полезно, но используется только в health-check).

**Effort:** 20 минут — задокументировать в `.env.example` и `docs/runbooks/RUNBOOK.md §2`.

### 5.4. [MEDIUM] Нет dependabot / renovate

Dep updates — вручную. Учитывая §4.2, это прямой фактор риска: critical CVE в `fast-jwt` проехал в `main` и не был замечен до аудита.

**Effort:** 10 минут — `.github/dependabot.yml` с еженедельным rebase. Потребует сначала §4.1 (CI).

### 5.5. [MEDIUM] CHANGELOG.md заброшен

`CHANGELOG.md` — 12 строк, только "Initial documentation set". Не ведётся с 2025 года. Релиз-теги есть (`git describe` в deploy), но связи "тег → изменения" нет.

**Effort:** 30 минут — импортировать squash-commits main'а за последние 20 релизов в Keep-a-Changelog формат; дальше — policy, что каждый PR обязан добавить строку.

### 5.6. [MEDIUM] Нет DLQ operator UI для failed intents

`recoveryManager.ts` и `errorClassifier.ts` существуют, failed intent'ы помечаются, но оператор не может из UI посмотреть список, причину, retry. Только через `psql` вручную.

**Effort:** 1 сессия — простой admin-page в apps/web с таблицей `Intent WHERE state='FAILED'`.

### 5.7. [MEDIUM] BOT_WORKER_SECRET / SECRET_ENCRYPTION_KEY — нет документированной rotation

`SECRET_ENCRYPTION_KEY` используется в `apps/api/src/lib/crypto.ts` для AES-256-GCM exchange-ключей. Если ключ ротируется, все сохранённые `ExchangeConnection` становятся нерасшифровываемыми — это упомянуто в `docs/runbooks/RUNBOOK.md §6.6` как симптом, но процедуры "как ротировать без потери данных" нет (варианты: dual-key re-encryption, forced reconnect).

**Effort:** 1 сессия — миграционный скрипт + секция в RUNBOOK.

### 5.8. [LOW] CSP mismatch между API и nginx

API выставляет строгий CSP (`default-src 'none'`) на JSON-ответах; nginx (`deploy/nginx.conf`) — более мягкий на static assets. Nginx побеждает для web-страниц, что нормально, но рассогласование создаёт риск "починил в одном месте, забыл в другом".

**Effort:** 15 минут — sync политик, комментарий в обоих файлах.

### 5.9. [LOW] Runbook не покрывает: key rotation, "бот завис", exchange outage, DR drill

`docs/runbooks/RUNBOOK.md` покрывает 7 сценариев (§6.1–6.7): API не отвечает, трассировка запроса, unhandled 500, worker не запускается, rate limit, decrypt failure, smoke-test. Не покрыто:
- Bot застрял в `RUNNING` без прогресса — как безопасно остановить.
- Exchange API вернул 5xx на час — что ожидать, когда вмешиваться.
- DR drill procedure (см. §4.4).
- Rotation секретов (см. §5.7).

**Effort:** 1 сессия после того, как §4.4 и §5.7 реализованы.

### 5.10. [LOW] Demo vs live mode — нет runtime-safe guard

Переключение demo/live — через env-переменную (Bybit testnet URL vs mainnet). Нет runtime-проверки "а точно ли мы в demo": если оператор случайно задеплоит с mainnet URL, safety-guards не сработают — они работают по DSL-параметрам стратегии, а не по типу аккаунта.

**Effort:** 30 минут — проверка `BYBIT_API_URL` на старте worker'а с явным лог-сообщением `[DEMO MODE]` / `[LIVE MODE]`; отказ стартовать, если переменная выглядит подозрительно.

### 5.11. [LOW] Нет orphan worker detection (дубликат 4.5.3)

Упомянут в §4.5 — дублирую для полноты списка.

### 5.12. [LOW] Нет "DSL dry-run" preview перед запуском

У юзера нет возможности запустить стратегию в "симуляцию последних 24h" перед включением. `backtest.ts` существует, но это исторический бэктест; live-preview отсутствует. Не блокер, но снижает доверие к стратегии.

**Effort:** не оценивается в этом аудите — это продуктовая задача, не production-readiness.

---

## 6. Recommended next 3 actions

Порядок важен: каждый следующий шаг выигрывает от предыдущих.

### Action 1 (Immediate, ≤ 1 сессия) — security deps bump

**Что:** `pnpm up @fastify/jwt fastify next` (точные версии — пусть подберёт автор PR по latest stable), прогнать `pnpm test:api`, `pnpm build:api`, `pnpm build:web`. Проверить, что `pnpm audit --prod` показывает 0 CRITICAL.

**Почему первым:** закрывает §4.2 — единственный gap, который есть публично известный CVE-шаблон прямо сейчас. Не требует CI, не требует observability, не требует консенсуса по roadmap'у. Риск PR — минимальный (major-bump `@fastify/jwt` с v10 на v11 — потенциально breaking, см. changelog fastify-jwt; план B — остаться на v10, но форснуть `fast-jwt@^6.2.0` через `pnpm.overrides`).

**Почему не ждать CI (§4.1):** CVE в JWT — это "drop everything and fix" уровень; бюрократия настройки CI добавляет дни без нужды. Сначала закрыть уязвимость, потом строить infrastructure вокруг.

**Deliverable:** 1 PR, ~5 файлов diff (lockfile + package.json + потенциально 1-2 type-fix в auth.ts), CHANGELOG entry.

### Action 2 (Short-term, 1 сессия) — GitHub Actions CI

**Что:** `.github/workflows/ci.yml`:
```yaml
jobs:
  lint-typecheck-test:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup pnpm@10.29, node@20
      - pnpm install --frozen-lockfile
      - pnpm --filter @botmarketplace/api exec tsc --noEmit
      - pnpm --filter @botmarketplace/web exec next build  # если реалистично в CI
      - pnpm test:api
      - pnpm check:stray
```

Плюс `.github/dependabot.yml` (еженедельный security updates, ручной rebase для non-security).

**Почему вторым:** закрывает §4.1 и §5.4 одной сессией. После Action 1 у нас есть clean lockfile, на котором CI будет зелёным с первого раза — это важно, чтобы не дебажить failing baseline.

**Deliverable:** 1 PR, 2 новых файла в `.github/`.

### Action 3 (Medium-term, 2–3 сессии) — observability stack

**Что:** закрывает §4.3 в три шага (каждый — отдельная PR):
1. `/metrics` endpoint с `prom-client` на API и worker. Экспорт: default process metrics + counter'ы intent_created/filled/failed, histogram request_duration.
2. Sentry (или self-hosted GlitchTip) интеграция. `@sentry/node` на API + worker; sourcemap upload через CI (требует Action 2).
3. Alert rules: Prometheus + Alertmanager (если deploy рядом — проще) ИЛИ Uptime Robot-подобный внешний health-checker, который дергает `/readyz` раз в 30 сек и шлёт Slack/Telegram при 2 подряд fail.

**Почему третьим:** у observability есть prerequisites — нужна CI для sourcemap upload (Action 2) и нужна безопасная версия fastify (Action 1), чтобы не катить Sentry SDK поверх уязвимой базы. Также — это тот gap, где effort максимальный (2–3 сессии vs 0.5 для Action 1), поэтому он не может быть первым.

**Deliverable:** 3 PR, суммарно ~10 файлов новых + 4 обновлённых (pool config в `.env.example` попутно, §5.3).

### Actions вне топ-3

Дальше — в свободном порядке по приоритету бизнеса:
- §4.4 (offsite backup) — до того, как появится платный tier.
- §4.5 (graceful shutdown + periodic reconciliation) — до того, как будет больше 10 одновременных runs.
- §5.x — когда доберутся руки.

---

## 7. Appendix — full audit by 11 axes

Детализация таблицы из §3. Для каждой оси: что есть (факты из репозитория), оценка зрелости, пробелы.

### 7.1. CI/CD

**Что есть.**
- Корневые скрипты `package.json:13-15`: `test:api`, `check:stray`.
- `apps/api/package.json:15`: `test`, `test:watch` (vitest).
- `deploy/smoke-test.sh` — E2E smoke после deploy (healthz, readyz, auth, rate limit, worker auth).
- `scripts/clean-stray-ts-artifacts.sh` — страж от закомиченных `.js` рядом с `.ts` (PR #253).

**Зрелость.** 2/5. Инструменты есть, автоматизация нулевая.

**Пробелы.**
- `.github/workflows/` отсутствует.
- ESLint/Prettier не настроены.
- Нет pre-commit hook'а (husky / lefthook).
- Dependabot/renovate не настроен.

### 7.2. Security — dependencies

**Что есть.**
- `pnpm-lock.yaml` фиксирует версии, `deploy/deploy.sh:56` использует `--frozen-lockfile`.
- Scripts с audit-вызовами нет, но `pnpm audit` доступен.

**Зрелость.** 1/5. Уязвимости в main.

**Пробелы.**
- 2 CRITICAL + 4 HIGH + 6 MODERATE в `pnpm audit --prod`.
- `@fastify/jwt@^10` pins уязвимый `fast-jwt`.
- Нет CI-шага, который бы падал на CRITICAL.

### 7.3. AuthN / AuthZ

**Что есть.**
- `apps/api/src/routes/auth.ts` — register/login/me через `@fastify/jwt`.
- bcryptjs для паролей (`apps/api/package.json:25`).
- Rate limit через `@fastify/rate-limit@^10.3.0` + helper `withRateLimit` (global 100/min + targeted override для `/auth/login`, `/auth/register`).
- Worker-auth через `BOT_WORKER_SECRET` (env), проверяется в `PATCH /state`, `POST /heartbeat`, `POST /reconcile`. Warning в `deploy/deploy.sh:74-77`, если секрет = placeholder.

**Зрелость.** 3/5. Базовые механизмы правильные, но транзитивная CVE в JWT-слое сводит оценку вниз.

**Пробелы.**
- См. §4.2.
- Нет 2FA / TOTP.
- Нет refresh-token rotation policy.
- Нет session revocation списка (logout — клиент-сайд).

### 7.4. Observability

**Что есть.**
- Pino logger (`apps/api/src/lib/logger.ts`), log-level через env.
- `X-Request-Id` tracing, задокументирован в `docs/runbooks/RUNBOOK.md §6.2`.
- `/healthz` — uptime + timestamp (`apps/api/src/routes/healthz.ts`).
- `/readyz` — DB check + worker staleness + enc key + stuck runs + pool metrics (`apps/api/src/routes/readyz.ts`).
- journalctl для каждого systemd-юнита.

**Зрелость.** 2/5. Логи и health есть, метрик и алертинга нет.

**Пробелы.** См. §4.3.

### 7.5. Backups & DR

**Что есть.**
- `deploy/backup.sh` — pg_dump с timestamp, 7 дней retention.
- `deploy/botmarket-backup.service` + `.timer` — systemd, 03:00 ежедневно, `Persistent=true` (догонит пропущенный запуск).
- `docs/runbooks/RUNBOOK.md §7` — команды `pg_restore`.

**Зрелость.** 2/5. Резервное копирование есть, DR-стратегии нет.

**Пробелы.** См. §4.4. Плюс: нет бэкапа `.env` (ключи шифрования!) в отдельном secure storage — при потере VPS восстановление зашифрованных exchange connections невозможно.

### 7.6. Lifecycle (graceful shutdown / reconciliation)

**Что есть.**
- `apps/api/src/lib/startupRecovery.ts` + `stateReconciler.ts` — reconciliation на старте worker'а.
- Worker lease: `leaseOwner` + `leaseUntil` (30s TTL), `apps/api/src/lib/botWorker.ts:188`.
- Stuck-runs detection в `/readyz` (часть pool metrics).

**Зрелость.** 2/5. Стартовый reconciliation — хорошо; runtime и shutdown — нет.

**Пробелы.** См. §4.5.

### 7.7. Deploy / rollback

**Что есть.**
- `deploy/deploy.sh` (119 строк, 7 шагов): pull → install → migrate → build → env-check → systemd-sync → restart.
- `--branch` / `--ref` флаги позволяют деплоить конкретный ref.
- `deploy/setup.sh` — первичная установка на чистую VPS.
- Systemd: `deploy/botmarket-{api,web,worker}.service`.
- Post-deploy `systemctl is-active` проверка.

**Зрелость.** 3/5. Deploy документирован и воспроизводим; rollback — ручной.

**Пробелы.** См. §5.1. Плюс: шаг `db:migrate` (строка 60) бежит до `build`, значит при failed build'е мы уже на новой схеме с потенциально несовместимым runtime'ом — нет "pre-flight" dry-run миграции.

### 7.8. Runbooks

**Что есть.**
- `docs/runbooks/RUNBOOK.md` — 335 строк, 10 секций, 7 диагностических кейсов.
- Покрыты: quick-start, env vars, deploy/migrations/services, 7 типовых проблем, backup/restore команды, post-deploy checklist, systemd структура.

**Зрелость.** 3/5. Хороший baseline, но gaps в incident coverage.

**Пробелы.** См. §5.9.

### 7.9. Tests

**Что есть.**
- vitest для apps/api (файлы `*.test.ts`).
- Smoke test (`deploy/smoke-test.sh`) — 15+ проверок в проде.
- `docs/runbooks/RUNBOOK.md §8` — post-deploy checklist.

**Зрелость.** 3/5. Unit/integration покрытие приличное (PR #252 — свежий фикс), E2E есть через smoke-test, но нет load-test и нет "создал бота → получил fill" happy-path.

**Пробелы.**
- См. §5.2 (load).
- Нет E2E теста полного жизненного цикла бота (создание стратегии → подключение exchange → запуск run → получение fill'а → закрытие позиции).
- Coverage metric не публикуется.

### 7.10. Secrets management

**Что есть.**
- `.env` в `/opt/-botmarketplace-site/.env`, не в репо.
- `SECRET_ENCRYPTION_KEY` — 64-hex (32 bytes) для AES-256-GCM exchange-ключей (`apps/api/src/lib/crypto.ts`).
- `BOT_WORKER_SECRET` — shared secret для worker-endpoints.
- JWT secret через `@fastify/jwt` (отдельный env).
- `deploy/deploy.sh:73-78` — warning при placeholder BOT_WORKER_SECRET.
- `/readyz` проверяет наличие и длину `SECRET_ENCRYPTION_KEY`.

**Зрелость.** 3/5. Правильные примитивы, нет lifecycle.

**Пробелы.** См. §5.7. Плюс: `.env` не бэкапится (см. §7.5 pragmatic примечание).

### 7.11. Documentation hygiene

**Что есть.**
- `docs/` — 30+ файлов, structured README.
- Роадмапы v1 (`16-roadmap.md`), v2 (`30-roadmap-v2.md`), v3 (`31-stability-roadmap-v3.md`), v4 (`34-roadmap-v4-test-coverage-and-hardening.md`).
- Spike-notes (`36-dsl-graph-bidirectional-spike.md`).
- Prompts архив (`docs/prompts/`, `docs/deploy-*-prompt.md`).

**Зрелость.** 4/5. Лучшая ось в аудите.

**Пробелы.**
- `CHANGELOG.md` = 12 строк (§5.5).
- Нет "architecture decision records" (ADR) — решения размазаны по роадмапам.

---

## 8. Cross-references

**Связанные документы в репозитории:**

- `docs/03-requirements-nonfunctional.md` — исходные NFR, часть из них закрыта частично (latency, availability).
- `docs/05-security.md` — threat-model на уровне приложения; этот аудит дополняет его операционным слоем.
- `docs/14-deployment.md` — спецификация deploy; аудит фиксирует, что deploy.sh ей соответствует, но rollback.sh отсутствует.
- `docs/15-operations.md` — операционные требования; §4.3/§4.4/§4.5 — прямое продолжение.
- `docs/runbooks/RUNBOOK.md` — current-state runbook; §5.9 фиксирует gaps.
- `docs/31-stability-roadmap-v3.md` — roadmap v3 закрыт, но не покрывал observability/alerting.
- `docs/34-roadmap-v4-test-coverage-and-hardening.md` — roadmap v4, пересекается с §7.9.
- `docs/36-dsl-graph-bidirectional-spike.md` — шаблон docs-only spike, использованный здесь.
- `CHANGELOG.md` — заброшен, см. §5.5.

**Релевантные PR-ы:**
- PR #251 (ea24b45) — fix orphan node/next processes at systemctl restart. Частично снимает §4.5, но не полностью (это про процессы, не про positions).
- PR #252 (53452c5) — fix positionManager.test.ts module resolution. Индикатор того, что без CI (§4.1) тесты ломаются в main незамеченными.
- PR #253 (d2b6e66) — check:stray tooling. Готовый кандидат для включения в CI workflow (§4.1 Action 2).
- PR #254 (0db6677) — Phase 2B2 + spike docs/36. Прецедент docs-only merge, которому следует этот аудит.

**Внешние ссылки (не прямая навигация — просто для проверки):**
- fast-jwt advisories: github advisories для пакета (не раскрываю ссылкой — проверьте `pnpm audit --prod` локально).
- CVE-2023-48223: "JWT Algorithm Confusion via Whitespace" — базовая уязвимость, фикс которой в fast-jwt оказался incomplete.
- Keep a Changelog: https://keepachangelog.com (эталон для §5.5).

---

## Conclusion

Проект технически добротный: архитектура ясная, код читаемый, runbook выше среднего для MVP. Но "production-ready" в строгом смысле требует закрыть минимум §4.2 (CVE в JWT) прежде, чем открывать публичный доступ, и §4.1+§4.3 — прежде, чем позиционировать сервис как надёжный.

Рекомендуемая последовательность из §6 минимизирует риск и накапливает инфраструктуру инкрементально: safety-fix → CI → observability. Каждый шаг — отдельная PR, без crossed dependencies внутри шага.

Этот документ — снимок состояния на `0db6677`. После любого из предложенных actions имеет смысл обновить соответствующую ось в §7 (inline-edit) или написать `docs/38-...` с follow-up замерами.
