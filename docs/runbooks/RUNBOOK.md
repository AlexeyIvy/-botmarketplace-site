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

# Решение: пересоздать exchange connections с текущим ключом
# (Через UI: удалить и создать заново)
```

### 6.7 Smoke tests падают на worker-related проверках

```bash
# BOT_WORKER_SECRET должен совпадать между .env и переменной окружения smoke-теста
BOT_WORKER_SECRET=$(grep BOT_WORKER_SECRET /opt/-botmarketplace-site/.env | cut -d= -f2 | tr -d '"')
BOT_WORKER_SECRET="$BOT_WORKER_SECRET" bash deploy/smoke-test.sh

# Или запустить без проверки worker secret (dev mode):
# Убрать BOT_WORKER_SECRET из окружения — тест переключится в dev-режим
```

---

## 7. Backup и восстановление

### Создать backup вручную

```bash
bash deploy/backup.sh
# Дамп сохраняется в /opt/-botmarketplace-site/backups/
```

### Автоматический backup

```bash
# Таймер настроен через systemd:
systemctl status botmarket-backup.timer
systemctl list-timers botmarket-backup.timer
```

### Восстановление из backup

```bash
# 1. Остановить сервисы
systemctl stop botmarket-api botmarket-web

# 2. Восстановить БД
psql "$DATABASE_URL" < /opt/-botmarketplace-site/backups/botmarket-YYYYMMDD.sql

# 3. Запустить сервисы
systemctl start botmarket-api botmarket-web

# 4. Проверить
bash deploy/smoke-test.sh
```

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

## 11. Полезные команды

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
