# SC001 Primary Forced-Flow Causal Actionability Audit v0.1

TASK_ID: SC001-P1-FLOW-CLOCK-001
WORKER_ID: P1_PROSPECTIVE_EVENT
TERMINAL_STATUS: CAUSAL_ACTIONABILITY_STATIC_FAIL
Audit class: T0_DESIGN_ONLY_PREOUTCOME_STATIC_AUDIT
Outcome accessed: false
Network used: false
Frozen rules changed: false

## EXACT BINDINGS

This audit is limited to the exact task and frozen S0 bindings at main
`e1de40ede4f9126078cbd84cd87c85f234b2f458`. It does not inspect market
bodies, recompute an outcome, run code, or evaluate alpha.

Source bindings (SHA256):

- `sc001-next-primary-forced-flow-relative-dislocation-s0-protocol-v0.2.md`:
  `331bc684246ed03470c2cb0008e167e7dd01c2efad41a37aa09d2b1122cf7f96`
- mechanism fingerprint v0.2:
  `8d225dbbfb76fe489b3da380d14101c62e1713a14ab3d665f31bd7392d695ea3`
- `sc001_forced_flow_s0_analyzer_v0_1.py`:
  `760096bd0572afa3b53d4b603ac6e33fbfa4b8fbc5934b3ba9061c9a69f171e3`
- `sc001_b13c_s0_source_only_cluster_census_v0_1.py`:
  `601252728e8fa7caf2d9c467d99e61296268a78879a42323725b67bac223db5b`
- B13-C sentinel protocol v0.1:
  `8f8035b0f1e9c7add09732d0e55e399b8a20a4357799193b06e80208b2c54829`
- implementation handshake v0.1:
  `46a20d4045eddbb45040178c4a67b47f5d47967f185ae2647ab043e7a45a20a9`
- input provenance/materialization protocol v0.1:
  `214d16b568b35717481aff7d517b55c94c2b59248c3c51ea31664c77e4dd659e`

Frozen facts used: clusters are per symbol; a consecutive same-symbol event gap
`<= 5000 ms` extends a cluster; an eligible cluster has at least three
distinct, pure-side events and passes the source-gap censor; the first strict
coactive observation second starts in `[E+1000,E+2000)`, where `E` is the
historically selected last cluster event time. H=52 bps, the seven dates, the
12-symbol denominator, signs, sources, and all evidence roles are unchanged.

## CLOCK PROOF WITH INEQUALITIES

Let `E` be the exchange event timestamp of the event later labelled the final
event of a cluster. Let `Delta=5000 ms`. The census appends an event when
`t_i-t_(i-1) <= Delta`; it closes the prior cluster only on a later event with
a strictly greater gap, or at end of the historical input
(`cluster_events`, lines 216-242). It then assigns
`c_end=c[-1]["t"]` and `entry=[c_end+1000,c_end+2000)` (lines 244-260).

Therefore, at event time, finality of the event at E cannot be established
before the no-continuation boundary has passed. Because an event exactly at
`E+Delta` still belongs to the cluster, an operational event-time watermark
must satisfy:

`W > E + 5000`.

Let `L >= 0` denote the not-statically-bounded delay required to establish
that all messages with event time `<= E+5000` have arrived, and let
`P >= 0` be processing/decision delay. Static sources do not establish either
bound. The earliest safe knowledge/order time is therefore:

`K >= W + L + P > E + 5000`.

Now let `S` be the aligned start of the frozen strict-coactive observation
second. The analyzer selects it using
`E+1000 <= S < E+2000` (`cluster_metric`, lines 128-135). Write
`E=1000q+r`, `0 <= r < 1000`. The only aligned S is:

- if `r=0`, `S-E=1000`;
- if `0<r<1000`, `S-E=2000-r`.

Hence for every alignment phase:

`1000 <= S-E < 2000`.

The completed one-second bucket is not available before its end `C=S+1000`,
so:

`2000 <= C-E < 3000`.

Combining the bounds:

`S < E+2000 < E+3000 > C` is not the intended ordering; precisely,
`S < E+2000`, `C < E+3000`, and
`E+3000 < E+5000 < K`.

Thus both the observation-second start and its close precede the earliest
possible knowledge that E was final. This holds for every millisecond alignment
phase. Any unknown late-arrival/watermark delay only widens the gap. No
latency assumption can rescue the frozen E+1..E+2 window.

## EVENT-TIME VS RECEIVE-TIME AND SECOND-CLOSE

The static implementation preserves both liquidation event time `t` and
collector receive time `recv` during parsing (census lines 176-198).
It uses the earliest receive copy for duplicate collapse and sorts by
`(symbol,t,recv,fingerprint)` (lines 199-208). Cluster membership, closure,
`c_end`, and the entry window nevertheless use event time only (lines
216-260). No receive-time watermark or bounded-lateness rule proves when
absence of a continuation became knowable.

The analyzer's cluster schema contains `cluster_end_ms`, count, maximum gap,
and a source-gap flag, but no last-event receive time, closure-observed time, or
watermark (lines 87-103). The coactive schema contains only symbol,
`second_start_ms`, two prices, and `source_identity_pass` (lines 105-125).
It has no underlying last-trade event timestamps, receive timestamps, bucket
close/availability time, or decision time.

