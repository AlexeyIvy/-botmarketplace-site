# SC001 — B14-A P0 Prospective Collector Waiting-State Record v0.1

Date: 2026-09-19
Status: **B14A_P0_COLLECTION_WAITING — PROSPECTIVE EVENT CLOCK ARMED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-p0-collector-self-test-pass-v0.1.md`;
- `docs/research/sc001-b14a-p0-prospective-2026-09-25-headroom-protocol-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.23.md`.

## 1. Observed live state

tmux session:

`b14ap0`

Observed collector state:

`B14A_P0_COLLECTION_WAITING`

Observed:

- connect_at_utc = `2026-09-25T07:28:30+00:00`;
- decision_anchor_utc = `2026-09-25T07:30:00+00:00`.

The collector is armed and waiting prospectively before any B14-A price capture.

## 2. Research implication

No B14-A basis outcome has been consumed.

No threshold, instrument, event time, or headroom rule may be changed before the frozen event.

## 3. Expected transitions

At connect time:

`B14A_P0_COLLECTION_RUNNING`

After frozen capture window:

`B14A_P0_COLLECTION_COMPLETE`

unless operational/source failure causes:

`B14A_P0_COLLECTION_REVIEW`

## 4. Hard rule until event

Do not:

- restart with altered times;
- change instruments;
- alter the 50 bps hurdle;
- inspect alternative expiries;
- open basis/convergence/PnL.

Operational health checks are allowed.

B13-C protected liquidation collector remains independent and should continue running.
