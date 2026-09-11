# BotMarketplace Research Dialog Handoff — 2026-09-11 v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Repository:** `AlexeyIvy/-botmarketplace-site`  
**Canonical roadmap:** `docs/research/r009-r003-strategy-first-roadmap-v3.0.md`  
**Roadmap commit:** `13554741ef47c9113a6f7853bfdf697691ae246c`  
**Purpose:** self-contained context for continuing research in a fresh ChatGPT dialog without losing frozen clocks, decisions, or anti-overfitting constraints.

## 1. Research posture

The project is currently strategy-first, not platform-first. Broad BotMarketplace feature development is frozen while systematic strategies are searched, falsified, forward-tested, and implementation-audited.

Core discipline:

- freeze rules and decision gates before inspecting results;
- prefer falsification over rescue tuning;
- never move a forward inception after seeing data;
- never select a venue, asset, capital tier, or rule version because its observed P&L looks prettier;
- historical evidence is not prospective evidence;
- technical initialization checks do not imply strategy profitability or antifragility;
- no real-capital promotion yet.

The original frozen BTC SMA120 forward record predates newer work and continues independently. Do not reset or merge it into R009/R010.

## 2. Candidate history that matters

### R001 / options

Crisis convexity was observed, but static long puts suffered excessive premium drag and the later IV/RV implementation did not justify promotion. R001 is PAUSED / REDESIGN, not a current execution priority.

### R002 / BTC trend

BTC SMA120 and Donchian trend work remain useful building blocks, but broad-universe rescue/tuning is closed. Do not reopen SMA/Donchian/ADX/volatility/indicator grids from inspected history.

### R008 / crisis-opportunity ladder

The crisis-only ladder is closed as a standalone candidate. Historical diagnostics showed it is mostly conditional/distressed beta rather than proven convex crisis alpha. Do not rescue it with new thresholds, tranche sizes, hysteresis, or hindsight exits.

## 3. R009 — frozen BTC state-dependent beta handoff

### Exact frozen architecture

- TREND10: 120-day SMA; target 10% BTC when `close > SMA120`, otherwise 0%.
- CRISIS10: four 2.5pp tranches armed at closing-ATH drawdowns -20/-35/-50/-65%.
- Once armed, each crisis tranche remains deployed until a new closing ATH.
- Combined target = TREND10 + CRISIS10; range 0-20% BTC.
- Daily self-financing target accounting.
- Cost tracks 5/10/25/50 bps; 10 bps baseline; paper cash return 0%.

R009-E001 historical mechanism screen was `PROMISING_SCREEN / ADVANCE TO FORWARD`, not historical PASS. BTC PRIMARY_LONG at 10 bps was roughly CAGR 15.02%, MaxDD -15.73%, Calmar 0.95, average BTC target 12.91%. Correct economic description: **state-dependent beta handoff**, not proven convexity or rare dry powder.

### Cross-asset falsification

ETH unchanged-rule test = `UNCHANGED_RULE_MIXED`. Fixed BNB/LTC/XRP/ADA/SOL panel = `CROSS_ASSET_BREADTH_MIXED`, 3 SUPPORT / 2 MIXED / 0 FAIL. Do not select BNB/ADA/SOL as winners and do not expand the panel.

Second-pass diagnostics found a recurring weakness: the sticky crisis sleeve can remain active for years, and greater crisis-state persistence is descriptively associated with worse risk efficiency. Most crisis contribution on five of six non-BTC assets occurred while the existing SMA120 trend state was already ON. This retrospective clue motivated R010; it does not authorize changing R009.

## 4. R009-E002 — active BTC forward

**Status:** initialization technically accepted.  
**Fixed inception:** `2026-09-10 00:00 UTC`.  
**Signal bar:** 2026-09-09 closed UTC daily bar.  
**Source:** Binance Spot BTCUSDT daily, fully closed bars only.  
**Frozen engine commit:** `b82b5bb3cd71f6f3ba5efc796684e221c29917e7`.

Initial audited state:

- close 78,306.43;
- SMA120 68,302.24;
- trend ON = 10%;
- three sticky crisis tranches = 7.5%;
- combined target = 17.5%;
- baseline inception fee = 0.000175 NAV;
- no forward-day P&L existed at the initial audit timestamp, which was correct then.

No terminal strategy conclusion before at least 365 realized forward daily intervals. Strong crisis interpretation additionally requires at least one prospective -20% drawdown breach. Do not reset, retune, or replace this record.

Audit: `docs/research/r009-e002-forward-initialization-technical-audit-v0.1.md`.

## 5. R009 implementation granularity — G001/G002 complete

### G001

Status `MECHANICAL_ENVELOPE_ESTABLISHED`.

Frozen current Binance BTCUSDT rules at the snapshot:

- quantity step 0.00001 BTC;
- minQty 0.00001 BTC;
- minNotional 5 USDT;
- reference close 78,306.43.

