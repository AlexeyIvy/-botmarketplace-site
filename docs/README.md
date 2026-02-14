# Bot Marketplace — документация (MVP)

Здесь собраны спецификации и заметки по MVP: интеграция Bybit (demo-first), формат Strategy DSL, рантайм бота, контракты backend API и эксплуатация.

## Навигация

- [Техническое задание (root)](../TECH_SPEC.md)
- [Changelog (root)](../CHANGELOG.md)

### Основа проекта
- [Глоссарий](00-glossary.md)
- [Цели и границы](01-goals-scope.md)
- [Tech Stack](17-tech-stack.md)

### Требования
- [Функциональные требования](02-requirements-functional.md)
- [Нефункциональные требования](03-requirements-nonfunctional.md)

### Архитектура и данные
- [Архитектура](04-architecture.md)
- [Data model](07-data-model.md)

### Биржа и торговля
- [Bybit integration](09-bybit-integration.md)

### Стратегии и бот
- [Strategy DSL](10-strategy-dsl.md)
- [Bot runtime](11-bot-runtime.md)

### UI/UX
- [UI/UX](12-ui-ux.md)

### Backend API
- [API contracts](12-api-contracts.md)
- [OpenAPI (how-to)](openapi/README.md)
- [OpenAPI spec](openapi/openapi.yaml)

### Безопасность и эксплуатация
- [Security](05-security.md)
- [Threat model](06-threat-model.md)
- [Deployment](14-deployment.md)
- [Operations](15-operations.md)

### План и приёмка
- [Roadmap](16-roadmap.md)
- [Acceptance criteria](15-acceptance-criteria.md)

### Foundation (execution framework)
- [Foundation v1 plan](18-foundation-v1-plan.md)
- [CloudCode control loop](19-cloudcode-control-loop.md)
- [Canonical map](20-canonical-map.md)
- [Project stages](21-project-stages.md)
- [Stage 1 — bootstrap](steps/01-stage-1-bootstrap.md)

## Принципы

- Все изменения фиксируем в markdown и коммитим.
- Стратегия декларативная; код стратегии не исполняем.
- Demo-first: торговые операции только в demo до отдельного решения о проде.
