# SC001 P1 collector health visibility recovery design v0.1

Date: 2026-10-04
TASK_ID: SC001-P1-OPS-001
WORKER_ID: P1_PROSPECTIVE_EVENT
Authorization: DESIGN_ONLY / T0
PR: https://github.com/AlexeyIvy/-botmarketplace-site/pull/429
STRATEGY_REVIEW_REQUIRED: false
TERMINAL_STATUS: COLLECTOR_HEALTH_VISIBILITY_DEFER_INTERFACE

## OBSERVED FAILURE

The exact task and originating Issue #420 report that Test Executor job
`job_20261001T182200Z_53ef4eb0` failed with PermissionError on
`/home/botmarket/sc001_data/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json`
before reading state. This is an access/visibility failure, not evidence that the
collector stopped. The job, state file and VPS were not opened in this task.

Canonical service configuration runs the collector as `botmarket` with
`UMask=0027`. Collector `atomic_json()` creates a temporary file and replaces
the state inode. These facts make identity, directory traversal, namespace/mount
and file permissions relevant possible causes. The exact denied layer and live
permissions are unverified; no chmod/group-membership repair is justified from
this evidence. A one-inode permission fix would also be fragile under replacement.

Baseline: current main `67559b5f837443eb11eb7420a10507471797eacb`;
dispatch PR head `b16bb076a7a98801a9c0f0a1921d2181cce43db1`.
The exact PR manifest explicitly permits one new result file and one worker
commit; this is the later task-specific output budget, distinct from the older
Issue's zero changed-file repair budget. No executable change or repair is made.

## SAFE VISIBILITY REQUIREMENT

Only the following operational fields may be exposed, with fixed schema,
bounded scalar values and explicit UNKNOWN/unavailable states:

| Field family | Intended source and meaning | Limitation |
| --- | --- | --- |
| Process/running state | Fixed B13-C systemd unit ActiveState/SubState; sanitized collector status if separately authorized | A running process does not establish source continuity |
| Connection state | Strict enum from connection_status | CONNECTED is set before subscription acknowledgement; it is not an ACK/completeness certificate |
| Heartbeat freshness | Age of last_heartbeat_ms at a stated observation time | Missing/future/stale timestamps remain unknown/anomalous; never substitute last_message_ms |
| Qualified-symbol count | source_qualified_symbols, integer 0..12 | Startup metadata qualification, not ongoing subscription or market coverage |
| Reconnect diagnostics | reconnect_count and cumulative_gap_ms | Collector-defined counters; not exact loss/coverage estimates |
| Process-gap diagnostics | process_restart_count and cumulative_process_gap_ms | Potential gaps since persisted heartbeat, not independently measured downtime |

Envelope metadata may contain schema/version, fixed collector identity,
observation time, availability/error enums and snapshot age. No symbol list,
raw/event/invalid counts, message timestamps, data-file size/mtime, raw exception
text, log tail, event-frequency proxy, price, size, cluster, return or PnL fields.

Health output must not establish evidence eligibility. The canonical continuity
qualification v0.2 fixes the window as
`2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z`.
Its earlier point-in-time PASS is not a current reading or whole-window proof.
Keep the window, gap censoring, denominator, source and research rules unchanged.

## EXISTING INTERFACE CHECK

Static inspection used current-main canonical source, not live collector files.

| Existing surface | Finding | Disposition |
| --- | --- | --- |
| `ops/systemd/sc001_collectors_status.sh` | Reads entire B13-C state, prints raw/normalized/invalid event counts, reads B14-A state and tails both logs | Do not execute or merely filter its stdout |
| `research/sc001/sc001_b13c_source_quality_state_census_v0_1.py` | Reads entire state, reports counts and events/day, and falls back from heartbeat to stopped/message time | Not suitable for this narrower task |
| `ops/mcp/reader_server_v0_1.py` | Generic root/path file reader; no field-restricted health method in inspected source | Read-only filesystem access is not an evidence firewall |
| B13-C systemd unit and collector v0.3 | Unit-level process status exists conceptually; all six application health families are held in mixed state | Process-only visibility is possible in principle; full safe endpoint is not established |
| Continuity qualification v0.2 | Documents a separately authorized past Runner check | Not a reusable authorization or current health endpoint |