Continuous 2.5pp notional floor is $200, but the exact step-aware executable threshold is about **$219.26**. The first frozen grid tier where all R009 target states/transitions were statically feasible was **$250**. That is a mechanical floor only.

### G002

Status `DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED`.

Replay 2018-01-01 through 2026-09-09 using the frozen current execution rules. At 10 bps:

- $250: avg target error 0.448pp, P95 1.227pp, max 2.153pp;
- $500: avg 0.238pp, P95 0.658pp;
- $1,000: avg 0.114pp, P95 0.327pp, max 0.542pp;
- $5,000+: near-continuous granularity.

All observed signal-state changes executed even at the smallest tested tiers; the very high raw skipped-order share at small capital came mainly from tiny drift corrections below minimum order size. No negative cash and no trapped exit dust occurred in the frozen baseline replay.

Interpretation: $250 remains a coarse mechanical floor, not a practical minimum. **$1,000 is only a descriptive small-account demo-engineering candidate**, not an optimized or universal minimum. Do not choose account size by historical ending return.

Result docs:

- `docs/research/r009-g001-results-and-technical-audit-v0.1.md` — commit `b3e0960f12f71dae596c8963ba94e0a1b075c6f0`;
- `docs/research/r009-g002-results-and-technical-audit-v0.1.md` — commit `c21861f1459541e5d08f78c6d582ffc4ac4d41d5`.

G003 large-AUM liquidity/capacity is deferred until material scaling or multi-user fanout makes it decision-relevant.

## 6. R003 — funding/basis carry

### Historical E002

Frozen fully funded implementation:

- 50% NAV long BTC spot;
- 50% NAV USDT futures-collateral bookkeeping;
- equal-BTC short perpetual;
- no borrowing or leverage optimization;
- month-end UTC rebalance;
- 10 bps baseline per traded notional per leg; 5/25 bps stress;
- realized/zero/adverse funding tracks.

Historical result = `IMPLEMENTATION_PROMISING`, but recent capital efficiency = `MARGINAL`. PRIMARY_2020 baseline was about CAGR 6.60%, MaxDD -1.33%; POST_2023 about CAGR 3.74%, MaxDD -1.10%. Zero-funding economics were slightly negative, confirming funding as the return source. This is not production/OOS proof.

Frozen safe opportunity-cost references: 13-week Treasury 3.90% annual at inception and diagnostic Treasury+2pp floor 5.90%.

### Binance R003-E003 canonical forward

**Fixed decision boundary:** `2026-09-10 12:00 UTC`.  
**Frozen economic engine:** `cfc001400008ee4d63a27ad6821dda5cb9354f3e`.

Initial establishment at 12:59:59.999 UTC and first following hour were technically accepted. Before the first realized funding event, a code audit found a timestamp-attribution causality defect; the submitted initial snapshot was uncontaminated because funding used = 0.

Future Binance refreshes must use the causality-safe launcher commit:

`4aef73ff696821d762e0822c012459078f7b8a33`

This hotfix changes only timestamp mapping / pandas compatibility, not economics or inception.

A later retry hit Binance HTTP 418. Treat this as a temporary source/access issue. **Do not delete the persistent folder, reset inception, or replace Binance with another venue inside E003.** Retry only when source access permits.

Audit: `docs/research/r003-e003-forward-initialization-technical-audit-v0.1.md`.

### Bybit X001 historical structural replication

Formal result `STRUCTURAL_SIGNAL_MIXED`; data PASS; crisis financing diagnostic compatible. Funding behavior looked economically similar to Binance in aggregate, but the frozen year-concentration gate failed because 2021 contributed ~56.94% of positive completed-year funding returns. Do not rescue by opening a historical Bybit X002.

### Bybit R003-X003 prospective venue forward

Separate parallel record, not a replacement for Binance.

- fixed boundary `2026-09-10 16:00 UTC`;
- initial establishment close 16:59:59.999 UTC;
- first forward hour technically accepted;
- same 50/50 equal-BTC fully funded idea;
- Bybit spot + linear perpetual + mark price + actual funding timestamps;
- month-end rebalance;
- 5/10/25 bps research cost tracks;
- same Treasury opportunity-cost references;
- funding events only after actual timestamp and after portfolio establishment.

Frozen commits:

- protocol `7ba9bf6ca43e4d4936fbca9085f9adfea0a9f116`;
- engine `2ef343190a672a2099654ec91da88c4bef201b9f`;
- launcher `7b92db3b86bb64620b79bc5b8b26c0157439a15c`.

Keep Binance and Bybit histories separate. If they disagree, preserve both; never select the prettier venue retrospectively.

## 7. R010-E001 — active prospective drawdown-armed recovery shadow-forward

R010 exists because the R009 sticky crisis sleeve can become prolonged distressed beta. R010 is a distinct candidate, not a patch or replacement for R009.

