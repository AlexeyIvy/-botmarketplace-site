# SC001 — Normalized Market Schema & Taker Kernel Validation Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN SYNTHETIC ENGINEERING GATE — NO FRESH MARKET BODY ACCESS**  
Scope: **SCALPING RESEARCH / SC001**

## 1. Purpose

Validate the common normalized time/state model and a reusable taker execution kernel before any new July/August 2024 strategy body is opened.

This stage is synthetic-only. It does not calculate E007 or any other strategy signal/PnL and does not resolve historical 2024 instrument specs.

Parent requirements:

- `SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS`, 20/20;
- frozen first-generation universe;
- frozen fresh chronology/asset-holdout roles;
- `docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`.

## 2. Separation of clocks

Future replay code must distinguish at least:

- `source_event_ts_ms`: venue/exchange event time represented by the historical source;
- `observed_ts_ms`: when the strategy is allowed to observe that event under the frozen market-data latency scenario;
- `decision_ts_ms`: when the strategy creates an intent;
- `send_ts_ms`: local outbound send time;
- `activation_ts_ms`: venue-arrival/execution eligibility time.

Synthetic validation must prove that strategy visibility never uses `observed_ts_ms > decision_ts_ms`.

## 3. Execution-only venue state

A taker fill is simulated from the reconstructed opposite-side venue book that is valid at `activation_ts_ms`.

The execution state is allowed to use historical venue state at activation for fill reconstruction, but that state must not be exposed to the strategy if its `observed_ts_ms` would be in the future relative to `decision_ts_ms`.

The kernel must require a book-state interval satisfying:

`valid_from_ts_ms <= activation_ts_ms < valid_to_ts_ms`

A book from after activation may not be back-used. A stale/unknown interval yields unresolved execution, not a fabricated fill.

## 4. Normalized discrete representation

Canonical synthetic execution state uses:

- integer price ticks;
- integer quantity lots;
- deterministic sequence numbers;
- explicit `inst_id`;
- strict positive price/quantity;
- unique price level per side;
- asks strictly ascending;
- bids strictly descending;
- best bid < best ask.

Historical converters later must map raw venue units into this schema only after historical execution specs are resolved.

## 5. Taker execution rule

For BUY:

- consume asks from lowest price upward.

For SELL:

- consume bids from highest price downward.

The kernel:

- never uses the next public trade print as the canonical fill price;
- sweeps visible depth level by level;
- emits one immutable `Fill` per consumed level;
- charges the supplied taker fee in each fill;
- returns explicit unfilled quantity if visible depth is insufficient;
- never invents liquidity beyond the normalized book;
- preserves deterministic fill ordering and IDs.

Insufficient depth is an unresolved/partial execution state, not automatic rejection and not hidden completion.

## 6. Historical specs remain unresolved

Synthetic fixtures use fixture `LinearSpec` values solely to validate mechanics.

This stage must print:

`historical exact execution specs verified = False`

Current OKX instrument metadata may not be used as historical July/August 2024 execution specs.

No real promotional execution/PnL may run until exact historical spec/fee handling is separately frozen and reviewed.

## 7. Required synthetic validation

The runner must cover at least:

1. normalized event accepts causal timestamp order;
2. observed-before-source rejection;
3. strategy future-visibility rejection;
4. valid book interval membership;
5. activation exactly at valid-from accepted;
6. activation exactly at valid-to rejected;
7. crossed book rejection;
8. duplicate level rejection;
9. bad ask ordering rejection;
10. bad bid ordering rejection;
11. BUY single-level fill;
12. SELL single-level fill;
13. BUY multi-level sweep;
14. SELL multi-level sweep;
15. partial depth explicit remainder;
16. zero/negative request rejection;
17. wrong instrument rejection;
18. latency determines activation timestamp;
19. future book state cannot be back-used;
20. deterministic fill IDs/order;
21. accounting reconciliation for BUY->SELL round trip;
22. accounting reconciliation for SELL->BUY round trip;
23. fee drag exactly matches fill ledger;
24. repeated identical run yields identical fill-ledger hash.

## 8. Exact terminal gate

PASS token:

`SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_PASS`

Required summary:

- `tests_passed = 24 / 24`;
- `real market data body accessed = False`;
- `strategy signal calculated = False`;
- `promotional PnL calculated = False`;
- `July/August reserved bodies accessed = False`;
- `historical exact execution specs verified = False`.

Any failed test => exact REVIEW and no progression to real-data execution work.

## 9. After PASS

Only after PASS may SC001 proceed to:

1. exact historical execution-spec/fee evidence handling for the frozen universe/chronology;
2. real-data parser/normalizer engineering on non-promotional or metadata-only evidence;
3. taker-kernel differential/mechanical validation;
4. cheap predeclared E007 economic-feasibility audit;
5. only later, one-shot July Discovery body opening under a frozen manifest.
