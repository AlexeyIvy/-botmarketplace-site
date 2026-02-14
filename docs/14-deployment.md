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