Frozen semantics:

- Binance Spot BTCUSDT daily;
- SMA120 TREND10 = 10% when ON, 0% when OFF;
- drawdown breaches -20/-35/-50/-65% arm four 2.5pp tranches;
- armed capital remains cash while trend is OFF;
- while trend is ON, recovery exposure = armed weight;
- if trend turns OFF, recovery exposure returns to cash but arming memory remains;
- only a new closing ATH clears arming memory;
- target 0-20%; no leverage, expiry, hysteresis, cooldown, second indicator, or parameter grid;
- daily self-financing; 5/10/25/50 bps; cash return 0%.

**Fixed signal bar:** 2026-09-10.  
**Fixed forward inception:** `2026-09-11 00:00 UTC`.

Frozen commits:

- protocol `5f13f36712bd48ffdf21292591ddb7b592ba1d03`;
- engine `5088678bdf480a222f9b2cc276ab3573ec4a3639`;
- launcher `e456e32d19437b5fa5cd0e7abc5540a7fc91d5a8`;
- implementation freeze `3c93e58f929fc4065daa8b8fc2230c1a652ed84c`.

Initialization technically accepted. Frozen signal state:

- close 76,568.72;
- SMA120 68,279.3625;
- trend ON;
- 3 inherited armed tranches = 7.5%;
- recovery target 7.5%;
- R010 target 17.5%;
- R009 comparator also 17.5% in that state.

Inherited pre-inception arming is warmup only and is **not** prospective evidence. At initialization all prospective mechanism-event counts were zero.

No terminal R010 conclusion before at least 365 realized forward days. Strong mature interpretation additionally requires at least one **prospective** new arming event and one **prospective** recovery activation event.

Audit: `docs/research/r010-e001-initialization-technical-audit-v0.1.md`, commit `341e1089b84665cbf854756528deb97e73897f39`.

## 8. Safe Sleeve — next priority

S001 has already selected the architecture class:

> **ARCHITECTURE_PREFERRED_FOR_S002: MULTI-DOMAIN LAYERED RESERVE**

The safe layer must separate:

1. off-venue survival reserve;
2. deliberately small execution buffer;
3. crisis-deployment bridge;
4. derivatives collateral.

R003 exchange collateral belongs to derivatives collateral, **not** the safe reserve. Stablecoin balances are not safe reserve by default. A self-custodied stablecoin may be useful as a mobility bridge but still carries issuer/depeg/chain risks.

S002 is now the first new task. It must be **user-access / jurisdiction aware** and compare concrete pathways rather than generic APYs. It should examine accessible banks, brokers/custodians, short T-bills / government MMFs where available, transfer and settlement windows, insurance/custody limits, stablecoin bridge practicality, crisis deployment speed, expected portfolio size, fees and after-tax implications. Do not assume product access before checking it.

S001 reference: `docs/research/safe-sleeve-s001-initial-architecture-assessment-v0.1.md`.

## 9. Minimal demo gate

A minimal paper/demo integration may be considered only after:

- forward plumbing for R009/R003/R010 remains stable;
- S002 identifies a viable reserve/access architecture;
- account-size/granularity assumptions are explicit;
- venue/API failure and reconciliation paths are understood;
- no real capital is needed.

Demo = execution/operations validation only; it is not strategy proof or antifragility proof.

## 10. Immediate execution order in the next dialog

1. Read `docs/research/r009-r003-strategy-first-roadmap-v3.0.md` and this handoff first.
2. Start **Safe-Sleeve S002** as the next design/due-diligence task.
3. Continue R009-E002 unchanged.
4. Continue R010-E001 unchanged from 2026-09-11 00:00 UTC.
5. Continue Bybit R003-X003 unchanged.
6. Retry Binance R003-E003 only when source access permits, using the causality-safe launcher and preserving 2026-09-10 12:00 UTC inception.
7. Keep G003 deferred until liquidity/capacity becomes relevant.
8. Keep broad BotMarketplace platform development frozen.

## 11. Non-negotiable prohibitions

Do not:

- retune R009 from historical or early forward results;
- change R010 thresholds, weights, reset, or inception after launch;
- treat inherited R010 armed tranches as validation;
- replace R009 with R010;
- merge Binance and Bybit R003 forward histories;
- move any forward inception;
- choose a venue/asset/capital tier by prettier observed P&L;
- call exchange cash or stablecoin balances the safe sleeve by default;
- treat demo success as proof of strategy efficacy;
- start real-money deployment now;
- restart broad platform development before the research/implementation gates justify it.

## 12. First instruction for the next clean dialog

Open the canonical roadmap and this handoff. Confirm the four forward clocks are preserved. Then begin Safe-Sleeve S002 by defining exactly what user-access/jurisdiction information is necessary and researching only the concrete implementation pathways that are actually available. Do not redesign any active strategy while doing S002.
