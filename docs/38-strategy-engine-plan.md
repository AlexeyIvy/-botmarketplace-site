# 38 — Strategy Engine Improvement Plan

> Статус: **АКТИВНЫЙ** | Создан: 2026-04-20 | Автор: expert review

## Контекст

Production-readiness audit (docs/37) полностью закрыт (#289).
Следующий этап — углубление аналитической мощности торгового движка.

Этот документ разбивает работу на **5 эпиков** и **15 атомарных задач**,
каждая из которых не превышает контекстного окна Claude Code.

---

## Карта эпиков

| # | Эпик | Задачи | Приоритет |
|---|------|--------|-----------|
| E1 | Рефакторинг indicators/ | T1, T2 | 🔴 Высокий |
| E2 | Улучшение бэктеста | T3, T4, T5 | 🔴 Высокий |
| E3 | DSL Optimizer | T6, T7, T8 | 🟡 Средний |
| E4 | Walk-Forward тестирование | T9, T10 | 🟡 Средний |
| E5 | Рефакторинг dslEvaluator | T11, T12, T13, T14, T15 | 🟢 Низкий |

Детали задач: см. **docs/39-strategy-engine-tasks.md**

---

## Зависимости между задачами

```
T1 (indicators публичный API)
  └── T2 (Bollinger экспорт)
        └── T3 (fillAt OPEN_NEXT_BAR)
              └── T4 (метрики Sharpe/PF)
                    └── T5 (BacktestReport v2)
                          ├── T6 (optimizer core)
                          │     ├── T7 (optimizer API endpoint)
                          │     └── T8 (optimizer UI)
                          └── T9 (walk-forward core)
                                └── T10 (walk-forward API + UI)

T11 (извлечь indicatorRegistry)
  └── T12 (извлечь entryEvaluator)
        └── T13 (извлечь exitEvaluator)
              └── T14 (извлечь dcaLoop)
                    └── T15 (dslEvaluator = тонкий оркестратор)
```

E5 (рефакторинг) — параллельная дорожка, не блокирует E2/E3/E4.

---

## Ожидаемые результаты

После выполнения всех эпиков:

- **Каждый индикатор** доступен как переиспользуемая чистая функция
- **Бэктест** реалистичен: нет lookahead bias на entry, есть Sharpe Ratio и Profit Factor
- **Optimizer** автоматически подбирает параметры стратегии по заданной метрике
- **Walk-Forward** выявляет overfit до деплоя стратегии в прод
- **dslEvaluator.ts** разбит на 5 модулей ≤8 KB каждый вместо 40 KB монолита
