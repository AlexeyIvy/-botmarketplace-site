# SC001 Current Roadmap and Stop Rules v4.60

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C7-C10 SLATE COMPLETE / ZERO SURVIVORS / POST-SLATE SYNTHESIS NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.59.md`

## 1. Binding terminal strategy states

All prior terminal states remain immutable.

- C1-C6: `REJECT_SENTINEL`;
- C9-S1: `C9_S1_REJECT_SENTINEL`;
- C8B-S0: `C8B_S0_REJECT_HEADROOM`;
- C10-S0: `C10_S0_REJECT_HEADROOM`;
- C7-S0: `C7_S0_REJECT_SPREAD_HEADROOM`.

No direct rescue tuning is authorized.

## 2. C7-S0 final result

Exact:

`C7_S0_REJECT_SPREAD_HEADROOM`

Observed:

- data-pass assets = 7/7;
- eligible assets = 0/7;
- persistent >=5-second spread>=10-bps episodes = 0 for every asset;
- maker/fill/queue/adverse-selection/PnL = false;
- promotional alpha = false;
- exit code = 0.

Approximate p75 quoted spreads:

- ETH ~0.0401 bps;
- DOGE ~1.2482 bps;
- ORDI ~0.1637 bps;
- UNI ~1.5336 bps;
- XRP ~1.9270 bps;
- OP ~0.2842 bps;
- BCH ~3.6758 bps.

The frozen 10-bps maker-entry/taker-fail-safe architecture has no structural spread headroom.

## 3. C7 consequence

Do not proceed to:

- maker-order simulation;
- queue/fill modeling;
- adverse-selection modeling;
- MDE/promotional Discovery;
- PnL.

Do not lower 10 bps or select a historical winner subset.

Binding postmortem:

`docs/research/sc001-c7-s0-spread-headroom-result-readonly-postmortem-v0.1.md`

## 4. Evidence registries updated

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.6.md`

Current reusable-block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.5.md`

Current landscape:

`docs/research/sc001-strategy-landscape-v0.6.md`

## 5. C7-C10 slate complete

The frozen diversified next-slate sequence:

1. C9;
2. C8;
3. C10;
4. C7;

is complete.

Survivors:

`0`

This is a valid research outcome.

Do not manufacture a new candidate from the nearest miss.

## 6. Binding post-slate synthesis

Current synthesis:

`docs/research/sc001-c7-c10-post-slate-mechanism-building-block-synthesis-v0.1.md`

Primary conclusion:

`measurement validity is often high, but standalone edge/headroom is too small for the required fill architecture`.

Future candidate design must explicitly optimize:

`informational edge scale / structural fill count / cost reserve`.

## 7. Current hard gate

`NO NEW OUTCOME-BEARING C11+ EXPERIMENT YET`

Allowed work only:

- non-alpha candidate design;
- role/redundancy mapping across RB001-RB018;
- data-feasibility review;
- edge-to-fill architecture review;
- prospective interaction hypotheses;
- contamination planning;
- cheapest-sentinel design.

Not allowed:

- new backtests;
- feature-combination outcome mining;
- threshold grids;
- historical winner selection;
- protected/promotional data access.

## 8. Candidate-family design directions

The synthesis identifies three design families for non-alpha review:

### N1 — execution-veto architecture
Use weak microstructure blocks as veto/timing/execution context for an independently defined base opportunity.

### N2 — relative ranking with one-sided execution
Explore RB006 cross-sectional residual rank only under a materially new low-fill-count architecture.

### N3 — regime-dependent execution-mode choice
Use high-validity R2/R6 state primitives to choose maker/taker/no-trade mode for an independent base opportunity.

These are **not yet C11/C12/C13** and no outcome is authorized.

## 9. Immediate next action

Create three non-alpha feasibility cards for N1/N2/N3 using candidate-card template v0.2.

For each card freeze:

- independent base mechanism;
- horizon;
- execution archetype;
- risk signature;
- one primary auxiliary block maximum;
- optional one execution/risk veto maximum;
- expected informational-edge scale;
- structural fill count;
- cost reserve;
- data needs and contamination cost;
- cheapest sentinel;
- stop rule.

Only after card review may at most 2-3 new C11+ candidates be assigned.
