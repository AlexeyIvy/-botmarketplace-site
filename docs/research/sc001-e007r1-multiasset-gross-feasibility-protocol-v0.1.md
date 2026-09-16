# SC001-E007R1 — Multi-Asset Gross Feasibility Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE JULY DISCOVERY TRADE BODY ACCESS**

## 1. Purpose

Run a cheap, specification-independent replication screen of the frozen E007 displacement -> partial mean-reversion mechanism before investing further effort in historical discrete execution-spec reconstruction and L2 execution.

This is a **new experiment ID**. It does not reopen or alter terminal `E007_DISCOVERY_FAIL`.

The stage asks only whether the gross price effect has enough multi-asset headroom to justify the next engineering layer.

It must not calculate discrete contract PnL, maker economics, L2 fills, capacity, or promoted net PnL.

## 2. Frozen assets and chronology

Discovery assets only:

- BTC-USDT-SWAP
- ETH-USDT-SWAP
- DOGE-USDT-SWAP
- ORDI-USDT-SWAP
- UNI-USDT-SWAP
- XRP-USDT-SWAP
- OP-USDT-SWAP
- BCH-USDT-SWAP

Performance dates: `2024-07-01..2024-07-14` UTC.

Boundary-only archive dates allowed for causal construction:

- `2024-06-30` — D-1/warm-up only;
- `2024-07-15` — D+1/late-exit reconstruction only.

Asset holdout remains CLOSED:

- SOL-USDT-SWAP
- FIL-USDT-SWAP
- LTC-USDT-SWAP
- SUI-USDT-SWAP

Chronological Confirmation `2024-08-01..14` remains CLOSED.

`2024-07-16..30` remains unassigned/unopened.

## 3. Frozen E007 mechanism

Strict replication of the old E007 signal logic:

- 5-second UTC grid;
- current VWAP over `[t-5s,t)`;
- anchor VWAP over `[t-65s,t-60s)`;
- displacement `D_t = 10,000 * (C_t/A_t - 1)` bps;
- trigger only on strict crossing from prior valid `|D| < 80` to current `|D| >= 80`;
- `D >= +80` => SHORT reversal;
- `D <= -80` => LONG reversal;
- frozen 50% arithmetic retracement target;
- primary trade-proxy latency = 500 ms;
- exit = earlier of target completion or 10-minute max hold;
- daily decision cap = 4;
- one open/pending position maximum;
- 10-minute cooldown after completed exit;
- no new decision after 23:49 UTC;
- no per-asset retuning;
- no TFI or other prior SC001 features.

## 4. Gross-only economics

Completed event gross edge in bps remains:

`direction * 10,000 * (exit_price / entry_price - 1)`

No contract size, lot size, tick size, fee amount in USDT, L2 depth or PnL is used in this screen.

A reference regular-user taker round-trip hurdle of `10 bps` may be used only as a comparative economic floor. It is not labeled an exact historical fee proof.

## 5. Multi-asset feasibility outputs

Report per instrument and pooled across the 8 Discovery assets:

- trigger/decision count;
- completed event count;
- active-day count;
- completion rate;
- mean / median / 10% trimmed gross edge bps;
- positive event share;
- positive active-day share;
- long/short counts and means;
- latency proxy diagnostics at 500/1000/2000 ms using the same frozen events;
- equal-weight instrument mean;
- median instrument mean;
- positive-instrument count;
- top-instrument contribution share;
- day/instrument concentration diagnostics.

## 6. Frozen feasibility gates

This is a **screen**, not promotion.

Exact `E007R1_GROSS_FEASIBILITY_PASS` requires all:

- all 8 Discovery assets attempted;
- at least 6 assets active;
- at least 4 assets with >=5 completed events;
- pooled completed events >=40;
- equal-weight mean instrument gross edge >=20 bps;
- median instrument mean gross edge >=15 bps;
- at least 5/8 instruments with positive mean gross edge;
- pooled 10% trimmed mean >=15 bps;
- pooled median >=10 bps;
- 1000 ms equal-weight mean >=15 bps;
- 2000 ms equal-weight mean >=10 bps;
- no single instrument contributes >35% of absolute pooled gross-edge contribution;
- no accounting/execution invariant is evaluated here because no discrete execution/PnL is permitted.

Any failed mandatory gate gives `E007R1_GROSS_FEASIBILITY_FAIL` and blocks further E007R1 L2/spec engineering.

## 7. Data-acquisition firewall

Before any trade body is opened, a metadata-only preflight must verify the exact official OKX archive identity/HEAD size for all required instrument-date files.

Expected archive set = 8 instruments x 16 dates = `128` daily trade archives.

Preflight exact PASS token:

`E007R1_TRADE_METADATA_PREFLIGHT_PASS`

Only after preflight review may body download be authorized.

## 8. Stop rules

Do not:

- open the 4 asset-holdout symbols;
- open August Confirmation;
- use July 16..30;
- lower the 80 bps trigger;
- change hold/target/latency after output;
- choose profitable symbols and discard losing symbols;
- convert gross bps to promoted PnL before exact historical execution specs are resolved;
- claim this screen is Confirmation or final validation.
