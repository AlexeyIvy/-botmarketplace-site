# SC001 — Forced-Flow Archive Metadata Preflight Review v0.1

Date: 2026-09-30
Status: SOURCE / MATERIALIZATION REVIEW — BYBIT 12/12 PASS, OKX 0/12 UNRESOLVED
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

Canonical result:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-archive-metadata-preflight-result-v0.1.json

Test Executor job:
job_20260930T190128Z_c9756e2a

Network profile:
public_research

## Result

Exact terminal token:

FORCED_FLOW_ARCHIVE_METADATA_PREFLIGHT_REVIEW

Qualification date:
2026-09-29 UTC

Bybit:
- 12 / 12 exact expected daily archive identities passed;
- every expected public.bybit.com archive returned HTTP 200 HEAD;
- every archive had positive Content-Length;
- no archive body was downloaded.

OKX:
- 0 / 12 exact expected daily archive identities resolved through the frozen official historical-data metadata resolver;
- both www.okx.com and us.okx.com resolver attempts returned zero exact trusted URLs for every frozen base;
- no fallback source or alternate date was used;
- no archive body was downloaded.

## Interpretation

This is a source/materialization feasibility REVIEW, not a strategy failure and not an alpha result.

The result establishes that the frozen Bybit daily archive transport pattern is available for the qualification date.

It does not establish that OKX historical trade bodies are unavailable in general. It establishes only that the exact frozen resolver/date/filename contract did not resolve the requested 2026-09-29 daily SWAP archives at the time of this single authorized run.

Possible explanations such as publication delay, resolver contract drift, date-boundary semantics or filename/index behavior remain unresolved. They must be investigated as source/engineering questions without opening price/trade bodies.

## Firewalls preserved

Confirmed:
- archive_body_accessed = false;
- trade_rows_accessed = false;
- price_accessed = false;
- cross_venue_ratio_calculated = false;
- returns_calculated = false;
- pnl_calculated = false;
- s0_executed = false.

## Consequence

Do not rerun the same frozen live preflight automatically.

Next allowed work is static/source-engineering investigation of official OKX historical archive publication and resolver semantics only.

Any revised OKX transport contract must:
1. be justified by official/source-structure evidence;
2. remain metadata/HEAD-only;
3. be frozen prospectively;
4. receive separate user approval before a new live run.

No change is authorized to:
- the primary fresh window;
- H=52 bps;
- the 12-symbol denominator;
- the 7-day denominator;
- event/cluster semantics;
- no-peek lock;
- S0 authorization state.
