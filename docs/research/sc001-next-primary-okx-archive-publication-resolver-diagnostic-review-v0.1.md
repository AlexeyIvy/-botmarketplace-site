# SC001 — OKX Historical Archive Publication / Resolver Diagnostic Review v0.1

Date: 2026-09-30
Status: RECENT PUBLICATION LAG CONFIRMED / RESOLVER CONTRACT VALIDATED
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

Canonical result:
docs/research/sc001-next-primary-okx-archive-publication-resolver-diagnostic-result-v0.1.json

Test Executor job:
job_20260930T191248Z_ab42053b

Network profile:
public_research

## Exact terminal state

OKX_ARCHIVE_DIAGNOSTIC_RECENT_PUBLICATION_LAG

Frozen instrument:
BTC-USDT-SWAP

Frozen dates:
- 2026-09-29
- 2026-09-28
- 2026-09-23

Observed:

2026-09-29:
- resolver response code = 0 on both www.okx.com and us.okx.com;
- structurally valid response;
- exact trusted archive URL count = 0.

2026-09-28:
- exact trusted archive URL count = 1;
- trusted host = static.okx.com;
- HEAD = HTTP 200;
- Content-Length = 17,599,557 bytes.

2026-09-23:
- exact trusted archive URL count = 1;
- trusted host = static.okx.com;
- HEAD = HTTP 200;
- Content-Length = 19,459,479 bytes.

## Interpretation

The previous 0/12 OKX result on 2026-09-29 was not evidence that the OKX historical archive resolver is broken or that historical trade archives are structurally unavailable.

The resolver contract is functional on older completed dates.

The cheapest supported explanation is:

RECENT_PUBLICATION_LAG

The immediate prior UTC day was not yet exposed as the exact daily SWAP archive at the time of the check, while older dates were.

This remains source/transport evidence only. No trade body, price, basis, return, PnL or S0 outcome was opened.

## Operational consequence

Do not move the primary evidence window.

Do not substitute another venue or third-party source.

Post-window S0 materialization must wait until every mechanically required OKX daily archive identity is actually published and HEAD-qualified.

Because the provenance contract mechanically requires the 2026-10-07 OKX archive for the +1s/<+2s boundary observation, the primary S0 cannot be assumed materializable immediately at 2026-10-07T00:00:00Z.

The 2026-10-07 full-day archive itself cannot be complete before 2026-10-08T00:00:00Z, and observed resolver behavior shows that immediate next-day publication cannot be assumed.

Therefore:
- 2026-10-07 remains the evidence-window close;
- the post-window gate checks may begin on 2026-10-07;
- actual trade-body materialization/S0 must wait for exact required archive availability;
- availability must be checked metadata-only before authorization.

No exact future publication timestamp is inferred from this three-date diagnostic.

## Firewalls

Confirmed false:
- archive body access;
- trade-row access;
- price access;
- return/PnL;
- S0 execution.

## Next allowed action

Prepare a metadata-only post-window archive-availability readiness gate covering the exact mechanically required dates and frozen 12-symbol universe.

No body download or S0 authorization is implied.
