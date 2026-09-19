# SC001 Current Roadmap and Stop Rules v5.23

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A P0 COLLECTOR SELF-TEST PASS / PROSPECTIVE WAITING COLLECTION NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.22.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A structural economics

Frozen:

- final structural burden = 37 bps;
- headroom hurdle = 50 bps.

## 3. B14-A P0 self-test

Exact state:

`B14A_P0_COLLECTOR_SELF_TEST_PASS`

Binding result:

`docs/research/sc001-b14a-p0-collector-self-test-pass-v0.1.md`

## 4. Frozen prospective event

Expiry:

`2026-09-25T08:00:00Z`

Decision anchor:

`2026-09-25T07:30:00Z`

Capture:

`2026-09-25T07:29:00Z .. 2026-09-25T08:02:00Z`

## 5. Collector state transition

Start collector now in tmux.

Expected initial state while event is in the future:

`B14A_P0_COLLECTION_WAITING`

At the pre-frozen connection time it should transition to:

`B14A_P0_COLLECTION_RUNNING`

After the capture window:

`B14A_P0_COLLECTION_COMPLETE`

unless an operational/source issue causes:

`B14A_P0_COLLECTION_REVIEW`

## 6. Raw capture firewall

During collection:

- raw trade capture = authorized;
- basis = forbidden;
- convergence = forbidden;
- execution/PnL = forbidden;
- candidate ID = forbidden.

## 7. Immediate action

Launch the P0 collector in a dedicated tmux session and verify:

- tmux alive;
- initial WAITING state;
- frozen expiry/T0;
- no basis calculation.

Do not stop B13-C.
