# Stage 1 — Platform bootstrap: Verification Report

Date: 2026-03-03
Status: **DONE**

## Plan

Цель: подтвердить что Stage 1 (Platform bootstrap) полностью реализован и все acceptance checks воспроизводятся.

Файлы к изменению:
- `docs/21-project-stages.md` — обновить статус Stage 1 с "in progress" → "done"
- `docs/steps/01-stage-1-bootstrap-verification.md` — этот документ

Риски: нет (верификация уже существующего кода, не изменяет бизнес-логику).

## Implementation

Все компоненты Stage 1 были реализованы в ходе предыдущих шагов:

| Компонент | Файл | Статус |
|-----------|------|--------|
| `GET /api/healthz` | `apps/api/src/routes/healthz.ts` | ✅ |
| `GET /api/readyz` | `apps/api/src/routes/readyz.ts` | ✅ |
| `POST /api/auth/login` | `apps/api/src/routes/auth.ts` | ✅ |
| `POST /api/auth/register` | `apps/api/src/routes/auth.ts` | ✅ |
| Frontend Terminal route | `apps/web/src/app/terminal/page.tsx` | ✅ |
| Frontend Lab route | `apps/web/src/app/lab/page.tsx` | ✅ |
| Frontend Factory route | `apps/web/src/app/factory/page.tsx` | ✅ |
| Navbar (Terminal/Lab/Factory) | `apps/web/src/app/navbar.tsx` | ✅ |
| DB schema + migrations | `apps/api/prisma/schema.prisma` + 10 migrations | ✅ |

## Verification

Все acceptance checks пройдены:

```bash
# 1. healthz
curl http://localhost:4000/api/v1/healthz
# → HTTP 200 {"status":"ok","uptime":...,"timestamp":"..."}

# 2. readyz
curl http://localhost:4000/api/v1/readyz
# → HTTP 200 {"status":"ok"}

# 3. auth/login (deterministic stub — wrong creds → 401)
curl -X POST http://localhost:4000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"wrong"}'
# → HTTP 401 {"type":"about:blank","title":"Unauthorized","status":401,"detail":"invalid credentials"}

# 4. DB migrations
pnpm --filter @botmarketplace/api exec prisma migrate status
# → "10 migrations found" / "Database schema is up to date!"

# 5. Frontend routes
curl -o /dev/null -w "%{http_code}" http://localhost:3000/terminal  # → 200
curl -o /dev/null -w "%{http_code}" http://localhost:3000/lab       # → 200
curl -o /dev/null -w "%{http_code}" http://localhost:3000/factory   # → 200
```

Результат: **5/5 pass**.

## Handover

Готово:
- Stage 1 (Platform bootstrap) полностью верифицирован.
- `docs/21-project-stages.md` обновлён: Stage 1 → done.

Следующий шаг: **Stage 2 — Terminal Core** (см. `docs/21-project-stages.md`).
