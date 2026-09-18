# SC001 Current Roadmap and Stop Rules v4.52

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8B-S0 TERMINAL HEADROOM REJECT / C10 NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.51.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal:

`C9_S1_REJECT_SENTINEL`

C8B-S0 is now terminal:

`C8B_S0_REJECT_HEADROOM`

No rescue tuning is authorized.

## 2. C8B-S0 execution/result integrity

Technical completion:

- exit code 0;
- strict coactive seconds = 82,024;
- baseline eligible seconds = 81,904;
- baseline eligible UTC hours = 24;
- all sample gates passed;
- no convergence/return/lag/PnL calculated;
- no promotional alpha accessed.

## 3. C8B-S0 structural result

Observed:

- persistent >=30 bps same-sign two-second episodes = 0;
- episode hours = 0;
- p99 absolute dislocation about 2.4455 bps;
- maximum absolute dislocation about 20.8001 bps.

All frozen headroom gates failed.

Primary failure class:

`AMPLE_SAMPLE_NO_PAIRED_CROSS_VENUE_STRUCTURAL_HEADROOM`

## 4. C8B consequence

Do not proceed to:

- convergence outcome;
- bid/ask reconstruction;
- legging/slippage model;
- paired execution;
- MDE;
- promotional Discovery;
- PnL.

Do not lower:

- 30 bps hurdle;
- two-second persistence;
- five-minute causal baseline;
- 120-observation baseline minimum.

Do not switch to C8A directional lead/lag as a rescue.

A future directional cross-venue candidate requires a new independent ID and prospective design.

## 5. C8 evidence outputs

Binding postmortem:

`docs/research/sc001-c8b-s0-headroom-result-readonly-postmortem-v0.1.md`

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.4.md`

Current reusable-block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.3.md`

Current landscape:

`docs/research/sc001-strategy-landscape-v0.4.md`

## 6. Next-slate sequence

The previously frozen engineering/information-efficiency sequence was:

1. C9;
2. C8;
3. C10;
4. C7.

C9 and C8B have now terminated negatively at structural/sentinel stages.

Next:

`C10 — L2 LIQUIDITY-VACUUM / REPLENISHMENT`

## 7. C10 scientific distinction

C10 must not be C5 + L2.

The base event must be defined directly from order-book state primitives such as:

- near-touch depth collapse;
- spread shock;
- one-sided liquidity vacuum;
- replenishment failure;
- book-slope/microprice discontinuity.

C5 aggressive-flow labels and RB005 are excluded from the initial C10 base mechanism.

## 8. C10 first-stage objective

Use already contaminated/replay-qualified BTC OKX L2 only for a cheap structural pilot.

Before any outcome:

1. verify exact local Q009A/Q009B/E008 L2 identities still exist on VPS;
2. choose one already contaminated pilot day by a non-outcome rule;
3. freeze a book-state event definition;
4. freeze one unconditional future-move horizon;
5. freeze structural magnitude/sample gates;
6. calculate no fill model, queue model or PnL.

## 9. Immediate next action

Run a no-alpha C10 local-data eligibility preflight against the already qualified BTC L2 inventory.

No L2 outcome-bearing calculation is authorized until the C10 event protocol is frozen.
