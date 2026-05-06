# Roadmap V3 — Review Notes & Known Issues

> Документ фиксирует замечания code review по каждой выполненной задаче.
> Действия помечены как TODO с привязкой к задаче, где их лучше всего исправить.

---

## Task #1 — Fix activateRun() (PR #196)

### Замечание 1.1 — Тесты не тестируют реальный код (severity: HIGH)

**Файл**: `apps/api/tests/lib/activateRunFix.test.ts`

Тесты являются плацебо — они не импортируют и не вызывают реальные функции из `botWorker.ts`. Вместо этого они:
- Дублируют TRANSITIONS граф из `stateMachine.ts` и проверяют копию
- Симулируют catch-блок вручную (`try { throw err } catch { ... }`)
- Проверяют свойства языка (Date comparison, for-of с await)

**Риск**: если кто-то уберёт `await` из `poll()` или удалит `transition` из catch — тесты всё равно пройдут.

**TODO (Task #15 — botWorker тесты, Tier 2)**:
1. Экспортировать `activateRun`, `timeoutExpiredRuns` для тестирования (как `export { activateRun as _activateRun }` или через отдельный test entrypoint)
2. Замокать `prisma` и `transition`, вызвать реальные функции
3. Альтернатива: вынести логику ephemeral timeout detection в pure function (по аналогии с `safetyGuards.ts`), тестировать её отдельно
4. После переписывания — удалить текущий `activateRunFix.test.ts`

### Замечание 1.2 — EPHEMERAL_TIMEOUT_MS не конфигурируется через env (severity: LOW)

**Файл**: `apps/api/src/lib/botWorker.ts:94`

`EPHEMERAL_TIMEOUT_MS` захардкожен как 5 минут. В отличие от `MAX_RUN_DURATION_MS`, нет env override. При текущей архитектуре (single worker) 5 минут — адекватный запас (нормальная активация занимает 3-5 секунд). Но при масштабировании может потребоваться тюнинг.

**TODO (при необходимости)**: добавить `process.env.EPHEMERAL_TIMEOUT_MS` по аналогии с `MAX_RUN_DURATION_MS`.

### Замечание 1.3 — Последовательный await увеличивает длительность poll цикла (severity: INFO)

При 5 QUEUED runs: `5 × (sleep(800) + sleep(1200) + Prisma queries) ≈ 10-12 секунд`. При `POLL_INTERVAL_MS = 4000` это задерживает следующий poll. Приемлемо для single worker, но стоит помнить при масштабировании.

**Связано с**: Roadmap V3 Task #A (убрать искусственные sleep в activateRun).

---

## Task #2 — Fix encryption key missing (PR #197)

### Замечание 2.1 — getEncryptionKeyRaw() throw ломает demo-mode при отсутствии ключа (severity: MEDIUM)

**Файл**: `apps/api/src/lib/botWorker.ts`, функция `reconcilePlacedIntents()`

До фикса: если `SECRET_ENCRYPTION_KEY` не задан, `reconcilePlacedIntents()` тихо пропускала reconciliation, остальной poll цикл работал. Demo-mode боты (без `exchangeConnection`) функционировали нормально.

После фикса: `getEncryptionKeyRaw()` бросает exception, который пробрасывается в `poll()` catch и **завершает весь poll цикл** — включая `evaluateStrategies`, `processIntents` и т.д. Demo-mode боты тоже пострадают, хотя encryption key им не нужен.

**Mitigation**: Task #12 (env validation at startup) сделает `SECRET_ENCRYPTION_KEY` обязательным при старте, поэтому runtime throw никогда не случится. До выполнения Task #12 — убедиться что `SECRET_ENCRYPTION_KEY` задан в `.env` / deployment config.

**Альтернативный TODO (Task #10 — poll per-step isolation)**: когда poll шаги будут обёрнуты в `safeStep()`, throw из `reconcilePlacedIntents` перестанет убивать весь цикл. Это естественно решит проблему.

### Замечание 2.2 — Нет теста на tampered ciphertext (severity: LOW)

**Файл**: `apps/api/tests/lib/encryptionKeyFix.test.ts`

Есть тест wrong-key rejection, но нет теста на повреждённый ciphertext (изменить один байт → decrypt должен бросить ошибку). GCM гарантирует это, но явный тест документирует ожидание.

**TODO (Task #13 — crypto.ts тесты, Tier 2)**: добавить тест на tampered ciphertext и invalid format.

---

## Dependency notes

```
Task #10 (poll per-step isolation) → решает замечание 2.1 (demo-mode resilience)  ✅ DONE
Task #12 (env validation)          → решает замечание 2.1 (startup fail-fast)     ✅ DONE
Task #15 (botWorker тесты)         → решает замечание 1.1 (плацебо-тесты)
Task #A  (убрать sleep)            → решает замечание 1.3 (poll duration)
Task #13 (crypto тесты)            → решает замечание 2.2 (tampered ciphertext)
```

---

## Task #7 — Nginx HSTS + CSP (VPS config)

### Статус: CSP в режиме Report-Only

**Заголовки добавлены:**
- `Strict-Transport-Security: max-age=63072000; includeSubDomains` — **active**
- `Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';` — **report-only**

**TODO**: после проверки browser console на CSP violations — переключить `Content-Security-Policy-Report-Only` на `Content-Security-Policy` в nginx конфиге на VPS.

### Замечание 7.1 — Расхождение имён nginx конфигов (severity: INFO)

На VPS реально активен `/etc/nginx/sites-enabled/botmarketplace.conf`, а не `botmarketplace.ru`. Файл `deploy/nginx.conf` в репо синхронизирован с актуальной структурой (включая upstream блоки).

---

## Tier 1 — Final Status

| # | Задача | PR/Commit | Статус |
|---|--------|-----------|--------|
| 1 | activateRun fix | PR #196 | done |
| 2 | encryption key throw | PR #197 | done |
| 3 | JWT 1h + refresh + prod secret | PR #201 | done |
| 4 | CORS whitelist | PR #198 | done |
| 5 | PrismaClient singleton | PR #198 | done |
| 6 | trustProxy | PR #198 | done |
| 7 | Nginx HSTS + CSP | VPS commit 5202f4f | done (CSP report-only) |
| 8 | Login rate limit | PR #199 | done |
| 9 | Graceful shutdown | PR #200 | done |
| 10 | poll per-step isolation | PR #199 | done |
| 11 | TOCTOU unique constraint | PR #200 | done |
| 12 | Env validation | PR #199 | done |
