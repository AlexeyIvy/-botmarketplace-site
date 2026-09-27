# SC001 Current Roadmap and Stop Rules v5.135

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 extractor v0.1 launcher failure isolated / v0.1.1 prepared**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.134.md`

## Failed v0.1 offline self-test

Runner job:

`job_20260927T075438Z_85b2eb56`

Bundle integrity:

PASS

Exit:

`2`

Exact failure:

`argparse: the following arguments are required: --mode`

No self-test body executed.

No:
- network call;
- real price-body access;
- return;
- threshold outcome;
- PnL.

This is not research evidence.

## Root cause

Research Runner v1.0.5 invokes Python entrypoints with:
- package root positional argument;
- exact entrypoint positional argument;

and does not automatically append `--mode self-test`.

Extractor v0.1 incorrectly required explicit `--mode`.

## Corrected v0.1.1

Entrypoint:

`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1_1.py`

SHA256:

`18621a8540d9b2e70f01bf34a0ee103e0eb1dc10fceec33e69a2572d827f1ee0`

Only changes:
- self-test is safe default when `--mode` is absent;
- accepts Runner's two positional launcher arguments;
- fail-closed validates exact package root / entrypoint relationship.

Unchanged:
- 1,905 clusters;
- 76 archives;
- source identities;
- entry/exit bucket semantics;
- parser;
- acquisition architecture;
- S0 thresholds;
- return/PnL firewalls.

## Next state

`SEAL_B13C_S0_PRICE_ANCHOR_EXTRACTOR_V011_OFFLINE_SELFTEST`
