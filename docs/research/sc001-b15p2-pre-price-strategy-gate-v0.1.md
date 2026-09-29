# SC001 / B15-P2 — Pre-Price Strategy Gate v0.1

Date: 2026-09-29  
Status: **PASS TO DESIGN PRICE EXPERIMENT / PRICE FIREWALL STILL CLOSED**

## Evidence entering the gate

The exact frozen v0.1.8 full semantic rerun passed over all 94 frozen Bybit delisting events.

Uniform mechanism evidence:

- 94 / 94 exact announced-time matches;
- 94 / 94 explicit trading stop;
- 94 / 94 explicit active/conditional-order auto-cancel;
- 94 / 94 explicit open-position auto-close;
- 94 / 94 closing-price basis = 30-minute average index-price window;
- 76 BLT_RICHTEXT + 18 DOUBLE_DASH_ART_HTML;
- zero unresolved events;
- no price, observed index values, returns or PnL accessed.

Canonical semantic freeze:

`docs/research/sc001-b15p2-semantic-classes-freeze-v0.1.json`

## Role 1 — financial expert / trader

Assessment:

The mechanism is now sufficiently explicit to justify **designing** a prospective economic test.

What is known before price access:

1. there is a known delisting timestamp T;
2. trading ends at T;
3. open positions are forcibly closed;
4. the stated close basis references the 30 minutes before T.

That creates a legitimate microstructure question: whether liquidity, basis, order flow or price behavior changes systematically as T approaches.

What is not known:

- whether any dislocation exists;
- its sign;
- whether it is tradable;
- whether it survives spread, fees and slippage;
- whether usable liquidity exists close enough to T;
- whether the exchange's internal index averaging convention creates any actionable relationship to executable market prices.

Therefore the gate does **not** authorize a strategy claim. It only supports designing a falsifiable price experiment.

## Role 2 — programmer-trader / systems expert

Assessment:

The data-generating mechanism is deterministic enough to build a causal test, provided several implementation boundaries are frozen before any outcome access.

Required engineering constraints:

- use the frozen 94-event IDs only;
- freeze each event's T and announcement observability timestamp;
- define all analysis windows relative to T before reading outcomes;
- separate reference/index data from executable trade/book data;
- never substitute the forced-close reference for an executable fill;
- preserve point-in-time data availability;
- model latency, spread, fees, depth and slippage;
- emit per-event structured diagnostics;
- keep acquisition, signal calculation, execution simulation and aggregation as separate stages.

The Test Executor is now the preferred environment for offline parser/test work. Any protected or large historical market dataset still needs an explicitly designed read-only input boundary rather than broadening host permissions.

## Role 3 — mathematician / statistician

Assessment:

The 94-event frozen sample is large enough to justify a pre-registered exploratory test, but not to skip contamination and robustness controls.

Before observing returns, freeze:

- primary outcome family;
- directionality rule or explicitly two-sided test;
- horizon grid;
- aggregation method;
- event weighting;
- treatment of overlapping events;
- minimum liquidity rules;
- cost assumptions;
- outlier policy;
- robustness splits.

Statistical stop rules:

- no post-hoc horizon cherry-picking;
- no symbol subset selection based on returns;
- no rescue-tuning after a failed primary specification;
- distinguish exploratory secondary results from confirmatory claims;
- require prospective or untouched confirmation before promotion.

## Gate decision

**PASS TO DESIGN PRICE EXPERIMENT.**

This means only that the mechanism is specific enough to formulate a causal, falsifiable next experiment.

It does **not** mean:

- the strategy has edge;
- the strategy is profitable;
- the event is tradable;
- the 30-minute reference window itself is an exploitable signal.

## Frozen mechanism fingerprint

Canonical fingerprint:

`docs/research/sc001-b15p2-mechanism-fingerprint-v0.1.json`

The fingerprint freezes:

- mechanism sequence;
- causal boundaries;
- pre-price hypothesis class;
- edge-to-fill requirements;
- contamination controls;
- capital-time requirements;
- falsification rules.

## Next required step

Design a **pre-registered price/outcome experiment specification** before accessing any affected-contract prices, observed index values, basis, returns or PnL.

That specification must define at minimum:

1. data sources and exact fields;
2. event-relative time grid;
3. primary observable(s);
4. executable-price model;
5. fee/spread/slippage assumptions;
6. horizon grid;
7. aggregation/statistical method;
8. liquidity exclusions;
9. overlap handling;
10. stop/falsification rules;
11. contamination status of every secondary analysis.

Opening the price/outcome firewall remains a separate explicit authorization boundary.

## Firewalls

Still CLOSED:

- price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.
