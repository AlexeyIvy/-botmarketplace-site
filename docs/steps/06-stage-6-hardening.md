# Stage 6 — Hardening & Release Readiness

## Цель

Подготовить проект к MVP-релизу:
- rate limiting на чувствительных эндпоинтах
- max duration enforcement (TIMED_OUT) для зависших ботов
- Stop All для экстренной остановки всех активных ботов
- ежедневный бэкап PostgreSQL через systemd timer
- smoke-test checklist для проверки деплоя

## Acceptance Criteria

- [ ] Rate limiting: POST /auth/register, POST /bots/:id/runs, POST /lab/backtest
- [ ] Bot Run автоматически переводится в TIMED_OUT если работает дольше MAX_RUN_DURATION_MS
- [ ] POST /api/v1/runs/stop-all останавливает все активные боты в workspace
- [ ] Ежедневный бэкап БД настроен через systemd timer
- [ ] smoke-test.sh успешно проходит все проверки на продакшне

## Архитектура

### Rate Limiting (`@fastify/rate-limit`)
- Глобальный лимит: 200 req/min per IP
- POST /auth/register: 5 req / 15 min per IP
- POST /bots/:id/runs: 10 req / min per IP
- POST /lab/backtest: 5 req / min per IP

### Max Run Duration
- `MAX_RUN_DURATION_MS` из env (дефолт: 4 часа = 14 400 000 мс)
- В `botWorker.ts`: каждый цикл проверяет RUNNING runs с `startedAt < now - MAX_RUN_DURATION_MS`
- Если превышено → `transition(runId, "TIMED_OUT", { errorCode: "MAX_DURATION_EXCEEDED" })`

### Stop All
- `POST /api/v1/runs/stop-all` — останавливает все активные (не-терминальные) runs в workspace
- Возвращает: `{ stopped: string[], errors: string[] }`

### DB Backup
- `deploy/backup.sh` — pg_dump → сжатый .sql.gz с датой
- `deploy/botmarket-backup.service` + `deploy/botmarket-backup.timer` — systemd timer (ежедневно в 03:00)
- Хранит последние 7 бэкапов

## Файлы

```
apps/api/src/app.ts                     (rate limiting)
apps/api/src/lib/botWorker.ts           (max duration)
apps/api/src/routes/runs.ts             (stop-all endpoint)
deploy/backup.sh                        (новый)
deploy/botmarket-backup.service         (новый)
deploy/botmarket-backup.timer           (новый)
deploy/smoke-test.sh                    (новый)
docs/steps/06-stage-6-hardening.md     (этот файл)
```
