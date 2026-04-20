# Runbook — BotMarketplace Operations

**Аудитория:** оператор, разработчик, self-hosted инсталляция
**Версия:** v0.1.0-rc1 (Stage 14)

---

## 1. Быстрый старт (TL;DR)

```bash
# Клонировать + настроить
git clone https://github.com/AlexeyIvy/-botmarketplace-site.git /opt/-botmarketplace-site
cd /opt/-botmarketplace-site
cp .env.example .env   # заполнить обязательные переменные

# Деплой
bash deploy/setup.sh    # первичная установка (systemd, nginx, etc.)
bash deploy/deploy.sh   # билд + миграции + рестарт

# Валидация
bash deploy/smoke-test.sh
```

---

## 2. Переменные окружения (`.env`)

| Переменная | Обязательна | Формат | Как сгенерировать |
|-----------|:-----------:|--------|-------------------|
| `DATABASE_URL` | Да | `postgresql://user:pass@localhost:5432/botmarket` | Настроить PostgreSQL |
| `JWT_SECRET` | Да | 32+ случайных байт (hex/string) | `openssl rand -hex 32` |
| `SECRET_ENCRYPTION_KEY` | Да | 32-байтный HEX (64 символа) | `openssl rand -hex 32` |
| `BOT_WORKER_SECRET` | Production | Произвольная строка 32+ символов | `openssl rand -hex 32` |
| `NODE_ENV` | Нет | `production` | Установить `production` на VPS |
| `PORT` | Нет | Число (default: 3001) | — |
| `POOL_WAIT_THRESHOLD` | Нет | Число (default: 5) | Порог `waiting` в `/readyz` connection pool check |
| `BYBIT_ALLOW_LIVE` | Live-прод | `true` | Обязателен при `NODE_ENV=production` + `BYBIT_ENV=live` (§5.10 guard) |

### Критические замечания

- **`SECRET_ENCRYPTION_KEY`** — если изменить после создания exchange connections, все существующие зашифрованные секреты станут нечитаемы. Храни в безопасном месте, делай backup.
- **`BOT_WORKER_SECRET`** — без него в production worker endpoints (`PATCH /state`, `POST /heartbeat`, `POST /reconcile`) доступны без аутентификации. **Обязательно установить перед production-деплоем.**
- **`JWT_SECRET`** — изменение инвалидирует все выданные токены (все пользователи разлогинятся).

### Prisma connection pool (`DATABASE_URL`)

В production задавай пул явно через query-параметры:

```
postgresql://user:pass@host:5432/botmarket?schema=public&connection_limit=10&pool_timeout=10
```

- `connection_limit` — сколько коннектов откроет каждый процесс (API и worker — независимо).
  Итоговое потребление: `connection_limit × N_процессов`. Postgres по умолчанию держит
  `max_connections=100`; оставляй ≥10% admin-slots запаса.
- `pool_timeout` (сек) — сколько Prisma ждёт свободный коннект перед ошибкой. Слишком
  маленькое → «pool wait count > threshold» в `/readyz` → `degraded`. Слишком большое →
  HTTP request'ы ждут и упираются в таймауты клиента.

Живые метрики пула: `botmarket_*` на `/metrics` + `/readyz.checks.connectionPool` +
пинованые метрики в логах (`module=prisma` каждые 60 сек). Если `waiting > 0` стабильно —
либо поднимать `connection_limit`, либо поднимать Postgres `max_connections`.

---

## 3. Деплой

### 3.1 Стандартный деплой (последний main)

```bash
cd /opt/-botmarketplace-site
bash deploy/deploy.sh
```

### 3.2 Деплой конкретного тега / коммита (рекомендуется для RC)

```bash
cd /opt/-botmarketplace-site
git fetch --tags
git checkout v0.1.0-rc1   # или конкретный SHA: git checkout abc1234

# Установить зависимости + мигрировать + собрать + рестартовать
pnpm install --frozen-lockfile
pnpm run db:migrate
pnpm run build:api
pnpm run build:web
systemctl restart botmarket-api botmarket-web

# Проверить
bash deploy/smoke-test.sh
```

### 3.3 Деплой с явным branch

```bash
bash deploy/deploy.sh --branch feature/my-branch
```

### 3.4 Тегирование RC

