# SC001 Current Roadmap and Stop Rules v4.48

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8-D1 v0.2 FULL-DAY AS-OF CLOCK REJECTED AS ENGINEERING REPRESENTATION / D1E STRICT COACTIVE 1S FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.47.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 still has no strategy verdict.

## 2. C8-D1 v0.2 clock result

Exact:

`C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_REVIEW`

After correct OKX D+D1 UTC stitching:

- OKX grid share about 0.99024;
- Bybit grid share about 0.97566;
- joint share about 0.96657;
- OKX p99 staleness 1615 ms;
- Bybit p99 staleness 1752.2 ms.

The remaining failure is not an archive-boundary issue.

It is a mismatch between the full-day carry-forward representation and the frozen clock-quality gates.

## 3. No post-hoc threshold loosening

Do not lower or loosen:

- 0.98 venue coverage;
- 0.95 joint coverage;
- 1000 ms p99 staleness;
- 5s max adjacent-gap rule;

to make the v0.2 architecture pass.

The v0.2 representation is retained as:

`FULL_DAY_1S_GRID_WITH_LAST_TRADE_CARRY_FORWARD = NOT_QUALIFIED`

for C8.

This is an engineering architecture verdict, not a strategy verdict.

## 4. Scientific clock redesign

Next representation:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

Reason:

- stale last-trade carry-forward can create false cross-venue dislocations;
- same-second coactivity removes stale-price inheritance;
- no future interpolation is needed;
- engineering suitability can be tested entirely from timestamps before price comparison.

## 5. C8-D1E frozen implementation

Protocol:

`docs/research/sc001-c8-d1e-strict-coactive-1s-clock-qualification-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c8_d1e_strict_coactive_1s_clock_v0_1.py`

Freeze:

`docs/research/sc001-c8-d1e-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `2b3f05c48900c3cf85690e31a4aa4f1d504a060d`;
- runner: `d96fea261f400d8096e84587a67199dfb5d82fd6`;
- contamination registry: `442a5e0462c1d2aa1a7458691c0b08223d641a13`;
- parent clock review: `f3fdcd2b992317636674b05ee27ba18054453be7`.

## 6. D1E representation

For each UTC second:

- venue active only if >=1 trade occurred inside that same second;
- synchronized second only if both venues active in that same second;
- no carry-forward;
- no last observation from a prior second;
- no future interpolation;
- no cross-venue price comparison.

## 7. D1E engineering gates

Require:

- source/body integrity;
- OKX 1440/1440 target UTC minute buckets;
- both venues active in all 24 UTC hours;
- joint coactive seconds >=50,000;
- joint coactive hours =24;
- minimum joint-active seconds in each UTC hour >=600;
- p99 absolute last-event timestamp skew within coactive second <=1000 ms.

## 8. Exact D1E terminal states

PASS:

`C8_D1E_STRICT_COACTIVE_1S_PASS`

REVIEW:

`C8_D1E_STRICT_COACTIVE_1S_REVIEW`

REVIEW remains engineering/timestamp state only.

## 9. Evidence chronology

The 2025-01-15 bodies remain:

`NONPROMOTIONAL_ENGINEERING_CLOCK_CALIBRATION`.

No later C8 price/dislocation sentinel may treat that date as clean promotional evidence.

A later outcome-bearing C8 stage must use a separately declared Selection/Calibration period.

## 10. Immediate next action

Run frozen C8-D1E strict coactive 1-second timestamp-only qualification on VPS.

No cross-venue price/dislocation outcome is authorized.
