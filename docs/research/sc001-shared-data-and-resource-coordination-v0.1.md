# SC001 — Shared Data & Resource Coordination v0.1

Date: 2026-10-01
Status: BINDING COMPANION CONTROL FOR MULTI-WORKER DATA / COMPUTE
Scope: BotMarketplace / SCALPING RESEARCH / SC001

Parent architecture:
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.2.md

This document adds resource coordination only. It authorizes no new data access, download, outcome, collector mutation, or research run.

## 1. Problems controlled

Prevent:
- duplicate historical archive downloads;
- duplicate derived datasets;
- two workers acquiring the same resource concurrently;
- disk overcommit from concurrent plans;
- exchange/API request bursts across workers;
- heavy research jobs degrading protected collectors;
- bypass of central execution/rate controls;
- physical dataset presence being mistaken for evidence authorization.

## 2. Core model

Separate three concepts:

1. PHYSICAL RESOURCE
   The bytes exist once in the shared SC001 data store.

2. EVIDENCE ACCESS
   A task is explicitly allowed to open/use those bytes for a stated evidence role.

3. RESEARCH CLAIM
   The resulting analysis may be Selection, Calibration, Discovery, Confirmation, Forward, engineering-only, or nonpromotional.

Physical presence never implies evidence authorization or promotional eligibility.

## 3. Deterministic dataset identity

Every planned raw dataset must have a canonical DATASET_KEY before acquisition.

Required identity fields:
- source_provider;
- source_host / endpoint_class;
- market_type;
- instrument or frozen universe identifier;
- data_kind (trade, kline, funding, L2, metadata, etc.);
- granularity / archive class;
- UTC_start;
- UTC_end_exclusive;
- exact source identity rule (filename/basename/query identity);
- source semantic version when relevant.

RESOURCE_ID:
SHA256(canonical JSON serialization of DATASET_KEY).

The same RESOURCE_ID means the same physical dataset request regardless of worker or strategy.

Do not encode strategy name into RESOURCE_ID.

## 4. Append-only GitHub data registry

Do not maintain one large mutable catalog file.

Use deterministic per-resource records:

Reservation:
docs/research/data-registry/reservations/<RESOURCE_ID>.json

Verified raw dataset:
docs/research/data-registry/datasets/<RESOURCE_ID>.json

Derived dataset:
docs/research/data-registry/derived/<DERIVED_ID>.json

Task-specific evidence-access receipt:
docs/research/data-registry/access/<RESOURCE_ID>--<TASK_ID>.json

This avoids concurrent workers rewriting one central registry.

## 5. Atomic acquisition reservation

Before any network request that could download or materially query an exchange/archive source:

1. compute RESOURCE_ID;
2. check for verified dataset record;
3. check for active reservation;
4. if verified dataset exists: do not download again;
5. if another unexpired reservation exists: do not download;
6. otherwise atomically create the deterministic reservation file.

GitHub create-file semantics are the lock:
- first successful create owns the reservation;
- a second create for the same path must fail closed.

Reservation fields must include:
- resource_id;
- dataset_key;
- task_id;
- worker_id;
- claimed_at_utc;
- lease_until_utc;
- authorization_class;
- user_approval_ref if required;
- expected_bytes;
- estimated_peak_disk_bytes;
- network_hosts;
- max_requests_per_host;
- max_network_bytes;
- retry_budget;
- local_target_logical_path;
- status = RESERVED.

Default acquisition lease:
6 hours unless the task declares a smaller bound.

An expired reservation is not automatically stealable.
Return:
STALE_RESOURCE_RESERVATION_REVIEW

before takeover unless a separately authorized recovery procedure proves that no active job owns it.

## 6. Reuse rule

If a VERIFIED dataset record exists:
- verify local existence/identity before use;
- do not reacquire;
- create a task-specific access receipt;
- access only under the evidence role authorized by that task.

If the task is not authorized to open that evidence class, reuse is forbidden even though the bytes exist.

## 7. Immutable raw cache