```bash
# Локально (разработчик):
git tag -a v0.1.0-rc1 -m "Release Candidate 1 — Stage 14 complete"
git push origin v0.1.0-rc1

# На VPS:
git fetch --tags
git checkout v0.1.0-rc1
```

### 3.5 Rollback на предыдущий релиз

```bash
# Посмотреть план без выполнения (покажет текущий / целевой teg + коммиты)
bash deploy/rollback.sh --dry-run

# Откатиться на автоматически-определённый предыдущий тег
bash deploy/rollback.sh

# Откатиться на конкретный тег
bash deploy/rollback.sh --to v0.1.0-rc1

# Non-interactive (для автоматики)
bash deploy/rollback.sh --to v0.1.0-rc1 --yes
```

Под капотом: `rollback.sh` находит предыдущий тег (`git tag --sort=-version:refname | sed -n '2p'`), показывает список коммитов, которые будут откачены, и делегирует `deploy/deploy.sh --ref <tag>`.

**Важно про DB миграции.** Prisma миграции forward-only — если целевой тег предшествует breaking schema change (drop column, type change), rollback оставит БД в текущем (новом) состоянии, а код из старого тега может упасть. Процедура в этом случае:
1. Восстановить dump из backup: `bash deploy/backup.sh --restore <dump>` (см. §7).
2. Только потом запускать rollback.

Скрипт показывает предупреждение перед выполнением. Если меняли схему в диапазоне — **проверяй backup сначала**.

---

## 4. Миграции базы данных

Миграции запускаются автоматически при `bash deploy/deploy.sh`.

**Вручную:**
```bash
cd /opt/-botmarketplace-site
pnpm run db:migrate
# или напрямую:
pnpm --filter @botmarketplace/api exec prisma migrate deploy
```

**Посмотреть статус миграций:**
```bash
pnpm --filter @botmarketplace/api exec prisma migrate status
```

**Откат невозможен** через Prisma Migrate (нет rollback по умолчанию). При проблемах:
1. Восстановить БД из backup (`bash deploy/backup.sh` создаёт dump)
2. Или написать ручную миграцию

---

## 5. Управление сервисами

```bash
# Статус
systemctl status botmarket-api
systemctl status botmarket-web

# Рестарт
systemctl restart botmarket-api
systemctl restart botmarket-web

# Логи в реальном времени
journalctl -u botmarket-api -f
journalctl -u botmarket-web -f

# Логи за последний час
journalctl -u botmarket-api --since "1 hour ago"
```

---

## 6. Диагностика типовых проблем

### 6.1 API не отвечает (5xx / timeout)

```bash
# 1. Проверить статус сервиса
systemctl status botmarket-api

# 2. Посмотреть последние логи
journalctl -u botmarket-api -n 100 --no-pager

# 3. Проверить healthz
curl -s http://localhost:3001/api/v1/healthz

# 4. Если сервис упал — рестартовать
systemctl restart botmarket-api

# 5. Проверить БД
psql "$DATABASE_URL" -c "SELECT 1"
```

### 6.2 Трассировка конкретного запроса

```bash
# Получить X-Request-Id из ответа
REQ_ID=$(curl -sI https://botmarketplace.store/api/v1/healthz | grep -i x-request-id | awk '{print $2}' | tr -d '\r')

# Найти все записи в логах
journalctl -u botmarket-api --since "1 hour ago" | grep "$REQ_ID"

# Клиент может задать свой ID для удобного поиска:
curl -H "X-Request-Id: debug-session-1" https://botmarketplace.store/api/v1/healthz
journalctl -u botmarket-api | grep "debug-session-1"
```

### 6.3 Unhandled 500 error

```bash
# Найти ошибки (level=50 в pino = error)
journalctl -u botmarket-api --since "1 hour ago" | grep '"level":50'

# Или по тексту
journalctl -u botmarket-api --since "1 hour ago" | grep "Unhandled error"

# В dev-режиме detail в ответе содержит error.message
# В production detail = "An unexpected error occurred"
```

### 6.4 Bot worker не запускается

```bash
# Проверить наличие строки о старте worker
journalctl -u botmarket-api --no-pager | grep "botWorker.*started"

# Если не найдено — смотреть логи старта API
journalctl -u botmarket-api --since "10 minutes ago" | head -50

# Типичные причины:
# - DATABASE_URL не настроен
# - Prisma client не сгенерирован (pnpm --filter @botmarketplace/api exec prisma generate)
```

