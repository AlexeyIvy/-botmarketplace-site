# SC001 Current Roadmap and Stop Rules v5.69

Date: 2026-09-24  
Status: **B15-P1 SOURCE CAPABILITY OFFLINE SELF-TEST PASS / LIVE READ-ONLY REVALIDATION PENDING**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.68.md`

## Offline source-capability self-test

Bundle:
`bundle_20260924T121552Z_a91e518e`

Job:
`job_20260924T122232Z_8fd0930e`

PASS tokens:
- `B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_SELF_TEST_PASS`
- `B15P1_NONPRICE_SOURCE_CAPABILITY_COMPILE_AND_SELFTEST_PASS`

Result:
- exit_code = 0;
- package_integrity_ok = true;
- stderr empty;
- probe compile = PASS;
- EOF/main guard = PASS;
- snapshot contract fixture = PASS;
- frozen admitted assets = 192;
- exchange calls = false;
- credentials required = false;
- capability snapshot written = false;
- collector launch = false;
- price/PnL = false.

Artifacts:
- compile manifest SHA256:
  `bc8253ab7d928622a13460a96b5d9aca0875840835ff877942df86482aba6ba0`
- self-test manifest SHA256:
  `686e7151b4b858bcc3513468377b47b07e65fc440577b1e6551b3cbb47ba9f03`

## Live read-only revalidation

Probe SHA256:

`489e769665abcefd56bba9937d4179e932083e4545b3d1cac85638adf2b4bf1a`

Capability freeze SHA256:

`d0332d69208de8cdb4f8fdf9e521ff31b9db02717edbb1b2fae688931af4b4c3`

Run wrapper:

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.1.sh`

Required live checks:
- Bybit readOnly=1;
- no Bybit Withdraw permission token;
- Bybit IP-bound;
- OKX permission exactly read_only;
- OKX IP-bound;
- authenticated source schema PASS;
- exact public spot-USDT pair qualification against frozen 192 assets;
- one exact account/pair fee metadata probe per venue;
- absolute clock skew <= 10 seconds;
- IPv4-only process-local transport.

## Boundary

Even live capability PASS does not start the collector.

After live PASS:
1. persist secret-free snapshot PASS evidence;
2. verify/install frozen systemd candidate without enabling collector;
3. prepare exact launch authorization;
4. require separate explicit approval for launch.

## Next state

`RUN_B15P1_LIVE_READ_ONLY_SOURCE_CAPABILITY_REVALIDATION_ON_VPS`