Verified raw public market archives should have one canonical physical copy under the shared SC001 data root.

Preferred logical layout:
SC001_DATA_ROOT/_raw_cache/<provider>/<resource_id>/<source_basename>

After verification:
- record SHA256;
- record byte size;
- raw bytes are immutable;
- do not overwrite in place;
- if the same logical source later returns different bytes, quarantine and review rather than silently replacing.

Workers should reference the canonical copy read-only.

Do not create per-worker raw copies unless technically required and explicitly budgeted.

Hard links/symlinks or direct read-only references are preferred when safe and supported.

## 8. Derived-data deduplication

A derived dataset gets:

DERIVED_ID = SHA256(
  ordered parent RESOURCE_IDs +
  transform implementation SHA256 +
  exact config/parameter SHA256 +
  schema version
)

If the exact DERIVED_ID already exists and is verified:
- reuse it;
- do not recompute merely because another worker needs it.

Derived reuse does not change contamination/evidence role; create a separate access receipt for each task.

## 9. One-time legacy inventory bootstrap

Existing SC001 files predate this registry.

Before the first new substantial historical body acquisition after this policy:
perform one bounded READ_ONLY/OFFLINE inventory bootstrap of SC001_DATA_ROOT metadata.

Allowed bootstrap fields:
- logical path;
- basename;
- file size;
- extension/type;
- existing canonical reports that already contain SHA256;
- SHA256 calculation only when explicitly authorized and practical.

Do not parse market rows or outcomes merely to populate the catalog.

Match existing files to DATASET_KEY when identity is mechanically provable.

Uncertain identity:
LEGACY_PRESENT_UNRESOLVED
and do not redownload until reviewed.

This bootstrap is a one-time resource task, not a new research agent.

## 10. Network execution plane

For new REST/API/archive acquisition, the default allowed execution plane is:

BotMarketplace Test Executor / public_research

Current executor-enforced global limits are external runtime constraints and must be checked at execution time.

At policy creation, the observed executor limits were:
- max_concurrent_jobs = 1;
- max_runs_per_rolling_hour = 6;
- max_runs_per_utc_day = 30;
- max_timeout_seconds = 900.

These observed numbers are not frozen forever; execution must read current limits before every run.

Workers must not bypass this plane through:
- direct shell/network jobs;
- alternate VPS execution;
- web/browser downloads;
- ad hoc exchange API requests;
unless a task explicitly authorizes a different plane.

Public documentation lookup is not market-data acquisition.

## 11. Per-source request budget

Every network acquisition task must freeze:
- allowed hosts;
- allowed endpoint classes;
- max requests per host;
- max total downloaded bytes;
- retry count;
- request pacing / minimum inter-request delay where relevant;
- timeout;
- whether HEAD/metadata/body GET is allowed.

No worker may dynamically increase a request budget after encountering source errors.

A source/rate-limit failure returns DEFER/REVIEW, not an alternate-source spray.

## 12. Disk admission control

Before a body download or heavy derived-data job, compute:

ESTIMATED_PEAK_INCREMENT =
remaining_download_bytes
+ temporary_extraction_or_parse_bytes
+ expected_derived_output_bytes
+ explicit safety margin

Default minimum free space after the estimated peak:

MIN_FREE_AFTER =
max(10 GiB, 15% of filesystem total capacity)

A task may require a larger reserve.
A task may not lower this default without explicit resource-policy review.

If:
free_bytes - ESTIMATED_PEAK_INCREMENT < MIN_FREE_AFTER

then:
RESOURCE_DEFER_DISK

Do not start the job.

Every acquisition task also declares:
- MAX_DATASET_BYTES;
- MAX_PEAK_WORKSPACE_BYTES.

Compressed archives must account for decompression/temporary footprint, not only download size.

## 13. Resource classes

Classify execution before run:

LIGHT
- metadata, HEAD, small source audits, small transforms.

MEDIUM
- trade archive parsing / moderate derived datasets.

