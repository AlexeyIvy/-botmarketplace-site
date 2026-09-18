# SC001 — C8-D0 OKX/Bybit Source & Clock Semantics Protocol v0.2

Date: 2026-09-18
Status: **FROZEN SOURCE-RESOLUTION REPAIR AFTER v0.1 REVIEW / NO ALPHA**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.1.md`

## 1. Trigger

C8-D0 v0.1 returned:

`C8_D0_SOURCE_CLOCK_PREFLIGHT_REVIEW`

with 5/6 checks passed.

Only failure:

`OKX exact historical archive resolution count=0`

for:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

All other source/clock checks passed.

No historical body, cross-venue price, return, dislocation, lag, signal or PnL was opened.

## 2. Repair basis

Earlier SC001 OKX exact-date archive work established that a daily archive label can require discovery via:

1. the archive label day; and
2. the immediately previous metadata-query day.

Therefore v0.2 changes only OKX metadata discovery breadth.

It does not change:

- venue pair;
- instrument pair;
- qualification date;
- archive filename;
- source module;
- Bybit source;
- timestamp semantics;
- body firewall;
- C8 economic hypothesis.

## 3. Frozen OKX archive identity

Target archive remains exactly:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

Historical module:

`module=1`

Instrument type:

`SWAP`

Candidate metadata query windows, in order:

### Query A
`2025-01-15 00:00:00 UTC <= query < 2025-01-16 00:00:00 UTC`

### Query B
`2025-01-14 00:00:00 UTC <= query < 2025-01-15 00:00:00 UTC`

No other metadata date may be queried.

## 4. Exact resolution rule

For each candidate query window:

- request OKX public historical metadata;
- scan only trusted `static.okx.com` links;
- accept only exact filename `BTC-USDT-SWAP-trades-2025-01-15.zip`.

Stop after the first query window that yields at least one exact trusted URL.

After URL de-duplication require exactly one unique exact URL.

Then HEAD only:

- HTTP 200;
- HTTPS;
- host exactly `static.okx.com`;
- basename exact;
- positive Content-Length.

No body GET.

## 5. All other v0.1 checks remain unchanged

Require:

1. OKX instrument semantics PASS;
2. Bybit instrument semantics PASS;
3. OKX current trade timestamp schema PASS;
4. Bybit current trade timestamp schema PASS;
5. repaired OKX exact historical archive metadata/HEAD PASS;
6. Bybit exact historical archive HEAD PASS.

## 6. Exact terminal states

PASS:

`C8_D0_V02_SOURCE_CLOCK_PREFLIGHT_PASS`

REVIEW:

`C8_D0_V02_SOURCE_CLOCK_PREFLIGHT_REVIEW`

REVIEW remains engineering/source state only.

## 7. Firewalls

Must remain false:

- historical archive body downloaded/opened;
- cross-venue price compared;
- cross-venue return calculated;
- dislocation calculated;
- lag calculated;
- leader selected;
- strategy signal calculated;
- PnL calculated;
- promotional alpha accessed.

## 8. Consequence of PASS

v0.2 PASS authorizes only design of C8-D1 historical body/schema/clock synchronization.

No cross-venue outcome is authorized.
