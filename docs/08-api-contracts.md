# Контракты backend API (внутренний API приложения)

Документ описывает маршруты нашего backend API, payloads, требования к авторизации и ошибки.  
Примечание: это **НЕ** Bybit API. Bybit контракты описаны отдельно в `docs/09-bybit-integration.md`.

## 1) Общие правила

MUST:
- Все эндпоинты требуют аутентификацию.
- Все эндпоинты, которые принимают `{id}`, выполняют object-level authorization: найти объект по id, проверить принадлежность `userId/workspaceId`, иначе 404/403. Основание: OWASP API1:2023 BOLA. [web:403]
- Запрет “mass assignment”: обновления принимают только allowlist полей; неизвестные поля игнорируются или дают 400. Основание: OWASP API3:2023 Broken Object Property Level Authorization. [web:497]
- Валидация входных данных по схемам (JSON schema / zod / class-validator).
- Ограничение размера JSON и глубины вложенности.
- Идемпотентность: для торговых intents используем `intentId` (uuid/ulid); для проброса к Bybit используем `orderLinkId` (до 36 символов, уникальный). [web:358]

## 2) Формат ответов и ошибок

### 2.1 Успех
```json
{
  "ok": true,
  "result": {}
}

