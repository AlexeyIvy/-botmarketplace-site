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

