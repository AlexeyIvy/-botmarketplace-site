# SC001 parallel research — dialog handoff v6.99 — 2026-09-27

Current:
- B15-P1 W1 accumulation continues.
- B14-A waits for a future prospective expiry.
- B13-C S0 terminal REJECT / RB021 retained.
- B14-B terminal REJECT / RB022 retained.
- B15-P3 fixed redemption path deferred on access feasibility.
- B15-P2 scheduled delisting / forced-close selected as next independent source-only branch.

B15-P2 first census:
- venue = Bybit;
- window = Jan1-Sep27 2026 exclusive end;
- official APIs only:
  - announcements type=delistings;
  - market instruments category=linear status=Closed;
- exact LinearPerpetual + USDT + Closed + deliveryTime identity;
- exclude isPreListing=true;
- exact symbol-token match;
- require pre-event publishTime.

Frozen source gates:
- closed >=5;
- admitted >=5;
- coverage >=80%;
- all lead times >0;
- >=3 delivery months.

No prices/basis/PnL.

Implementation:
`research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1.py`

SHA:
`da047f6dba6881fdfa04db187616b851e1ed35af7af9b33ed6921daed807f8ef`

Next:
commit -> seal no-input offline self-test -> explicit Runner approval -> PASS -> separate approval for networked source-only census.
