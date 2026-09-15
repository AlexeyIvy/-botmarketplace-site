# SC001-E002 OKX Q1 Taker Economics Results v0.1

Date: 2026-09-15  
Status: **TERMINAL FAIL — E002 NOT ECONOMICALLY VIABLE AS FROZEN TAKER RULE**

## 1. Terminal verdict

Frozen executable taker-economics run completed on all four already-open 2024-Q1 OKX days with final verdict:

`TAKER_ECONOMICS_FAIL`

This is a terminal result under `docs/research/sc001-e002-okx-q1-taker-economics-protocol-v0.2.md`.

Q2 / formal Validation / Final remain closed. No rescue tuning is permitted for E002 under this protocol.

## 2. Primary failure diagnosis

The frozen signal retained a small positive pre-fee executable edge, but the edge was vastly smaller than the frozen Lv1 taker fee burden.

Base q95 / 10k / 100 ms / 0% haircut diagnostics observed:

- mean net edge per trade: about `-9.9328368 bps`;
- median net edge per trade: about `-10.0232555 bps`;
- positive daily mean net days: `0 / 4`;
- median daily mean net edge: about `-9.9359002 bps`;
- mean conservative funding cost: about `0.0001842 bps`;
- mean break-even round-trip fee implied by the pre-fee edge: about `0.0671512 bps`.

The frozen actual taker fee is about `10 bps` round trip (5 bps per fill), roughly 149x the observed base break-even round-trip fee.

Therefore the dominant failure mechanism is the fee burden, not funding or lack of visible-book fill capacity.

## 3. Stress diagnostics

### 250 ms latency / 0% depth haircut

- completed trades: `7125`;
- completion rate: `1.0`;
- mean gross midquote edge: about `0.1113430 bps`;
- mean pre-fee executable edge: about `0.0666668 bps`;
- mean spread/depth cost: about `0.0446751 bps`;
- mean fee cost: about `9.9999878 bps`;
- mean funding cost: about `0.0001842 bps`;
- mean net edge: about `-9.9335054 bps`;
- median net edge: about `-10.0232544 bps`;
- positive daily mean net days: `0 / 4`;
- median daily mean net edge: about `-9.9421053 bps`;
- mean break-even round-trip fee: about `0.0664837 bps`.

### 100 ms latency / 25% depth haircut

- completed trades: `7125`;
- completion rate: `1.0`;
- mean gross midquote edge: about `0.1126644 bps`;
- mean pre-fee executable edge: about `0.0581338 bps`;
- mean spread/depth cost: about `0.0545307 bps`;
- mean fee cost: about `9.9999879 bps`;
- mean funding cost: about `0.0001842 bps`;
- mean net edge: about `-9.9420383 bps`;
- median net edge: about `-10.0232583 bps`;
- positive daily mean net days: `0 / 4`;
- median daily mean net edge: about `-9.9451468 bps`;
- mean break-even round-trip fee: about `0.0579496 bps`.

## 4. Interpretation

The earlier midquote-confirmation PASS was a valid predictability result, but it did not imply executable profitability.

The taker-economics layer falsified the economic viability of this frozen E002 rule under realistic same-venue execution accounting:

- visible-book completion was not the bottleneck in the shown primary stress scenarios;
- funding cost was negligible;
- spread/depth consumed part of the already-small signal edge;
- the remaining pre-fee executable edge was only around six to seven hundredths of a basis point;
- the frozen regular-user taker fee burden was about ten basis points round trip.

This gap is too large to treat as a near miss.

## 5. Stop rule

E002 is now closed/downgraded under SC001.

Do not rescue E002 by substituting:

- q90 or q97.5 for q95;
- smaller size as the new primary;
- lower/VIP fees;
- maker execution assumptions;
- long-only or short-only filters;
- event exclusions;
- different holding horizon/window;
- relaxed non-overlap logic;
- Q2 exploration.

A materially different scalp mechanism must be treated as a new, separately frozen research candidate/version. The protected 2024-Q2 OKX holdout remains unopened for E002.