HEAVY
- multi-GB downloads;
- L2 replay;
- large decompression;
- expected RAM >2 GiB;
- sustained CPU/disk I/O.

Only one HEAVY SC001 resource job may run at a time.

The Test Executor max_concurrent_jobs=1 already serializes its jobs, but the HEAVY rule also applies to other explicitly authorized planes.

## 14. Protected collector priority

During any protected prospective collector window:

COLLECTOR_PROTECTION_MODE = ACTIVE

Default rule:
- LIGHT work allowed if it does not touch collector files or endpoints;
- MEDIUM work allowed only when its resource footprint is bounded and collector health is unaffected;
- HEAVY download/replay work on the same host is DEFERRED by default.

A HEAVY job during a protected window requires explicit:
RESOURCE_ISOLATION_PASS
showing that CPU, disk I/O, storage and network contention cannot threaten the collector, or use of a physically separate execution host.

Collector continuity has priority over historical throughput.

## 15. Partial downloads and recovery

Partial files use a deterministic .part identity owned by the reservation.

Only:
- the owning task;
- or an explicitly approved recovery task

may resume a partial download.

Do not start a second partial file for the same RESOURCE_ID.

On checksum/size/source mismatch:
QUARANTINE_RESOURCE
Do not overwrite or redownload silently.

## 16. Deletion / garbage collection

No automatic deletion of evidence-bearing verified raw data.

Temporary files may be removed after:
- terminal result is canonicalized;
- required hashes are recorded;
- no active task references them.

Reclaimable public raw cache deletion requires a separate bounded storage-maintenance decision.

Disk pressure must block new acquisition before it causes emergency deletion.

## 17. Cross-worker compute coordination

Before expensive computation, workers also check for an exact verified DERIVED_ID.

Do not independently:
- reconstruct the same UTC day;
- normalize the same trade archive;
- replay the same L2 archive;
- build the same feature-neutral base table

when an exact verified reusable derived artifact already exists.

Strategy-specific signals remain separate from shared source/normalization layers.

## 18. Failure tokens

Use explicit resource outcomes:

RESOURCE_REUSE_VERIFIED
RESOURCE_RESERVED_BY_OTHER_TASK
STALE_RESOURCE_RESERVATION_REVIEW
RESOURCE_DEFER_DISK
RESOURCE_DEFER_RATE_LIMIT
RESOURCE_DEFER_COLLECTOR_PROTECTION
RESOURCE_QUARANTINE_IDENTITY_MISMATCH
RESOURCE_READY_FOR_AUTHORIZED_ACQUISITION

These are infrastructure/resource states, not strategy evidence.

## 19. Worker responsibilities

P1/H1/X1 must:
- check the registry before proposing/acquiring data;
- reserve before network access;
- reuse verified resources;
- respect task-specific evidence-access receipts;
- obey current Test Executor limits;
- obey disk admission control;
- avoid HEAVY work that threatens protected collectors.

They must not:
- invent a duplicate workspace because another worker owns the dataset;
- copy raw archives merely for context isolation;
- bypass a reservation via another source/venue;
- interpret physical data presence as clean evidence.

## 20. Strategy Manager responsibilities

The Strategy Manager decides:
- whether an acquisition is worth its research cost;
- evidence role and contamination allocation;
- whether a stale reservation may be recovered;
- whether alternate source acquisition is scientifically legitimate;
- whether a HEAVY job during collector protection is justified.

Routine reuse of an already VERIFIED resource under an already authorized evidence role does not need a new strategic decision.

## 21. No new agent required

This control plane does not create a fourth worker.

Dataset deduplication and resource admission are shared execution rules.

A dedicated Shared Data Infrastructure worker remains deferred until repeated real workload shows that centralized data engineering would save material work.

## 22. Immediate applicability

Current H1/X1 tasks are DESIGN_ONLY and require no network acquisition, so this companion control does not invalidate or block them.

Any future task that proposes historical body download, exchange/API source acquisition, large replay, or reusable derived-data build must reference this document before execution.

No research outcome is authorized by this policy.
