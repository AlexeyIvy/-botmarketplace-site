# SC001-E008 — Conservative Passive Maker Spread-Capture Research Plan v0.1

Date: 2026-09-15  
Status: **PLANNING DOCUMENT — NO E008 PROFITABILITY OUTPUT AUTHORIZED**

## 1. Why E008 exists

SC001 E001-E007 has repeatedly shown that paying a full taker round trip is a severe economic handicap for short-horizon BTC strategies.

The strongest recent taker candidate, E007, produced a positive but insufficient and latency-fragile gross response. E002 separately established that microstructure information can be predictive while still being far too small to pay taker fees.

E008 therefore changes the economic mechanism rather than tuning another taker signal.

Candidate family:

**conservative passive top-of-book spread capture with explicit queue/adverse-selection modeling on OKX BTC-USDT-SWAP.**

This is not a rescue of E002 or E007.

## 2. Core economic hypothesis

A passive market-making strategy may be viable even when standalone directional taker alpha is not, because the base economics are different:

- the strategy attempts to earn part of the bid/ask spread rather than cross it twice;
- execution quality is dominated by fill probability, queue position, adverse selection and inventory risk;
- any predictive microstructure feature is secondary to a viable passive base and may later be tested only as an incremental veto/timing feature under a new experiment identifier.

No maker profitability claim is made by this planning document.

## 3. Existing data assets

Already-qualified L2 data include:

Q009A:
- 2024-01-14 — FULL_DAY_PASS;
- 2024-01-31 — FULL_DAY_PASS.

Q009B:
- 2024-02-12 — FULL_DAY_PASS;
- 2024-02-13 — FULL_DAY_PASS.

These four days contain replay-qualified 400-level OKX BTC-USDT-SWAP order-book data.

They were previously used in E002 infrastructure/midquote work, so they must **not** be treated as pristine validation data for E008. Their first role is data-model feasibility and conservative simulator validation only.

## 4. Immediate data-model question

Before any maker P&L is calculated, determine whether the available historical L2 + trade data are sufficient to support a conservative passive-fill model without hidden optimism.

The first stage must answer only:

1. Are all four qualified L2 archives/reports accessible on the current VPS or reproducibly restageable?
2. Are corresponding trade tapes available for the same UTC dates?
3. Can book updates and trades be causally aligned with deterministic timestamps?
4. Can a conservative queue-ahead state be reconstructed at best bid/ask?
5. Can fills be defined without assuming order priority that the data do not contain?
6. Can price-level depletion/crossing rules distinguish likely fills from simple quote disappearance/cancellation?
7. Is the data rich enough to model adverse selection after a hypothetical passive fill?

If any of these cannot be answered defensibly, E008 pauses before profitability.

## 5. Conservative fill-model philosophy

E008 must default against optimistic fills.

A future executable fill simulator should require, at minimum:

- hypothetical order placed at an observed displayed best price;
- displayed size ahead frozen/updated causally;
- no assumption of jumping the queue;
- fill credit only after sufficient opposite-side executed volume and/or unambiguous price-through evidence under a predeclared rule;
- cancellation/quote disappearance must not automatically count as a fill;
- stale-book states must be rejected or handled by a frozen rule;
- partial fills must be represented explicitly;
- inventory exposure begins only after modeled fill quantity is actually earned;
- opposite-side exit must use an equally conservative rule.

If queue position cannot be reconstructed exactly, the simulator must use a pessimistic lower-bound fill assumption rather than an optimistic proxy.

## 6. Base strategy firewall

Base E008 must initially exclude:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression;
- E006 basis;
- E007 displacement state;
- post-hoc day/hour/news/event filters;
- fee-tier optimization selected after P&L.

The goal is to determine whether passive spread capture is independently viable.

Only after an independently viable base may a new experiment test TFI or another feature as an incremental adverse-selection veto/timing feature.

## 7. Fee and economics treatment

Maker economics must use a frozen account-fee reference before alpha.

Do not rescue a weak strategy by assuming VIP/rebate economics after seeing P&L.

The executable protocol must report at least:

- gross spread capture before fees;
- maker fees/rebates under the frozen reference;
- adverse-selection markout after fill;
- realized round-trip net edge;
- fill rate and partial-fill distribution;
- inventory holding time;
- unmatched inventory count/time;
- turnover and maximum concurrent inventory.

## 8. Chronology and research contamination

The four existing Q009A/Q009B days are already known infrastructure/research days and therefore are unsuitable as the only evidence for promotion.

Proposed sequence:

1. Use Q009A/Q009B strictly for **no-profitability data-model feasibility** and deterministic simulator tests.
2. If feasible, freeze a new E008 executable protocol and a predeclared additional Q1 Discovery date set **before downloading/opening their L2 bodies for E008 profitability**.
3. Acquire only those frozen Discovery dates under data-only integrity protocols.
4. Run one E008 Discovery.
5. Only after a full PASS may a separately frozen, untouched Confirmation date set be acquired/opened.
6. Q2, formal Validation and Final remain closed until a later promotion decision.

## 9. Promotion philosophy

Unlike prior taker experiments, E008 should not be judged by directional forecast bps alone.

Promotion must require jointly:

- conservative fill-model validity;
- nontrivial number of filled round trips across many active days;
- positive net edge after frozen maker fees/rebates;
- robust markout/adverse-selection behavior;
- no dependence on one/few days;
- bounded inventory duration and unresolved inventory;
- stability under harsher queue-ahead assumptions;
- stability under execution latency/book-age stress.

A model that is profitable only under generous fill assumptions is an automatic failure.

## 10. Stop rules

If data-model feasibility fails:

- stop/pause E008;
- do not substitute optimistic queue assumptions;
- do not infer fills from quote disappearance alone;
- do not calculate promotional P&L.

If a later frozen primary profitability test fails:

- do not rescue through VIP fees/rebates;
- do not add TFI or event filters post hoc;
- do not weaken queue-ahead assumptions;
- do not cherry-pick one side/day/time bucket;
- do not open protected Confirmation/Q2/Validation/Final.

## 11. Immediate next action

Create a fail-closed **E008 L2/trade data inventory and synchronization feasibility audit** on the current VPS.

It may output only:

- presence/path/size/hash/status identities;
- replay qualification status;
- corresponding trade-tape availability;
- timestamp overlap and deterministic synchronization facts;
- whether conservative queue-model inputs exist.

It must not output maker P&L, fills, spread capture or strategy profitability.