The materialization protocol specifies Bybit and OKX
last-valid-trade-per-second files and a strict-coactive intersection, while its
artifact metadata is parent hashes, generator/config identity, row count,
min/max timestamps, and scope (lines 106-124). It does not specify per-row
feed-arrival or completed-bucket availability fields.

The synthetic preflight supplies a historical `cluster_end` and an already
materialized aligned price row, then labels exact-bucket behavior PASS
(analyzer lines 230-274). It tests arithmetic placement, not live closure
knowledge or completed-price availability. Actual exchange-to-collector
latency, lateness distribution, watermark semantics, feed arrival, order
submission, and fill latency are all UNKNOWN from these static sources.

## TRADABILITY / ECONOMIC OBJECT

The measured object is a signed cross-venue relative-basis deviation at one
coactive second. It is a gross state variable, not net Bybit-only capture.
Subsequent basis convergence can occur through Bybit moving, OKX moving, or
both. A one-leg Bybit position is monetized only by the future Bybit price path
and executable fills/costs; basis compression alone does not identify that
return.

No later price, return, spread/cost, fill, lag, or PnL was accessed here.
Accordingly this audit makes no claim about whether the historical basis
deviation predicts a positive or negative Bybit return. It finds only that the
current frozen observation cannot be conditioned on a causally known completed
cluster at that time, and that the economic object is insufficient by itself
to establish one-leg tradability.

## RETROSPECTIVE VS ACTIONABLE EVIDENCE

The current calculation can remain a retrospective, nonpromotional statistic:
given the full historical stream, identify clusters and describe the relative
basis shortly after the event later found to be final. That description is
conditional on future cluster membership.

It is not an actionable live signal. At E+1..E+2, the operator does not yet
know that no same-symbol event at or before E+5s will extend the cluster. The
future absence criterion selects which earlier event receives the label E.
That is lookahead selection even if no later price is inspected. Materialized
last-trade-per-second prices add a second availability requirement: the chosen
chronological last trade is known only after the second can be closed and its
messages are available.

The analyzer directly indexes precomputed seconds and accepts the historical
`cluster_end_ms` (lines 118-150); it neither uses receive timestamps nor
proves that the trigger and completed price bucket existed before a possible
decision/order.

## THREE-LENS VERDICT

- Market/financial: FAIL for promotion. The gross relative dislocation is not
  the same economic object as realizable net Bybit-only capture, and its live
  trigger is unavailable in the frozen window.
- Programmer/trader: FAIL for promotion. Required causal fields and checks -
  closure watermark, receive/availability times, bucket close, decision/order
  time, and execution identity - are absent from the analyzer contracts.
- Mathematician/statistician: FAIL for promotion. For every alignment phase,
  `C-E<3000 ms` while `K-E>5000 ms`; historical terminal-event selection
  conditions the measurement on future information.

Combined verdict: `CAUSAL_ACTIONABILITY_STATIC_FAIL`.

## STRATEGIC_GATE_DISPOSITION

STOP current frozen S0 from execution or tradeable-evidence promotion. The
finding does not invalidate the historical arithmetic as a descriptive
conditional statistic, does not inspect alpha, and does not change any prior
outcome. It establishes that the frozen timing/knowability gate is unsafe for a
live actionability claim.

Strategy review and continuation review are required. No automatic S0 run,
repair, reinterpretation, or same-evidence rescue is allowed.

## NEXT ALLOWED ACTION

The smallest viable future path is a separate Strategy Manager decision for a
new, prospectively frozen successor, not an edit to S0. A successor would need
at minimum:

1. a causally observable trigger time T after inactivity confirmation and an
   explicit event-time/receive-time bounded-lateness or watermark rule;
2. per-event receive/closure-observed timestamps and per-venue last-trade event,
   receive, bucket-close, and availability timestamps;
3. an observation/decision bucket occurring after T and after data
   availability, with decision/order time and execution semantics frozen;
4. a newly frozen economic estimand that separates cross-venue basis state
   from Bybit-only return and costs;
5. independent fresh evidence and contamination allocation under a new task.

The present seven-day/12-symbol/H=52 S0 may be retained only as descriptive,
nonpromotional historical evidence under its existing role.

## DO NOT DO

- Do not shift, widen, reinterpret, or repair the frozen E+1..E+2 window.
- Do not change H=52, dates, symbols, signs, sources, denominator, code, or
  evidence roles.
- Do not inspect later prices/outcomes or run a rescue on the same evidence.
- Do not invent latency or watermark bounds.
- Do not treat a materialized historical row as proof of live availability.
- Do not promote cross-venue basis compression as Bybit-only net capture.
- Do not start a successor without an independent prospective freeze and
  authorization.
- Do not merge, close, retarget, or otherwise mutate PR lifecycle.

## NO ROADMAP CHANGE REQUIRED

This worker has no shared-state write authority. No roadmap, governance,
Strategy State, contamination registry, or reusable registry was changed.
The task-local disposition is a proposed strategic gate for independent
Strategy Manager review; that owner decides any shared-state or roadmap update.
