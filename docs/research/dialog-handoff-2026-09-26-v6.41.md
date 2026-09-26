# SC001 / B15-P1 — dialog handoff v6.41 — 2026-09-26

Current state:

`B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PASS_VPS_READONLY_REVALIDATION_NEXT`

## Latest PASS

Combined offline bundle:

`bundle_20260926T084231Z_2c0e59c2`

Job:

`job_20260926T085440Z_102db938`

Result:

`B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT_PASS`

Bootstrap PASS also confirmed.

No credentials, exchange calls, systemd mutation, collector start, runtime authorization, price/PnL or live execution occurred.

## Next user-visible action

Execute one VPS command:

`sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.3.sh`

This is authenticated read-only capability revalidation only.

It must prove the live Bybit response parses under collector v0.1.4 and that legal `withdrawMax=-1` rows normalize to `UNLIMITED`.

Collector launch remains blocked until this live gate passes.
