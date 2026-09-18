# SC001 Current Roadmap and Stop Rules v4.41

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9 DATA ENGINEERING COMPLETE / C9-S1 SENTINEL FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.40.md`

## 1. Binding terminal states

All prior terminal SC001 states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9 has no strategy verdict yet.

## 2. C9 data-engineering gates complete

### D1 funding integrity

Exact:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS`

with:

- 8/8 assets;
- exact September funding ZIPs;
- 90 unique historical funding timestamps per visible asset;
- 8-hour interval set;
- no C9 strategy outcome.

### D2 mark/index integrity

Exact:

`C9_D2_MARK_INDEX_15M_INTEGRITY_PASS`

with:

- 8/8 assets;
- 2976 mark 15m rows per asset;
- 2976 index 15m rows per asset;
- 2976 exact aligned rows per asset;
- no October UTC mark/index access;
- no premium/return/state-transition/signal/sentinel/PnL.

## 3. October funding incident remains binding

October 2024 funding was contaminated by the D1 v0.2 implementation incident.

It is not clean C9 Confirmation evidence.

October trade/SPOT/L2/mark/index channels remain separately governed.

Current registry:

`docs/research/sc001-contamination-registry-v0.9.json`

## 4. C9-S1 mechanism frozen

Protocol:

`docs/research/sc001-c9-s1-scheduled-post-funding-relative-normalization-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c9_s1_scheduled_funding_normalization_v0_1.py`

Freeze:

`docs/research/sc001-c9-s1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `21549f5b4a0ed984b470cd0bcce0a96a968429d8`;
- runner: `e6e5a551e982ad52f7bcfbfd4a53cd07c3f1e68e`;
- contamination registry: `42202c03259676c1b40937db031e9f08ba30b153`.

## 5. C9-S1 frozen variant budget

Exactly one variant.

No funding magnitude threshold.

No alternate horizon.

No post-outcome sign choice.

No auxiliary feature bundle.

Event set:

- all nonzero September 2024 funding events on the eight frozen assets.

Direction:

- positive funding -> short relative premium;
- negative funding -> long relative premium.

Primary horizon:

- 30 minutes.

## 6. Causal state clock

At funding time `T`:

- pre-state uses the final close of `[T-15m,T)`, observable at `T`;
- post-outcome uses the final close of `[T+15m,T+30m)`, observable at `T+30m`.

No post-`T` value is used in the event-state definition.

## 7. Economic architecture

C9-S1 is screened as paired T3 relative value:

- four structural fills;
- 5 bps per-fill selection reference;
- 20 bps fee-reference floor;
- 30 bps gross screening hurdle.

Mark/index is an idealized relative-state proxy only.

A SURVIVE would justify later executable spot/perp cost research; it would not prove profitability.

## 8. Sample gates

Require:

- pooled evaluable observations >=500;
- each asset >=60 events;
- >=25 UTC calendar days;
- positive-funding observations >=20;
- negative-funding observations >=20.

Failure of these requirements gives:

`C9_S1_DEFER_SAMPLE_OR_SIGN_BREADTH`

No threshold may be changed.

## 9. Economic gates

Require all:

- pooled 10% trimmed mean >=30 bps;
- pooled median >=20 bps;
- equal-weight asset mean >=30 bps;
- median asset mean >=20 bps;
- >=6/8 positive asset means;
- equal-weight calendar-day mean >=30 bps;
- positive calendar-day share >=0.60.

If sample gates pass but any economic gate fails:

`C9_S1_REJECT_SENTINEL`

If all pass:

`C9_S1_SENTINEL_SURVIVE`

## 10. Dual evidence output

S1 must create:

1. Strategy Evidence Report;
2. Feature / Building-Block Evidence Report.

This implements the second-pass governance rule that strategy verdict and reusable feature evidence are recorded separately.

## 11. Hard no-rescue rules

After S1 output do not:

- add funding magnitude threshold;
- keep only positive or negative funding side;
- change 30m horizon;
- add volatility/flow/trend/basis filters;
- select winner assets;
- switch to directional two-fill architecture merely because 30 bps fails.

Any materially different mechanism requires a new ID and fresh design.

## 12. Immediate next action

Run the frozen C9-S1 sentinel exactly once on the declared nonpromotional September calibration data.

No protected promotional data is authorized.
