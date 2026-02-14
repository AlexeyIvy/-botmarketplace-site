# Canonical map (source of truth)

Этот документ фиксирует единственный источник истины по каждой теме, чтобы избежать дублей.

## Канонические документы

- **Глоссарий:** `docs/00-glossary.md`
- **Security policies:** `docs/05-security.md`
- **Threat model:** `docs/06-threat-model.md`
- **Data model:** `docs/07-data-model.md`
- **API contracts (human-readable):** `docs/12-api-contracts.md`
- **API contracts (machine-readable):** `docs/openapi/openapi.yaml`
- **Bybit integration:** `docs/09-bybit-integration.md`
- **Strategy DSL:** `docs/10-strategy-dsl.md`
- **Bot runtime:** `docs/11-bot-runtime.md`
- **Deployment:** `docs/14-deployment.md`
- **Operations/observability:** `docs/15-operations.md`
- **Roadmap:** `docs/16-roadmap.md`
- **Foundation execution plan:** `docs/18-foundation-v1-plan.md`
- **Execution control loop / DoD:** `docs/19-cloudcode-control-loop.md`

## Правила

MUST:
- При конфликте формулировок приоритет у канонического документа.
- При изменении контракта/API обновлять `docs/openapi/openapi.yaml` в том же PR.
- Не создавать второй документ на ту же тему; расширять канонический.
