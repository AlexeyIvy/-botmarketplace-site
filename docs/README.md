# Bot Marketplace — документация (MVP)

Здесь собраны спецификации и заметки по MVP: интеграция Bybit (demo-first), формат Strategy DSL, рантайм бота, контракты backend API и эксплуатация.

## Навигация

- [Техническое задание (root)](../TECH_SPEC.md)
- [Changelog (root)](../CHANGELOG.md)

### Биржа и торговля
- [Bybit integration](09-bybit-integration.md)

### Стратегии и бот
- [Strategy DSL](10-strategy-dsl.md)
- [Bot runtime](11-bot-runtime.md)

### Backend API
- [API contracts](12-api-contracts.md)
- [OpenAPI (how-to)](openapi/README.md)
- [OpenAPI spec](openapi/openapi.yaml)

### Безопасность и эксплуатация
- [Security](13-security.md)
- [Deployment](14-deployment.md)
- [Operations](15-operations.md)

### План
- [Roadmap](16-roadmap.md)

## Принципы

- Все изменения фиксируем в markdown и коммитим.
- Стратегия декларативная; код стратегии не исполняем.
- Demo-first: торговые операции только в demo до отдельного решения о проде.