### 6.5 Rate limiting 429 вместо нужного ответа

```bash
# Rate limit сбрасывается через 15 минут (окно для /auth/register)
# Подождать 15 минут или перезапустить API (окна в памяти)
systemctl restart botmarket-api

# Проверить текущее состояние:
curl -v https://botmarketplace.store/api/v1/auth/login \
  -X POST -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
# Если 429 — смотреть заголовки Retry-After
```

### 6.6 Exchange Connection не может расшифровать секрет

```bash
# Симптом: ошибка при test connection или при попытке разместить ордер
# Причина: SECRET_ENCRYPTION_KEY изменился после сохранения соединения

# Проверить текущий ключ в .env
grep SECRET_ENCRYPTION_KEY /opt/-botmarketplace-site/.env

# Правильный путь ротации ключа — см. §11.1 (dual-key rotation).
# Если ключ уже перепутан и backup свежее — restore + ротация.
```

### 6.7 Smoke tests падают на worker-related проверках

```bash
# BOT_WORKER_SECRET должен совпадать между .env и переменной окружения smoke-теста
BOT_WORKER_SECRET=$(grep BOT_WORKER_SECRET /opt/-botmarketplace-site/.env | cut -d= -f2 | tr -d '"')
BOT_WORKER_SECRET="$BOT_WORKER_SECRET" bash deploy/smoke-test.sh

# Или запустить без проверки worker secret (dev mode):
# Убрать BOT_WORKER_SECRET из окружения — тест переключится в dev-режим
```

### 6.8 Бот "завис" в RUNNING без прогресса

**Симптом.** `BotRun.state=RUNNING`, последний `BotEvent` старше 10–15 минут, но стратегия должна была генерировать сигналы. Потенциальные причины (по частоте): stuck PENDING intents, worker wedged (не вызывает poll), lease сожжён мёртвым воркером, DSL `enabled: false` выставлен случайно, все сигналы отфильтрованы safety guards.

**Диагностика:**

```bash
# 1. Проверить метрики
curl -s http://127.0.0.1:4000/metrics | grep -E 'botmarket_intent|stale_pending|orphan_leases'

# 2. Найти run
RUN_ID=<uuid>

# 3. События последних 30 мин
psql "$DATABASE_URL" -c "
  SELECT \"type\", \"payloadJson\", ts
  FROM \"BotEvent\"
  WHERE \"botRunId\" = '$RUN_ID'
  ORDER BY ts DESC LIMIT 20;
"

# 4. PENDING intents (если периодический reconciler ещё не успел сработать)
psql "$DATABASE_URL" -c "
  SELECT id, type, side, state, \"createdAt\"
  FROM \"BotIntent\"
  WHERE \"botRunId\" = '$RUN_ID' AND state = 'PENDING'
  ORDER BY \"createdAt\" DESC LIMIT 10;
"

# 5. Lease — старше 60 сек = orphan (см. §4.5.3)
psql "$DATABASE_URL" -c "
  SELECT id, state, \"leaseOwner\", \"leaseUntil\",
         EXTRACT(EPOCH FROM (NOW() - \"leaseUntil\")) AS lease_age_s
  FROM \"BotRun\" WHERE id = '$RUN_ID';
"

# 6. Worker poll жив? (последний poll должен быть < 8 сек назад)
journalctl -u botmarket-api --since "5 minutes ago" | grep "botWorker" | tail -5
journalctl -u botmarket-worker --since "5 minutes ago" | tail -5
```

**Действия:**

1. Если `stale_pending_cancelled_total` растёт — периодический reconciler уже работает, подожди 5 мин до следующего sweep, либо запусти вручную рестартом API.
2. Если `leaseUntil` старый и `leaseOwner` не текущий PID воркера — orphan; periodicReconciler переклеит на следующем тике (≤5 мин).
3. Если poll loop не виден в логах > 1 мин — воркер wedged. Рестарт: `systemctl restart botmarket-worker` (или `botmarket-api` для embedded). `stopWorker()` сам освободит lease (§4.5.1), новый воркер подхватит.
4. Безопасно остановить конкретный run (через UI или API):
   ```bash
   curl -X POST "http://localhost:4000/api/v1/runs/$RUN_ID/stop" \
     -H "Authorization: Bearer $TOKEN" \
     -H "X-Workspace-Id: $WS_ID"
   ```

