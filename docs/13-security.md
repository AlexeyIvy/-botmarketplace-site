# Security (MVP)

Цель: минимальный набор практик безопасности для MVP.

## 1) Secret management

MVP MUST:
- Bybit API key/secret, JWT signing key, webhook shared secret не храним в репозитории.
- Секреты храним в переменных окружения или в менеджере секретов (vault/аналог).
- Доступ к секретам — по минимально необходимым правам.

ASVS отмечает, что API keys/внутренние секреты не должны включаться в исходники и рекомендует использовать secrets management solution (vault/HSM по уровню). [web:752][web:738]

## 2) Auth & sessions

MVP MUST:
- Использовать session tokens (bearer), а не “вечные” статические ключи.
- Делать ротацию refresh-токенов и возможность инвалидировать активные сессии (logout).

ASVS по session management фиксирует требования про уникальность, невозможность угадывания и корректную инвалидизацию сессий. [web:753]

## 3) Webhook signature

MVP MUST:
- Любой входящий webhook подписываем HMAC (shared secret).
- Проверяем: подпись, timestamp (защита от replay), допустимое окно времени.
- Лимитируем частоту запросов per-IP / per-strategy.

## 4) Transport security

MVP MUST:
- Только HTTPS.
- Не логировать секреты, токены, подписи.

## 5) Operational hardening (минимум)

MVP SHOULD:
- Ограничить SSH доступ (ключи, без пароля), фаервол, авто-апдейты безопасности.
- Разделить окружения demo/prod ключами и конфигами.

