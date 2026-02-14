# OpenAPI — how to use

Источник истины для HTTP API MVP:
- `docs/openapi/openapi.yaml`

## Минимальные правила

- Любые изменения HTTP-контрактов вносятся сначала в `openapi.yaml`.
- Изменение контракта должно сопровождаться обновлением связанной документации.
- Ошибки описываются через Problem Details (`application/problem+json`).

## Проверка перед merge

- Спецификация остаётся синтаксически валидной YAML.
- Все добавленные endpoints имеют request/response схему.
- Изменения отражены в changelog.