**DLQ UI (§5.6).** Для ручного разбора FAILED intents — страница `/operator/dlq`
в web-UI (ссылка также доступна из Settings → Operator tools). Показывает
список с фильтром по state, деталями `metaJson` (включая `error`, `errorClass`,
`deadLetterReason`), pagination; кнопка **Retry** переводит FAILED → PENDING,
воркер подхватит на следующем тике. Эквиваленты через API:

```bash
# Список FAILED в воркспейсе
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" \
  "http://localhost:4000/api/v1/intents?state=FAILED&limit=50"

# Manual retry
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" \
  "http://localhost:4000/api/v1/intents/$INTENT_ID/retry"
```

### 6.9 Exchange API вернул 5xx / недоступен

**Симптом.** Счётчик `botmarket_intent_failed_total` резко растёт; в логах — `errorClass=transient` или `classification.retryable=true`; `/readyz` остаётся `ok` (проблема снаружи, не у нас).

**Что ожидать:**

- **Demo**: ничего — все intents симулируются без обращения к бирже.
- **Live**: intent executor делает до `MAX_INTENT_RETRIES` (default 3) повторов с backoff. После — intent переходит в `FAILED` с `errorClass=transient`, `deadLetterReason` в `metaJson`.
- Safety guard `pauseOnError` (§4.1 DSL, по умолчанию threshold 3 подряд FAILED) автоматически переведёт run в `STOPPING`, чтобы не спамить биржу.

**Когда вмешиваться:**

- Exchange down > 10 минут и счётчик `botmarket_intent_failed_total` растёт на десятки — мониторить, ничего не делать: safety guards сработают.
- Exchange down > 1 часа — остановить live runs через UI, ждать восстановления, затем перезапустить вручную.
- Exchange сам вернул "Invalid API key" на ранее рабочих ключах — это не outage, это revoke/истекший ключ. Пользователь обновляет в UI.

**Диагностика:**

```bash
# Сколько FAILED за последний час
psql "$DATABASE_URL" -c "
  SELECT DATE_TRUNC('minute', \"updatedAt\") AS t,
         COUNT(*) FILTER (WHERE state='FAILED') AS failed,
         COUNT(*) FILTER (WHERE state='PLACED') AS placed
  FROM \"BotIntent\"
  WHERE \"updatedAt\" > NOW() - INTERVAL '1 hour'
  GROUP BY 1 ORDER BY 1 DESC;
"

# Классификация ошибок (смотри metaJson.errorClass)
psql "$DATABASE_URL" -c "
  SELECT \"metaJson\"->>'errorClass' AS class, COUNT(*)
  FROM \"BotIntent\"
  WHERE state='FAILED' AND \"updatedAt\" > NOW() - INTERVAL '1 hour'
  GROUP BY 1;
"

# Статус биржи напрямую (bybit)
curl -s https://api.bybit.com/v5/market/time | jq .
```

Долгоиграющие live runs можно временно перевести в `demo` (через UI: Exchange Connection выбрать demo) — сигналы продолжат генерироваться, но без реальных ордеров.

### 6.10 DR drill (disaster recovery дрилл)

**Зачем.** §4.4 аудита: restore-процедура из backup должна быть проверена end-to-end, не только документирована. Раз в квартал.

**Процедура (в staging, не в prod!):**

1. **Поднять staging Postgres** отдельный от prod (docker compose или отдельный VPS):
   ```bash
   docker run -d --name botmarket-dr -p 5433:5432 \
     -e POSTGRES_USER=botmarket -e POSTGRES_PASSWORD=drill \
     -e POSTGRES_DB=botmarket postgres:15
   ```
2. **Взять свежий prod-dump** (не дольше 24ч):
   ```bash
   LATEST=$(ls -t /var/backups/botmarketplace/*.sql.gz | head -1)
   echo "restoring: $LATEST"
   ```
3. **Restore:**
   ```bash
   gunzip -c "$LATEST" | PGPASSWORD=drill psql -h localhost -p 5433 -U botmarket -d botmarket
   ```