The v0.3 collector blob `ef68b9f1ba82aa17b67b5312822d629666e02201`
matches its implementation freeze. Its ping path refreshes heartbeat every
20 seconds while connected; received messages and shutdown also update it.
The declared HEARTBEAT_SECONDS=30 is not itself an independent heartbeat timer.
Do not interpret stale heartbeat during disconnect/backoff as proof of process death.

No already-existing full, safe, callable health interface was established in
these canonical sources. This is a bounded repository finding; deployed MCP
configuration and service state were deliberately not inspected.

## MINIMAL CHANGE IF NEEDED

PROPOSED_SHARED_STATE_CHANGE: authorize a separate, bounded engineering task for
a fixed-purpose B13-C health adapter. No shared policy or runtime change is
performed here.

Preferred minimal design preserves the collector code, unit, permissions and
restart behavior. A small trusted adapter would read one fixed state object
under separately granted exact authority, project only the allowlist above,
and combine it with a fixed unit-level process query. The consumer receives
only the sanitized health object and never gains generic state/raw-directory
access. This is a new server-side read, not a workaround that makes the
current task's state-read prohibition disappear.

Required implementation constraints, to be frozen in the next exact task:

- Expose one no-argument health method, not arbitrary path, unit, command,
  JSON-key selection or shell access. Use direct APIs/fixed argument vectors.
- Keep the adapter outside the collector process. Restrict its OS filesystem
  view to the exact state source and required unit metadata; deny event/raw/log
  directories, network, writes to collector storage, and service-control actions.
  Do not run an entire generic MCP server as the collector user.
- Open the fixed state through trusted directory handles, reject symlink and
  non-regular-file substitutions, bound input bytes, validate schema/version and
  types, and project known fields into a newly constructed object. Never return
  the original JSON, nested arbitrary fields or exception payloads.
- Atomic replacement is handled by reading one opened inode once. Missing,
  inaccessible, oversized, malformed or mismatched state fails closed with an
  error enum and unavailable fields. Do not retry via raw data/logs or relax ACLs.
- Do not default absent counters to zero. Do not equate stale CONNECTED state
  with a current connection. Report observation/source freshness independently
  from process state and preserve disagreement.
- Bound calls and snapshot cadence; do not publish a high-frequency stream of
  message-driven heartbeat changes. Any cache must disclose age and retain
  UNKNOWN when stale. Exact limits and any health alert threshold must be
  declared prospectively by the implementation task, not inferred from outcomes.
- No daemon-reload/restart of the collector, shared-group expansion, recursive
  chmod, generic sudo, network probe or raw-data mount as a health repair.
  Do not use state mtime as heartbeat: event writes also update it.

If safe isolation of a reader cannot be achieved without broader evidence
access, defer full visibility. A separately authorized process-only method may
return the other five families as unavailable. If source-side sanitized output
would require modifying/restarting the frozen collector, treat that as a
different T3 proposal; do not alter the protected window for convenience.

## OFFLINE VALIDATION

Proposed validation only; no tests, collector imports/self-tests, executor jobs
or Runner bundles ran in this task.

Before any deployment, freeze the adapter interface and run synthetic fixtures
with a fake clock, mocked unit metadata and temporary files containing no real
collector evidence:

1. Allowlist contract: valid connected/disconnected/stopped examples expose
   exactly the declared keys; nested unexpected fields and synthetic secret,
   symbol/event/price markers never reach output, errors or logs.
2. Semantics: running+stale, stopped+recent heartbeat, CONNECTED without ACK,
   missing heartbeat with a recent last_message_ms, future timestamps, count
   boundaries and unavailable unit metadata must not yield a blanket healthy
   or completeness PASS.
3. Identity and parsing: wrong version/stage, null/bool-as-int/negative counters,
   malformed/duplicate-key/oversized JSON, permission denial, missing file,
   FIFO/device, symlink swaps and directory escape fail closed.
