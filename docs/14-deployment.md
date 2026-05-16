# Deployment (VPS, MVP)

Документ описывает базовый деплой на VPS: сайт, backend API и worker (бот-рантайм).

## 1) Компоненты

MVP:
- `site` (static): текущий репозиторий `/root/public_html` (может раздаваться nginx).
- `api` (backend): HTTP API `/api/*`.
- `worker` (bot runtime): отдельный процесс (может быть в одном бинаре/репо с api, но отдельный service).

## 2) Процессы и systemd

MVP SHOULD:
- Запускать `api` и `worker` через systemd units.
- Включить авто-рестарт при падениях: `Restart=on-failure` (и при необходимости `RestartSec=`). systemd это поддерживает. [web:760]

Пример (шаблон) unit для API:
- файл: `/etc/systemd/system/botmarket-api.service`
- ключевые поля: `After=network-online.target`, `WorkingDirectory=...`, `EnvironmentFile=...`, `ExecStart=...`, `Restart=on-failure`

Важно:
- После правок unit: `systemctl daemon-reload`.

## 3) NGINX reverse proxy

MVP:
- NGINX принимает 80/443.
- `/` -> static site.
- `/api/` -> proxy на backend.

NGINX умеет reverse proxy через `proxy_pass` и базовые сценарии проксирования. [web:772]

SHOULD:
- Пробрасывать заголовки: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

## 4) TLS

MVP SHOULD:
- Использовать Let's Encrypt.
- Настроить авто-обновление сертификатов (certbot renew), затем reload nginx.

## 5) Env vars (минимум)

MVP MUST:
- Секреты не в репозитории, только в env/secret manager (см. `docs/05-security.md`).

Минимальные переменные:
- `BYBIT_API_KEY`, `BYBIT_API_SECRET`
- `JWT_SECRET`
- `WEBHOOK_SECRET`
- `DB_URL`

## 6) Privilege model для `deploy.sh`

Текущее состояние (verified 2026-05-13, follow-up #3):

- `deploy/deploy.sh` не содержит ни одного внутреннего вызова `sudo`. Скрипт целиком ожидает root-окружения: `cp /etc/systemd/system/`, `systemctl daemon-reload`, `systemctl restart botmarket-{api,web,worker}`, `journalctl -u …`.
- На VPS он запускается одной внешней `sudo bash deploy/deploy.sh` либо напрямую под `root`.
- `ubuntu` имеет `NOPASSWD:ALL` из `/etc/sudoers.d/90-cloud-init-users` (cloud-init default). `botmarket` (uid 997) — service-юзер для рантайма, не в sudoers.
- Никаких password-prompt'ов в существующих deploy-логах нет.

Если позже появится отдельный CI-юзер (например `claude-ci`) и захочется убрать его из `sudo ALL=(ALL)`, минимальный sudoers-fragment с принципом least-privilege:

```sudo
# /etc/sudoers.d/botmarket-deploy   (mode 0440, root:root)
Cmnd_Alias BOTMARKET_DEPLOY = \
    /usr/bin/bash /opt/-botmarketplace-site/deploy/deploy.sh, \
    /usr/bin/bash /opt/-botmarketplace-site/deploy/deploy.sh --ref *, \
    /usr/bin/bash /opt/-botmarketplace-site/deploy/deploy.sh --branch *
Cmnd_Alias BOTMARKET_UNITS = \
    /usr/bin/systemctl restart botmarket-api, \
    /usr/bin/systemctl restart botmarket-web, \
    /usr/bin/systemctl restart botmarket-worker, \
    /usr/bin/systemctl is-active botmarket-api, \
    /usr/bin/systemctl is-active botmarket-web, \
    /usr/bin/systemctl is-active botmarket-worker, \
    /usr/bin/systemctl show -p ActiveState --value botmarket-worker
Cmnd_Alias BOTMARKET_LOGS = \
    /usr/bin/journalctl -u botmarket-api *, \
    /usr/bin/journalctl -u botmarket-web *, \
    /usr/bin/journalctl -u botmarket-worker *

claude-ci ALL=(root) NOPASSWD: BOTMARKET_DEPLOY, BOTMARKET_UNITS, BOTMARKET_LOGS
```

Принципы:
- Точные пути бинарей (`/usr/bin/systemctl`, `/usr/bin/journalctl`), без wildcards в путях.
- Wildcards только в аргументах `journalctl` (`-n`, `--since`, `-f`).
- Без `ALL` и без `NOPASSWD:ALL`.

Polkit-альтернатива покрывает только `systemctl`, но не `cp` в `/etc/systemd/system/` — для end-to-end deploy нужен sudoers-путь.

Сейчас этот fragment **НЕ применён**. Появится потребность — применять без расширения области.

