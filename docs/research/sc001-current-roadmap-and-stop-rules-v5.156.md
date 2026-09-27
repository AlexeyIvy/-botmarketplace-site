# SC001 Current Roadmap and Stop Rules v5.156

Date: 2026-09-27
Status: **B15-P2 NETWORKED SOURCE-ONLY CENSUS BOUNDARY FROZEN / AWAITING EXPLICIT NETWORK APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.155.md`

## Binding governance

`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`

remains binding.

No methodology change is introduced here.

## B15-P2 offline prerequisite

The exact source-census offline self-test passed:

`B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V01_SELF_TEST_PASS`

Canonical result:

`docs/research/sc001-b15p2-bybit-delisting-source-census-offline-selftest-result-v0.1.json`

Job:

`job_20260927T164347Z_5e17af47`

No network, real announcements, real instruments, price, basis or PnL were opened by that run.

## Networked source-only boundary

Frozen launch contract:

`docs/research/sc001-b15p2-networked-bybit-source-only-event-census-launch-contract-v0.1.json`

Host wrapper:

`scripts/research/run-b15p2-bybit-delisting-source-census-v0.1.sh`

Wrapper SHA256:

`fb377a3598e7353ec8087ac400f7e3f5db19206eef6717fccd9f765e3085abe5`

Approval code:

`BM-FB377A3598E7`

Networked execution is NOT authorized by this roadmap update.

## Network scope

Only official public Bybit source/event metadata:

- `api.bybit.com/v5/announcements/index`
  with locale `en-US`, type `delistings`;
- `api.bybit.com/v5/market/instruments-info`
  with category `linear`, status `Closed`.

No authentication is required.

## Firewalls

Still forbidden:

- affected-contract price;
- external-reference price;
- index level;
- basis;
- spread;
- pre/post event return;
- PnL;
- event ranking by outcome;
- horizon search from outcome;
- threshold rescue;
- order/trade execution.

## Operational properties

The wrapper:

- verifies exact frozen source SHA values before staging;
- verifies the canonical offline self-test PASS;
- stages only exact non-secret files for user `botmarket`;
- reruns the staged synthetic self-test before any network call;
- launches a one-shot transient systemd unit;
- writes source-only output under `/home/botmarket/sc001_data`;
- uses a one-shot launch marker to prevent accidental duplicate launch;
- provides a read-only `--status` mode;
- retains price/basis/PnL CLOSED.

## Strategy review

Preparation of this boundary is not itself a strategy-relevant event.

A simple source-census PASS does not require Strategy Review.

A meaningful source feasibility DEFER/REVIEW may trigger the Strategy Manager.

Before any B15-P2 price outcome, a Strategy Review / pre-outcome gate remains mandatory for:

- structured mechanism fingerprint;
- mechanism timescale;
- Edge-to-Fill;
- two-mode Minimum Viable Horizon;
- capital-time economics.

## Current branch states

B15-P1:
W1 accumulation / operational freeze unchanged.

B14-A:
`B14A_P0_DEFER_DATA` retained; future prospective retry only.

B13-C:
terminal S0 / RB021 retained; no same-evidence rescue.

B14-B:
terminal / RB022 retained; no same-window rescue.

B15-P2:
networked source-only census boundary frozen, unrun.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_NETWORKED_B15P2_SOURCE_ONLY_CENSUS_BM-FB377A3598E7`
