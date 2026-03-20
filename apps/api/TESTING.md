# Backend Testing Guide

## Quick Start

```bash
# Run all tests once
pnpm --filter @botmarketplace/api test

# Run tests in watch mode (re-runs on file changes)
pnpm --filter @botmarketplace/api test:watch

# From monorepo root
pnpm test:api
```

## Test Runner

We use [Vitest](https://vitest.dev/) — an ESM-native test runner with the same API as Jest but zero-config TypeScript support.

**Why Vitest over Jest:** The project uses `"type": "module"` with TypeScript + ESM. Vitest handles this natively without Babel transforms or experimental flags.

## Directory Structure

```
apps/api/
├── tests/
│   ├── fixtures/        # Shared test data factories
│   │   ├── candles.ts   # Candle generators (uptrend, downtrend, flat)
│   │   └── graphs.ts    # Graph JSON fixtures for compiler tests
│   └── lib/             # Unit tests (mirrors src/lib/ structure)
│       ├── backtest.test.ts
│       ├── dslValidator.test.ts
│       └── graphCompiler.test.ts
└── vitest.config.ts     # Test configuration
```

## Conventions

- Test files: `*.test.ts` under `tests/`
- Discovery is automatic — no need to register new test files
- Fixtures go in `tests/fixtures/` and export factory functions
- Test structure mirrors `src/` structure (e.g., `src/lib/foo.ts` → `tests/lib/foo.test.ts`)

## Adding New Tests

1. Create `tests/<path>/yourModule.test.ts`
2. Import from `vitest` and the module under test
3. Run `pnpm test` — Vitest discovers new `*.test.ts` files automatically

## CI Integration

Add to your CI pipeline:

```yaml
- name: Test API
  run: pnpm --filter @botmarketplace/api test
```
