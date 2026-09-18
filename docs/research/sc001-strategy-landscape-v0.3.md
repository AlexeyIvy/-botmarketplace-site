# SC001 — Strategy Landscape v0.3

Date: 2026-09-18  
Status: **CURRENT COVERAGE MAP AFTER C9-S1 / NON-ALPHA GOVERNANCE ARTIFACT**  
Supersedes: `sc001-strategy-landscape-v0.2.md`

## 1. Inheritance

All terminal/coverage conclusions from v0.2 remain binding.

C1-C6 remain terminal `REJECT_SENTINEL`.

## 2. C9 — scheduled funding / mark-index state

Mechanism:

- M5 relative-value / derivative state;
- M7/P11 scheduled event context;
- paired T3-style screening architecture.

Frozen sentinel:

`C9-S1 scheduled post-funding mark/index relative normalization`

Terminal state:

`C9_S1_REJECT_SENTINEL`

Observed calibration evidence:

- 712 pooled events;
- 89 events per asset across 8 assets;
- 490 positive-funding and 222 negative-funding observations;
- 30 active calendar days;
- pooled 10% trimmed signed normalization about -0.0916 bps;
- pooled median 0.0 bps;
- equal-weight asset mean about -0.0722 bps;
- equal-weight day mean about -0.0776 bps;
- positive-day share about 46.7%.

Coverage implication:

- the tested scheduled funding-sign -> 30-minute mark/index normalization mechanism is now covered with decisive negative selection evidence;
- event frequency and sign breadth were ample;
- economic effect was essentially zero rather than merely below cost.

No funding magnitude threshold, sign-side selection, horizon search, asset subset, or auxiliary feature rescue is authorized under C9-S1.

## 3. Feature-level retained knowledge

C9 still contributes reusable state/reference knowledge:

- scheduled funding clock/funding sign is a valid causal state variable but showed no directional edge in this tested role;
- mark/index premium is a valid derivative-state reference measurement;
- measurement validity does not imply directional alpha.

See:

- `sc001-feature-evidence-registry-v0.3.md`;
- `sc001-reusable-market-building-blocks-registry-v0.2.md`.

## 4. Current under-covered directions

After C1-C6 and C9, the main remaining orthogonal information gaps are:

- C8 cross-venue same-asset clock/dislocation mechanisms;
- C10 L2 liquidity-vacuum/replenishment mechanisms independent of C5;
- C7 spread-qualified maker/hybrid universe independent of BTC E008 rescue.

Under-covered means only information gap, not expected profitability.

## 5. Immediate next direction

Proceed to:

`C8-D0 CROSS-VENUE DATA / CLOCK SEMANTICS`

Before any dislocation outcome:

- freeze venue pair;
- freeze instrument mapping;
- verify historical public source availability;
- verify timestamp units/semantics;
- verify archive identity/checksums;
- verify deterministic synchronization rules;
- calculate no return, lag, spread, dislocation or PnL.

Preferred first audit pair remains OKX + Bybit unless source-contract verification fails.