4. **Быстрая валидация** схемы и данных:
   ```bash
   PGPASSWORD=drill psql -h localhost -p 5433 -U botmarket -d botmarket -c "
     SELECT COUNT(*) AS users FROM \"User\";
     SELECT COUNT(*) AS bots FROM \"Bot\";
     SELECT COUNT(*) AS runs FROM \"BotRun\";
     SELECT MAX(\"createdAt\") AS latest_bot FROM \"Bot\";
   "
   ```
   Счётчики должны быть близкими к prod; `latest_bot` — не старше prod последних креатов.
5. **Опционально:** поднять API/worker против этой БД и прогнать `deploy/smoke-test.sh`:
   ```bash
   DATABASE_URL="postgresql://botmarket:drill@localhost:5433/botmarket" \
     BASE_URL="http://localhost:4000" bash deploy/smoke-test.sh
   ```
6. **Teardown:**
   ```bash
   docker rm -f botmarket-dr
   ```
7. **Записать результат** в `CHANGELOG.md` (`[Unreleased] ### Docs — DR drill executed YYYY-MM-DD, result: ok / issues`).

**Красные флаги.** Если (1) backup файл повреждён, (2) restore падает с ошибками, (3) счётчики после restore отличаются от prod на > 10% — это блокер, разбираться до следующего prod-деплоя. Если backup старше 48ч — перенастроить cron (должен быть ежедневно, см. `botmarket-backup.timer`).

---

## 7. Backup и восстановление

### 7.1 Создать backup вручную

```bash
bash deploy/backup.sh
# Локально → /var/backups/botmarketplace/botmarket_YYYYMMDD_HHMMSS.sql.gz
# + offsite upload (S3 и/или rclone), если сконфигурировано — см. §7.4
```

### 7.2 Автоматический backup

Таймер настроен через systemd (ежедневно 03:00, retention 7 дней локально):

```bash
systemctl status botmarket-backup.timer
systemctl list-timers botmarket-backup.timer
journalctl -u botmarket-backup -n 50
```

### 7.3 Восстановление из backup

```bash
# Интерактивный вариант (скрипт сам остановит, спросит подтверждение):
bash deploy/backup.sh --restore /var/backups/botmarketplace/botmarket_YYYYMMDD_HHMMSS.sql.gz
systemctl restart botmarket-api botmarket-web
bash deploy/smoke-test.sh

# Если нужен dump из offsite (S3 / rclone):
bash deploy/backup.sh --pull botmarket_YYYYMMDD_HHMMSS.sql.gz
# → скачает в $BACKUP_DIR, дальше --restore как выше

# Посмотреть что есть в локальном и offsite сторах:
bash deploy/backup.sh --list
```

### 7.4 Offsite upload (§4.4 — disaster recovery)

Локальные backup'ы лежат на той же VPS, что и БД — single point of failure.
`backup.sh` поддерживает опциональный upload в объектное хранилище сразу после
локального дампа. Без этих переменных поведение прежнее (только локально),
поэтому существующие деплои работают без изменений.

**Вариант A — AWS S3 / S3-совместимое (DO Spaces, Wasabi, Backblaze B2 S3 API):**

```bash
# .env на VPS:
BACKUP_S3_BUCKET="my-botmarket-backups"
BACKUP_S3_PREFIX="prod"           # опционально, default: "botmarket"

# Credentials — стандартные AWS_* переменные или ~/.aws/credentials:
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_DEFAULT_REGION="us-east-1"    # или region твоего bucket'а
# AWS_ENDPOINT_URL_S3="..."       # для не-AWS S3 API (Backblaze B2 etc.)
```

Требует `apt install awscli` (или pip). При первом запуске убедись, что у
IAM-ключа есть права `s3:PutObject` + `s3:GetObject` + `s3:ListBucket`.

**Вариант B — rclone (наиболее гибкий; B2, GCS, Azure, SFTP, WebDAV, …):**

```bash
# Настроить remote интерактивно:
rclone config
# → пример результата: `[b2-prod]` с credentials

# .env:
BACKUP_RCLONE_REMOTE="b2-prod:botmarket-backups"
```

**Retention.** Локальные файлы удаляются через `KEEP_DAYS` (default 7).
Offsite retention управляй lifecycle-политикой на стороне bucket'а
(S3 Lifecycle / B2 Lifecycle Rules) — рекомендовано 30 дней hot + 90 дней
cold (Glacier / B2 Archive).

