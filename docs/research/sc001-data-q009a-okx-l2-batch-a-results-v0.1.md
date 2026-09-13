# SC001-DATA-Q009A — OKX Q1 L2 Batch A Results v0.1

Status: **PASS**  
Stage: `SC001-DATA-Q009A-OKX-L2-Q1-BATCH-A`

## Outcome

Both frozen Q1 L2 dates completed full-day acquisition/replay qualification successfully.

### 2024-01-14
- archive bytes: `426641072`
- archive status on final run: `REUSED`
- full-day replay: `FULL_DAY_PASS`
- records parsed: `7558603`
- snapshots / updates: `1440 / 7557163`
- UTC coverage: `1440/1440` minutes
- first / last UTC: `2024-01-14T00:00:00+00:00` / `2024-01-14T23:59:59.996000+00:00`
- crossed / empty states: `0 / 0`
- invalid JSON / malformed levels / nonmonotonic timestamps: `0 / 0 / 0`
- max inter-record gap: `492 ms`

### 2024-01-31
- archive bytes: `519114508`
- archive status on final run: `RESUMED`
- resumed from: `71303168` bytes
- market-data bytes fetched on final run: `447811340`
- full-day replay: `FULL_DAY_PASS`
- records parsed: `7753720`
- snapshots / updates: `1443 / 7752277`
- UTC coverage: `1440/1440` minutes
- first / last UTC: `2024-01-31T00:00:00.005000+00:00` / `2024-01-31T23:59:59.994000+00:00`
- crossed / empty states: `0 / 0`
- invalid JSON / malformed levels / nonmonotonic timestamps: `0 / 0 / 0`
- max inter-record gap: `62020 ms`

Total replayed L2 records across the two dates: `15312323`.

## Safety / resumability

The final run read `447811340` market-data bytes. This equals the remaining bytes of the 2024-01-31 archive after resuming from `71303168` bytes. The already completed 2024-01-14 archive was reused with zero additional market-data bytes.

Workspace after outputs: `945768801` bytes. Free storage after outputs: `67170000896` bytes. Frozen safety caps remained respected.

## Firewall

- strategy features calculated: **NO**
- midquote response calculated: **NO**
- strategy P&L calculated: **NO**
- execution profitability calculated: **NO**
- Q2 OKX accessed: **NO**
- formal Validation / Final accessed: **NO**

## Interpretation

Q009A qualifies the first two non-pilot Q1 L2 days for later combined midquote confirmation. It does not expose or calculate alpha on these dates.

The `62020 ms` maximum inter-record gap on 2024-01-31 is retained as a diagnostic. It does not invalidate the file because replay integrity passes, all 1440 UTC minutes are represented, and there are no crossed/empty states or timestamp reversals. Later midquote confirmation must report actual book-state age at signal/response targets rather than silently filtering this condition.

## Next step

Proceed to frozen data-only Q009B for `2024-02-12` and `2024-02-13`. Do not calculate the four-day midquote confirmation until Q009B also passes.