4. Atomicity and freshness: state replacement during a read yields one coherent
   snapshot; cache age cannot be reset by a failed refresh; clock anomalies do
   not become fresh heartbeat; call-rate bounds remain enforced.
5. Isolation: instrument filesystem, subprocess and socket access. Assert no
   event/raw/log opens, writes/chmod, collector signals, service-control calls,
   arbitrary unit/path selection or network calls. Test the deployment sandbox
   separately against synthetic directories before granting the real read.
6. Review from the allowlist outward; record exact implementation/deployment
   hashes and limits. Any required access expansion or source change stops for
   the matching authorization instead of weakening tests.

A future implementation PASS would establish adapter behavior only. A separate
authorized live check would establish point-in-time visibility, never full-window
completeness or S0 outcome authorization.

## AUTHORIZATION TIER

Current task: T0 design, one documentation artifact, zero executions, network
research runs, variants and repair cycles.

A new exact task could authorize repository-only implementation and synthetic
validation under T0 where it requires no live privileges, protected access or
shared-component change; shared-component repair requires its applicable review
tier. This document does not dispatch that task.

The proposed live adapter deployment requires **T3 explicit approval for the exact
privilege/interface change and exact state read**, with frozen implementation and
isolation details. Collector permission/source/restart changes are also T3 and
are not implied by approving this design. Runner sealed-bundle execution remains
T3; neither Runner nor Test Executor is needed to complete this design.

No permission change is proposed as an automatic repair. Until a safe interface
is authorized and validated, preserve UNKNOWN visibility and collector continuity.

## TERMINAL DISPOSITION

**COLLECTOR_HEALTH_VISIBILITY_DEFER_INTERFACE**

Design completed; safe full live visibility is not yet available/verified.
No claim is made that the collector is currently unhealthy or that visibility
has been restored. Next decision is whether to authorize the bounded adapter
implementation/deployment described above. No other task is started.

Safety receipts:

```text
outcome_accessed=false
protected_evidence_accessed=false
collector_state_read=false
collector_changed=false
network_accessed=false
test_executor_job_launched=false
runner_bundle_created=false
runner_bundle_executed=false
vps_raw_data_read=false
```

Here network_accessed=false means no research/source-network acquisition or
runtime network probe; authorized GitHub connector reads/writes occurred.

Verification: static requirement/field/boundary review only. The worker writes
only this result file to the existing PR branch, verifies exact readback, then
revalidates main and binding context before setting PR dispatch state TERMINAL
and posting one receipt. No Worker Result Manifest is required. PR/Issue remain
open; no merge, retarget, auto-merge, branch deletion or shared-state write.

### Canonical source identities

All following source blobs were read from main at the baseline above:

- Collector protocol v0.1: `53bbe369b32de9e57046a6f5737ea4f8413f9d28`.
- Operational resilience v0.2: `b058c36c17f35b37b8e329bbdff46ed8d7f7c515`.
- Implementation freeze v0.3: `31829af971a7e0839117e48e0691002e155b2bba`.
- Collector implementation v0.3: `ef68b9f1ba82aa17b67b5312822d629666e02201`.
- `ops/systemd/sc001-b13c-liquidation.service`: `f10e0fa2b66c114a40d2c0fb841ab03b7e797168`.
- `ops/systemd/sc001_collectors_status.sh`: `d6bd276a1db7e12e5aef5b28ce1bd4572cc98c05`.
- Source-quality state census v0.1: `cb05e841c8746489ddf7d80557cb14cbf4d5bac2`.
- `ops/mcp/reader_server_v0_1.py`: `72b8fa5c5cf24ba61004f6dd67c157fd2abe3af1`.
- Operational source continuity qualification v0.2: `bab9cd79c8eaa45c5b2cfc50d99a017a8743251f`.

Binding task manifest blob on the triggered PR:
`26f29c9532745c450d17da7a33cb54a6ea011b2a`.
P1 trigger and worker instructions, architecture v0.3, delegated policy v0.2,
active ratification, resource coordination and repair control were read before
claim. Their current-main context must remain valid at terminal revalidation.
