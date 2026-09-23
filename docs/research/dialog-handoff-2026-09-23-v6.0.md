# SC001 / B15-P1 — dialog handoff v6.0 — 2026-09-23

## Scope

Independent SCALPING RESEARCH / SC001, stage B15-P1 identity/route canonicalization.

Do not use price/PnL or transfer-status selection before identity/route freeze.
Do not rescue-tune closed hypotheses.
Do not silently change universe, data, cost, risk, stop rules, or canonical identity semantics.

## Current research state

- Runner: BotMarketplace Research Runner v1.0.5.
- Research jobs remain offline and hardened.
- Exact v0.1 source registries were verified by SHA256.
- Canonical patch preflight passed:
  - 100 resolved rows,
  - 9 hold rows,
  - 0 raw alias collisions.
- Canonical registry v0.2 candidate built with 85 unique aliases over 40 target network UIDs.
- Network metadata evidence synthesis produced 34 missing canonical network rows.
- Native registry candidate has 66 rows:
  - 42 base rows,
  - 24 common-proven additions.
- Ten official native hints remain metadata-only and are not admitted to native identity.
- Metadata preflight v0.1.1 passed after correcting only trailing-whitespace comparison.
- Exact CELO GoldToken and WAXP eosio.token special semantics were built and independently preflighted.
- Gravity Alpha lifecycle policy was built and independently preflighted.

Latest successful state:

`B15_P1_SPECIAL_HANDLERS_GRAVITY_POLICY_PREFLIGHT_PASS`

Next research state:

`BUILD_INTEGRATED_CANONICAL_REGISTRY_V02_REPLAY_CANDIDATE`

A sealed integrated replay candidate has already been prepared but not run:

- bundle: `bundle_20260923T165147Z_98f25758`
- SHA256: `0d21aeaa6a829ade283b6ec69d6fd41552a3832d24eaa4efb2f624abf9e39ec0`
- approval: `BM-0D21AEAA6A82`

## Replay acceptance targets

Replay the exact frozen `20260920T210446Z` Bybit/OKX identity snapshot.

Expected acceptance targets:

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

If any of these fail, freeze is prohibited.

## Special semantics carried into replay

The replay must preserve all previously evidence-backed non-default identity semantics:

- `BRC20_TICKER_NORMALIZATION`
- `CARDANO_POLICY_ASSET_ORDER_NORMALIZATION`
- `CELO_GOLDTOKEN_NATIVE_INTERFACE`
- `WAXP_EOSIO_TOKEN_NATIVE_INTERFACE`
- `ZKSYNC_ERA_ETH_SYSTEM_BASE_TOKEN`

Specialized identity kinds are preserved for provenance while common matching uses the canonical representation identity.

Important exact semantics:

- CELO:
  - identity kind: `native_erc20_interface`
  - representation: `native:CELO`
- WAXP:
  - identity kind: `native_contract_account`
  - representation: `native:WAXP`

## Gravity Alpha lifecycle gate

Historical metadata is retained for reproducibility.

- Before `2026-11-01`:
  - `REVALIDATION_REQUIRED_BEFORE_RUNTIME_ROUTE`
- On/after `2026-11-01`:
  - `ROUTE_DISABLED_DEPRECATED`

No automatic route enablement.

## GitHub Control MCP infrastructure

A dedicated read/write GitHub MCP control plane is now installed and connected independently from the research Runner.

Architecture:

`ChatGPT -> OpenAI Secure MCP Tunnel -> BotMarketplace GitHub Control MCP -> dedicated clean Git clone -> GitHub`

Repository:

`git@github.com:AlexeyIvy/-botmarketplace-site.git`

Branch:

`main`

Current control-plane protections:

- no arbitrary shell,
- no force-push,
- no GitHub Actions workflow writes,
- dedicated GitHub deploy key,
- dedicated clean clone,
- SHA/head concurrency checks,
- remote-moved check before commit,
- explicit diff capability,
- write and commit/push are separate actions.

The Research Runner remains offline and was not modified by this GitHub integration.

## Backup gates

### 1. CHECKPOINT_BACKUP_AFTER_IDENTITY_ROUTE_V02_FREEZE

Create a portable backup immediately after canonical identity/route v0.2 is frozen and before the price/economic stage.

### 2. FULL_DISASTER_RECOVERY_BACKUP_AFTER_B15_STAGE

Create a full recovery package after the B15 research stage.

Backup contents should include:

- Git repository/worktree state,
- research documentation,
- SC001 data,
- Runner bundles/jobs/artifacts,
- GitHub Control MCP code/config,
- tunnel-client profiles/config,
- /opt BotMarketplace service code,
- /etc BotMarketplace configs,
- relevant systemd units,
- environment/package manifests,
- SHA256 manifest,
- restore script,
- restore verification procedure.

Secrets/API credentials/SSH private keys must never be included in the normal backup archive in plaintext.

Store secrets only in a separate encrypted secrets archive.

A restore drill must be completed before declaring the backup valid.

## Infrastructure lessons to preserve

- External declared Runner inputs materialize under:
  `/work/run/input/<dest>`
- Immutable bundle text files live under:
  `/work/run/package/`
- Keep Runner `run_key` short; an overly long run_key caused `INVALID_ARGUMENT` before job creation.
- GitHub snapshot root exists for read-side reproducibility.
- Research jobs remain offline.
- GitHub Control uses a separate MCP service and separate OpenAI tunnel, so GitHub write access does not weaken Runner isolation.

## Resume instruction

Resume from:

`BUILD_INTEGRATED_CANONICAL_REGISTRY_V02_REPLAY_CANDIDATE`

using sealed bundle:

`bundle_20260923T165147Z_98f25758`

Do not rebuild or retune upstream identity decisions unless an independent integrity check fails.
