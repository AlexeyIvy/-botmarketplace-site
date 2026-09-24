# SC001 Current Roadmap and Stop Rules v5.70

Date: 2026-09-24  
Status: **B15-P1 LIVE SOURCE CAPABILITY RETRY READY — PERMISSION BOUNDARY FIXED BY SAFE STAGING**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.69.md`

## Offline prerequisite remains PASS

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_OFFLINE_SELF_TEST_PASS`

No change to collector implementation, frozen identity/route foundation, Stage C cost model or source-capability probe semantics.

## First live attempt

The live wrapper reached Python execution but the `botmarket` runtime user could not read the probe inside the isolated GitHub Control clone:

`Permission denied`

The probe itself never executed.

Therefore:
- exchange calls = 0;
- capability snapshot not written;
- collector launch = false;
- price/PnL = false.

## Root cause

GitHub Control intentionally uses a private clone owned by:

`botmarket-github:botmarket-github`

with an isolated state directory.

This isolation must remain intact.

## Corrected safe wrapper

The wrapper now:
- verifies exact source probe/freeze hashes as root;
- stages only the frozen non-secret probe dependency set under the botmarket home;
- sets staged file ownership to `botmarket:botmarket`;
- verifies staged hashes;
- verifies botmarket readability;
- runs the probe from staging.

No GitHub Control chmod/chown/group broadening is performed.

Corrected wrapper SHA256:

`286804edd60e889fd8a5b4f11d41cb38a73a97cd9214cdf7dfaf9cecca1a9592`

## Retry command

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.1.sh
```

## Next state

`RETRY_B15P1_LIVE_READ_ONLY_SOURCE_CAPABILITY_REVALIDATION`