**Бюджет.** DB-дамп ~50–500 MB gzipped при малой базе; 30-дневный retention
= <$1/мес на любом провайдере (S3 Standard IA, B2 — ~$0.01/GB/мес).

**DR drill.** Минимум раз в квартал — полный прогон restore из offsite. См.
§6.10.

---

## 8. Проверка после деплоя (чеклист)

```bash
# 1. Сервисы запущены
systemctl is-active botmarket-api && systemctl is-active botmarket-web

# 2. API liveness
curl -s https://botmarketplace.store/api/v1/healthz | jq .

# 3. Correlation ID в ответе
curl -sI https://botmarketplace.store/api/v1/healthz | grep -i x-request-id

# 4. Web UI доступен
curl -s -o /dev/null -w "%{http_code}" https://botmarketplace.store/login

# 5. Полный smoke suite
bash deploy/smoke-test.sh
```

---

## 9. Структура сервисов (systemd)

| Сервис | Описание | Порт |
|--------|---------|------|
| `botmarket-api` | Fastify API + в-процессе bot worker | 3001 |
| `botmarket-web` | Next.js UI | 3000 |
| `botmarket-backup.timer` | Автоматический backup по расписанию | — |
| `botmarket-healthcheck.timer` | Проверка `/readyz` каждые 30 сек + alert | — |

Nginx слушает 80/443 и проксирует на 3001 (API: `/api/`) и 3000 (Web).

---

## 10. Мониторинг и алерты

### 10.1 Prometheus scrape

API экспортирует метрики на `/metrics` (без auth, стандарт Prometheus). nginx
разрешает доступ только с loopback — снаружи endpoint недоступен. Метрики:

- `botmarket_intent_created_total` / `_filled_total` / `_failed_total` — counters
- `botmarket_http_request_duration_seconds` — histogram (method/route/status)
- `process_*`, `nodejs_*` — defaults от `prom-client`

Пример scrape-конфига (`prometheus.yml`):

```yaml
scrape_configs:
  - job_name: botmarket-api
    static_configs:
      - targets: ["127.0.0.1:4000"]
```

### 10.2 Sentry (ошибки)

Опциональная интеграция. Включается установкой `SENTRY_DSN` в `.env`. Если DSN
не задан — init пропускается (no-op). Все 5xx из Fastify error handler'а
отправляются как `captureException` с тегом `reqId` и контекстом `request`.

Дополнительно:

- `SENTRY_RELEASE` — тег release (рекомендуется: git sha из `deploy.sh`)
- `SENTRY_TRACES_SAMPLE_RATE` — доля traces (по умолчанию 0 — без traces)

### 10.3 Алерты по `/readyz`

Скрипт `deploy/healthcheck.sh` + systemd timer дёргают `/readyz` каждые 30 сек.
При **2 подряд** non-200 ответах шлётся webhook (Telegram / Slack).
Состояние счётчика хранится в `/var/lib/botmarket/healthcheck.state`.

**Установка:**

```bash
cp deploy/botmarket-healthcheck.{service,timer} /etc/systemd/system/
systemctl daemon-reload

# Прописать credentials в drop-in:
systemctl edit botmarket-healthcheck.service
# В редакторе:
#   [Service]
#   Environment="ALERT_WEBHOOK_URL=https://api.telegram.org/bot<TOKEN>/sendMessage"
#   Environment="ALERT_CHAT_ID=-1001234567890"
#   # Для Slack:
#   # Environment="ALERT_WEBHOOK_KIND=slack"
#   # Environment="ALERT_WEBHOOK_URL=https://hooks.slack.com/services/..."

systemctl enable --now botmarket-healthcheck.timer
```

**Проверка:**

```bash
systemctl list-timers | grep healthcheck     # ближайшее срабатывание
journalctl -u botmarket-healthcheck -n 50    # последние запуски
```

**Кастомизация:** переменные в drop-in — `READYZ_URL`, `FAIL_THRESHOLD`,
`STATE_FILE` (см. комментарии в `deploy/healthcheck.sh`).

---

## 11. Ротация секретов

### 11.1 `SECRET_ENCRYPTION_KEY` (dual-key rotation)

