# SC001 Current Roadmap and Stop Rules v5.93

Date: 2026-09-26  
Status: **B15-P1 v0.1.4 CAPABILITY v0.2.2 STACK OFFLINE PASS / AUTHENTICATED READ-ONLY VPS REVALIDATION NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.92.md`

## Combined offline gate result

Bundle:

`bundle_20260926T084231Z_2c0e59c2`

Job:

`job_20260926T085440Z_102db938`

Result:

`B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT_PASS`

Bootstrap:

`B15P1_V014_CAPABILITY_V022_STACK_BOOTSTRAP_PASS`

Package integrity = true.  
Exit code = 0.

Artifact SHA256 values:
- capability compile guard:
  `81ec7cb0b4b55b8017324b04e3a77d0c38e52d18c86020a2027c32058af1a7e2`
- capability self-test:
  `3ab81bc9607efaa5a94bda2d3ce51c26dc39dc1f4ca01d6b586fd25e1d775b09`
- stack preflight:
  `075cf2196389158523dc6aad3d9f42261a7200744c0a2e2d50af0d9430e3089a`
- bootstrap:
  `ca2f7b8f75aab5c6da877ae4eb932f798e594ddd47b24f7b4f4021a60f32b1ef`

## What was proven offline

Capability v0.2.2:
- Python compile PASS;
- v0.1.4 runner/library/freeze/service binding present;
- actual v0.1.4 Bybit parser proof present;
- snapshot contract present;
- 192 frozen admitted assets;
- no exchange calls;
- no collector launch;
- no price/PnL.

Live wrapper v0.3:
- Bash syntax PASS;
- 15 exact staged dependencies;
- 2 embedded Python blocks compile;
- one offline self-test invocation;
- one live capability run invocation;
- self-test precedes live run;
- no systemctl mutation;
- no collector start;
- no runtime launch-authorization creation;
- no curl/wget/nc/socat;
- no direct price endpoint path.

## Next host action

Run exactly:

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.3.sh`

on the VPS.

This host action is authenticated but read-only/non-price.

It will:
1. re-check all staged SHA values;
2. re-check collector v0.1.4 32/32 offline PASS;
3. rerun capability v0.2.2 offline self-test from staged bytes;
4. only then use the existing read-only Bybit/OKX API credentials;
5. call the actual v0.1.4 Bybit parser on the live Get Coin Info response;
6. require raw `withdrawMax=-1` count == normalized `UNLIMITED` count;
7. write a new v0.2.2 capability snapshot bound to v0.1.4 hashes.

It does NOT:
- start collector;
- mutate systemd;
- create runtime launch authorization;
- call price endpoints;
- place orders/transfers/withdrawals;
- use PnL.

## Stop rule

Do not relaunch collector yet.

Do not reuse v0.2.1 capability snapshot.

Only a full v0.2.2 authenticated read-only PASS permits preparation of the next controlled collector-launch gate.

## Next state

`RUN_V014_BOUND_AUTHENTICATED_READ_ONLY_CAPABILITY_REVALIDATION_ON_VPS`
