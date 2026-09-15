# SC001-E002 OKX Q1 Taker Execution Economics Protocol v0.2

Date: 2026-09-15  
Status: **FROZEN BEFORE IMPLEMENTATION / BEFORE ANY ECONOMICS OUTPUT**

Supersedes: `sc001-e002-okx-q1-taker-economics-protocol-v0.1.md`.

Reason for v0.2: pre-implementation expert review identified two items that must be pinned before a defensible executable-economics run:

1. period-appropriate contract/minimum-size/tick/fee metadata;
2. perpetual funding treatment for the rare case where a 5-second position spans a funding assessment.

No Q1 execution-economics output had been observed before this revision. Signal, dates, threshold family, latency grid, depth haircuts, sizes, holding horizon and promotion gates are unchanged from v0.1 except where explicitly tightened below.

## 1. Parent protocol retained

All sections and gates of v0.1 remain authoritative unless modified here.

Parent confirmation verdict remains:

`MIDQUOTE_CONFIRMATION_PASS`

Allowed dates remain exactly:

- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

Q2 / formal Validation / Final remain closed.

## 2. External execution metadata freeze

Authoritative metadata freeze:

`docs/research/sc001-e002-okx-q1-execution-metadata-fee-freeze-v0.1.md`

Pinned primary values:

- instrument: `BTC-USDT-SWAP`;
- linear USDT-margined perpetual;
- contract value: `0.01 BTC / contract`;
- Q1 minimum quantity: `1 contract`;
- Q1 quantity step: `1 contract`;
- tick size: `0.1 USDT`;
- primary account tier: regular user / Lv1;
- primary taker fee: `0.05%` per fill (`5 bps` per entry/exit fill rate).

Current post-Q1 `minSz/lotSz` values must not replace the historical Q1 values.

## 3. Exact quantity rule

For each entry candidate and each target-notional scenario:

- use the first fully applied executable L2 state at/after entry arrival;
- calculate `arrival_mid_entry` from best bid/ask of that state;
- `contracts_raw = floor(target_quote_notional / (0.01 * arrival_mid_entry))`;
- Q1 step size is one whole contract, so contract quantity is an integer;
- if `contracts_raw < 1`, use one contract and explicitly report target overshoot;
- contract quantity is frozen at entry and the exact same quantity is closed at exit;
- never resize from future depth, exit price, future score, or P&L.

Actual notional and fee calculations use executable VWAP, not arrival mid.

## 4. Tick-grid integrity gate

Every L2 price used for executable book construction must be an exact multiple of the pinned `0.1` tick under decimal arithmetic.

Any off-grid historical execution price is a metadata/source integrity failure. Do not silently round it.

## 5. Fee ledger

Primary Lv1 taker rate is frozen at `0.0005` per fill.

For every completed trade:

- entry fee = entry executable notional × `0.0005`;
- exit fee = exit executable notional × `0.0005`;
- fees are normalized to entry executable notional for bps reporting;
- entry and exit fees are reported separately;
- zero-fee decomposition remains diagnostic only;
- no VIP/lower-fee scenario may rescue the primary result.

## 6. Funding is now explicitly included

A perpetual position can, in principle, span a funding assessment even with a five-second horizon. Ignoring that would make the economics ledger incomplete.

Historical funding source:

- official OKX public funding-rate history endpoint / OKX historical funding-rate dataset;
- instrument `BTC-USDT-SWAP` only;
- retain the raw funding records used by the run in experiment metadata;
- use the realized rate associated with the funding assessment timestamp.

Default schedule is 00:00 / 08:00 / 16:00 UTC unless the historical record itself shows otherwise. The implementation must key off the actual returned `fundingTime`, not manufacture timestamps.

Official endpoint:

`GET /api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP`

Historical-data landing page:

`https://www.okx.com/en-us/historical-data`

## 7. Conservative primary funding treatment

No funding-time entry exclusion is introduced; that would be a new timing filter.

For the primary promotion ledger, if a position is open across an official historical `fundingTime`:

- charge a conservative cost equal to `abs(realized_funding_rate) * actual_entry_notional`;
- this cost is charged regardless of long/short direction;
- therefore favorable funding receipts cannot create or rescue a PASS;
- if more than one funding event were somehow crossed, sum the absolute-rate costs (not expected for a 5-second hold).

Funding-span condition is conservative-inclusive:

`entry_execution_ts <= fundingTime <= exit_execution_ts`.

A separate diagnostic may report signed economic funding using the historical sign convention, but only the conservative absolute funding charge enters the primary promotion gate.

This treatment intentionally avoids requiring a historical mark-price approximation for a vanishingly small number of boundary trades while ensuring funding cannot improve the primary result.

## 8. Revised net-edge definition

Primary per-trade economics become:

- `gross_midquote_edge_bps` = signed executable-state midquote move;
- `pre_fee_executable_edge_bps` = signed taker VWAP entry-to-exit return;
- `spread_depth_cost_bps` = gross midquote edge − pre-fee executable edge;
- `fee_cost_bps` = entry + exit taker fees normalized to entry notional;
- `funding_cost_bps` = conservative absolute historical funding charge normalized to entry notional;
- `net_edge_bps` = pre-fee executable edge − fee cost − funding cost.

The primary economic metric remains:

**NET EDGE PER TRADE AFTER ALL COSTS**.

## 9. Aggregate outputs added by v0.2

In addition to v0.1 outputs, report:

- funding-crossing trade count;
- mean/median/max conservative funding cost bps;
- raw historical funding records used;
- metadata-source identities and retrieval timestamps;
- tick-grid violation count (must equal zero).

## 10. Promotion gates unchanged in sign and structure

The v0.1 Base / Stress A / Stress B gates are unchanged, except `net_edge_bps` now explicitly includes both taker fees and the conservative funding charge.

Therefore:

- `TAKER_ECONOMICS_PASS` requires Base + 250ms stress + 25% depth-haircut stress after all pinned costs;
- `TAKER_ECONOMICS_WEAK` means Base only;
- `TAKER_ECONOMICS_FAIL` means Base fails;
- WEAK/FAIL keep Q2 closed;
- no rescue tuning.

## 11. Implementation optimization rule

The four frozen days are independent and may be processed in separate OS processes on the qualified 4-vCPU VPS, provided:

- each worker receives immutable frozen parameters;
- each worker reads only its own already-open day data;
- no cross-day adaptive threshold information is shared;
- no partial daily economics are interpreted before all four required days finish;
- final aggregation/verdict runs once after all four worker outputs pass integrity checks.

Process-level parallelism is an implementation optimization only; it may not change execution semantics or gates.
