# SC001 / B15-P1 — dialog handoff v6.18 — 2026-09-24

Current state:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_OFFLINE_SELF_TEST_PASS`

## Offline PASS

- bundle: `bundle_20260924T121552Z_a91e518e`
- job: `job_20260924T122232Z_8fd0930e`
- compile manifest SHA256: `bc8253ab7d928622a13460a96b5d9aca0875840835ff877942df86482aba6ba0`
- self-test manifest SHA256: `686e7151b4b858bcc3513468377b47b07e65fc440577b1e6551b3cbb47ba9f03`

No credentials/network/price/PnL/collector launch occurred.

## Live probe

Probe SHA256:

`489e769665abcefd56bba9937d4179e932083e4545b3d1cac85638adf2b4bf1a`

Freeze SHA256:

`d0332d69208de8cdb4f8fdf9e521ff31b9db02717edbb1b2fae688931af4b4c3`

Use:

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.1.sh
```

Expected live PASS:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`

then wrapper PASS:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_PASS`

Collector launch remains unauthorized after this check.
