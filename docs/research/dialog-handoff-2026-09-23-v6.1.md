# SC001 / B15-P1 — dialog handoff v6.1 — 2026-09-23

## Resume point

Independent branch:

`SCALPING RESEARCH / SC001 / B15-P1`

Latest successful research state:

`B15_P1_SPECIAL_HANDLERS_GRAVITY_POLICY_PREFLIGHT_PASS`

Next research state:

`BUILD_INTEGRATED_CANONICAL_REGISTRY_V02_REPLAY_CANDIDATE`

Prepared sealed bundle, not yet run:

- bundle: `bundle_20260923T165147Z_98f25758`
- SHA256: `0d21aeaa6a829ade283b6ec69d6fd41552a3832d24eaa4efb2f624abf9e39ec0`
- approval code: `BM-0D21AEAA6A82`

Resume by running this exact sealed bundle after explicit approval. Do not rebuild or retune upstream identity decisions unless an independent integrity check fails.

## Replay acceptance targets

Use the exact frozen `20260920T210446Z` Bybit/OKX identity snapshot.

Expected:

- integrated network rows: 76,
- native rows: 66,
- identity-closed assets: 42,
- IDENTITY_REVIEW assets exactly:
  - GRAM,
  - QTUM,
  - STX,
  - XLM,
- asset common representations: 48,
- USDT common representations: 12,
- remaining unresolved rows: 9,
- alias collisions: 0.

Any mismatch prohibits freeze.

## Special semantics that must be preserved

- `BRC20_TICKER_NORMALIZATION`
- `CARDANO_POLICY_ASSET_ORDER_NORMALIZATION`
- `CELO_GOLDTOKEN_NATIVE_INTERFACE`
- `WAXP_EOSIO_TOKEN_NATIVE_INTERFACE`
- `ZKSYNC_ERA_ETH_SYSTEM_BASE_TOKEN`

Exact CELO semantics:

- identity kind: `native_erc20_interface`
- representation: `native:CELO`

Exact WAXP semantics:

- identity kind: `native_contract_account`
- representation: `native:WAXP`

## Gravity Alpha lifecycle gate

- before `2026-11-01`:
  `REVALIDATION_REQUIRED_BEFORE_RUNTIME_ROUTE`
- on/after `2026-11-01`:
  `ROUTE_DISABLED_DEPRECATED`

No automatic route enablement.

## GitHub Control MCP — completed

The dedicated GitHub read/write MCP was fully connected and verified end-to-end.

Verified live sequence from ChatGPT:

1. `get_github_control_info`
2. `get_repo_status`
3. `refresh_repo`
4. `list_files`
5. `write_text_file`
6. `commit_and_push`
7. `read_text`
8. clean worktree verification

First real commit through the new MCP:

`f96d057ef190f2164f44e7132e4e27eb318d2123`

Commit message:

`docs(research): save SC001 B15 handoff v6.0`

Repository:

`git@github.com:AlexeyIvy/-botmarketplace-site.git`

Branch:

`main`

GitHub Control architecture:

`ChatGPT -> OpenAI Secure MCP Tunnel -> BotMarketplace GitHub Control MCP -> dedicated clean Git clone -> GitHub`

Current tunnel ID:

`tunnel_6ab41289ddd48191a3cbf6f03b774479`

GitHub Control MCP protections:

- no arbitrary shell,
- no force push,
- no workflow writes,
- dedicated deploy key,
- clean dedicated clone,
- HEAD/SHA concurrency checks,
- remote-moved check,
- write and commit/push are separate.

The Research Runner was not modified and remains offline for research jobs.

## MCP recovery documentation

Known-good infrastructure recovery documentation:

`docs/infrastructure/botmarketplace-mcp-stack-recovery-v1.0.md`

Known-good install scripts:

- `scripts/mcp/install-botmarket-github-control-v1.sh`
- `scripts/mcp/install-botmarket-github-tunnel-v1.sh`

These scripts document the final working configuration rather than the earlier failed iterations.

## Backup gates

### CHECKPOINT_BACKUP_AFTER_IDENTITY_ROUTE_V02_FREEZE

Immediately after identity/route v0.2 freeze and before price/economic research, create a portable VPS checkpoint and perform a restore verification.

### FULL_DISASTER_RECOVERY_BACKUP_AFTER_B15_STAGE

After B15, create a full recovery package.

Normal archive:

- repository and docs,
- SC001 data,
- Runner bundles/jobs/artifacts,
- MCP code/config without secret values,
- tunnel configs without secret values,
- systemd units,
- package/environment manifests,
- SHA256 manifest,
- restore script and restore verification procedure.

Secrets:

- exchange API secrets,
- private SSH keys,
- OpenAI runtime API keys

must be stored only in a separate encrypted secrets archive.

## Research discipline

Until identity/route freeze:

- no price/PnL,
- no transfer-status selection,
- no rescue tuning,
- no hidden universe/data/cost/risk/stop-rule changes,
- preserve fail-closed unresolved cases,
- keep SC001 independent from R009/R003/R010/Safe-Sleeve S002.