`SECRET_ENCRYPTION_KEY` шифрует `ExchangeConnection.encryptedSecret` и
Telegram bot token в `WorkspaceNotification.notifyJson`. Без процедуры
ниже ротация сломает все сохранённые секреты — пользователи не смогут
использовать bots без переподключения биржи.

**Процедура (zero-downtime):**

1. **Backup БД** перед началом (см. §7). Обязательно.
2. Сгенерировать новый ключ:
   ```bash
   NEW_KEY=$(openssl rand -hex 32)
   echo "$NEW_KEY"
   ```
3. Обновить `.env` — сохранить текущий ключ как `OLD`, поставить новый:
   ```
   SECRET_ENCRYPTION_KEY=<NEW_KEY>
   SECRET_ENCRYPTION_KEY_OLD=<prev key, тот что был в SECRET_ENCRYPTION_KEY>
   ```
4. Рестартовать сервисы:
   ```bash
   systemctl restart botmarket-api botmarket-worker
   ```
   API сейчас шифрует новые записи новым ключом, расшифровывает старые —
   старым (fallback через `decryptWithFallback`). Smoke-тест через UI:
   открыть список ботов, проверить что "Exchange" отображается (значит
   старые ключи читаются).
5. Прогнать миграцию — перешифровать всё новым ключом:
   ```bash
   # Dry-run (без изменений БД):
   pnpm --filter @botmarketplace/api exec tsx scripts/rotateEncryptionKey.ts --dry-run

   # Реальная миграция:
   pnpm --filter @botmarketplace/api exec tsx scripts/rotateEncryptionKey.ts
   ```
   Скрипт выведет счётчики `rotated=N failed=M`. Если `failed > 0` —
   **НЕ** удалять `SECRET_ENCRYPTION_KEY_OLD`, разбираться в логах
   прежде чем двигаться дальше.
6. Убрать старый ключ из `.env`:
   ```
   # удалить строку SECRET_ENCRYPTION_KEY_OLD=…
   ```
7. Рестарт ещё раз — убедиться, что всё читается только новым ключом:
   ```bash
   systemctl restart botmarket-api botmarket-worker
   systemctl is-active botmarket-api botmarket-worker
   ```
8. Записать событие в CHANGELOG.md (`[Unreleased] ### Security —
   encryption key rotated on <date>`).

**Если что-то пошло не так.** До шага 6 ротация полностью обратима —
просто вернуть `SECRET_ENCRYPTION_KEY` на старое значение и убрать
`_OLD`. После шага 6 (удаления OLD) откат требует restore из backup БД.

### 11.2 `JWT_SECRET` (инвалидация токенов)

Изменение `JWT_SECRET` делает все выданные access/refresh токены
невалидными (все пользователи разлогинятся). Процедура:

1. Сгенерировать новый секрет: `openssl rand -hex 32`.
2. Обновить `.env` и рестартовать API.
3. Уведомить пользователей (необязательно — они увидят форму логина при
   первом же запросе).

### 11.3 `BOT_WORKER_SECRET` (worker ↔ API канал)

Используется worker-to-API endpoints (`PATCH /state`, `POST /heartbeat`,
`POST /reconcile`). Если worker и API — в одном процессе (embedded),
просто обновить `.env` и рестартовать. Если worker standalone — сначала
обновить API (`.env` + restart), затем worker.

---

## 12. Полезные команды

```bash
# Версия приложения (из package.json)
cat /opt/-botmarketplace-site/package.json | grep '"version"'

# Текущий git ref
git -C /opt/-botmarketplace-site describe --tags --always

# Список тегов
git -C /opt/-botmarketplace-site tag --sort=-version:refname | head -5

# Проверить Prisma миграции
cd /opt/-botmarketplace-site && pnpm --filter @botmarketplace/api exec prisma migrate status

# Логи bot worker (только)
journalctl -u botmarket-api -f | grep botWorker

# Только ошибки (pino level 50)
journalctl -u botmarket-api --since "1 hour ago" | grep '"level":50'

# EMERGENCY: остановить все активные runs
curl -s -X POST https://botmarketplace.store/api/v1/runs/stop-all \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -H "X-Workspace-Id: $YOUR_WS_ID"
```

---

*Runbook обновлён: Stage 14 — Release Candidate Pack*
