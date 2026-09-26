# SC001 Current Roadmap and Stop Rules v5.124

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation / B14-A P0 root cause identified / B13-C S0 pre-outcome reversal sentinel frozen**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.123.md`

## B15-P1

Unchanged:
`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Binding P0 disposition:
`B14A_P0_DEFER_DATA`

Root cause:
OKX WebSocket subscribe request used `id=b14ap0-sub`, while current OKX grammar permits only 1-32 alphanumeric characters. Connection succeeded, subscription was rejected with code 60033.

No Sep25 price outcome was opened.

Future event repair is transport-only and prospective.

## B13-C source state

Source-quality census PASS:
- 12/12 qualified symbols;
- observation = 7.5958 days;
- normalized explicit liquidation events = 32,381;
- invalid events = 0;
- reconnects = 13;
- connection gap fraction ~= 0.0413%;
- one process restart;
- process gap fraction ~= 0.00277%;
- collector CONNECTED/RUNNING.

No protected outcome was opened.

## B13-C S0 protocol

Binding pre-outcome protocol:

`docs/research/sc001-b13c-s0-simple-post-liquidation-reversal-sentinel-protocol-v0.1.md`

Core frozen rule:
- all 12 symbols;
- exact protected calibration interval from collector start to census cutoff;
- per-symbol clusters with <=5s inter-event gaps;
- >=3 distinct fingerprints;
- pure-side clusters only;
- no size threshold/weighting;
- gap censoring;
- entry price bucket E+1s..E+2s;
- exit bucket E+31s..E+32s;
- one 30s reversal direction;
- no per-symbol ranking;
- gross headroom hurdle = 30 bps median plus 55% positive share and 4/6 positive complete-day medians;
- minimum 100 valid clusters.

S0 is not PnL Confirmation.

## Price source

Official Bybit public historical trade directories exist for all 12 frozen symbols, and Sep19 2026 daily archive identities are visible publicly.

Archive freshness is not uniform across all symbols/dates yet.

Do not run S0 until all required daily files for the frozen interval are available and schema-qualified.

## Next state

`B13C_S0_PRICE_ARCHIVE_AVAILABILITY_AND_SCHEMA_PREFLIGHT`
