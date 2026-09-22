# Dialog Handoff — SC001 B15 / MCP Runner v1.0.5
Date: 2026-09-23
Repository: AlexeyIvy/-botmarketplace-site

## Scope and isolation

This handoff continues the independent research branch:

SCALPING RESEARCH / SC001

SC001 remains independent from:
- R009
- R003
- R010
- Safe-Sleeve S002

Do not change their frozen rules, forward clocks, decisions, or use B15 outcomes to retroactively retune them.

## Active B15 stage

Current stage:
SC001-B15-P1 / NONPRICE IDENTITY INVENTORY

Confirmed prior run:
- run_id: 20260920T210446Z
- status: B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS
- next_state: NETWORK_ALIAS_AND_NATIVE_IDENTITY_REVIEW
- maturity_days: 90

Prior run_manifest values to preserve as reference and re-check from canonical artifacts before relying on them:
- Bybit spot USDT rows: 395
- OKX spot USDT rows: 406
- Bybit primary market bases: 369
- OKX primary market bases: 303
- common primary base candidates: 201
- Bybit chain identity rows: 300
- OKX chain identity rows: 265
- Bybit new-listing rows collected: 681
- Bybit delisting rows collected: 59

Safety flags from the run:
- order_endpoints_called: false
- price_endpoints_called: false
- transfer_endpoints_called: false
- withdraw_endpoints_called: false
- secret_values_printed: false
- Bybit credential mode: readOnly
- OKX credential mode: read_only

## Canonical safe export on VPS

Canonical safe export:
docs/research/artifacts/b15-p1-canonical-freeze/20260920T210446Z/

Expected files:
- ADMITTED.json
- EXCLUDED.json
- IDENTITY_REVIEW.json
- SAFE_REVIEW_EXPORT.json
- directed_route_graph.json
- final_builder_manifest.json
- usdt_quote_rebalance_graph.json

Previously reported builder counts, not yet revalidated in this dialog:
- ADMITTED: ~146
- IDENTITY_REVIEW: ~46
- EXCLUDED: ~9
- directed routes: ~310
- USDT rebalance routes: ~9

Rule: re-read and confirm exact counts from canonical export before accepting these numbers.

## Infrastructure state

BotMarketplace Research Runner:
- version: 1.0.5
- mode: offline-research-v1
- arbitrary_shell: false
- network_for_jobs: false
- Python: 3.12.3
- numpy: 1.26.4

Production MCP:
http://127.0.0.1:8767/mcp

Legacy local probe:
127.0.0.1:8766

Available input roots:
- research_docs
- sc001_data

Verified execution chain:
ChatGPT → MCP → Secure Tunnel → VPS → systemd sandbox → artifact → ChatGPT

Verified isolation:
- research job runs as root: NO
- uid: botmarket-job (992)
- gid: botmarket-job (984)
- supplementary groups: only 984
- Linux capabilities: 0
- external network: blocked
- arbitrary shell: NO
- package: read-only
- state: inaccessible/read-only
- logs: inaccessible/read-only
- output: writable
- runner-tunnel.env: PermissionError
- staging/requests/index/runs: PermissionError
- package integrity verification: PASS
- trusted finalizer: PASS
- artifact reading via MCP: PASS

Verified jobs:
- production control: job_20260922T210624Z_a23a45b0 — COMPLETED, exit_code 0, package_integrity_ok true
- corrected isolation diagnostic: job_20260922T212328Z_2bbcd679 — COMPLETED, exit_code 0, stderr empty

## MCP Runner workflow

Normal workflow:
1. Agree the research step.
2. Prepare code.
3. Create bundle.
4. Upload files with put_text_file.
5. Seal bundle and obtain immutable SHA256 + approval code.
6. User explicitly approves the sealed candidate.
7. Run bundle.
8. Wait for completion.
9. Read stdout/stderr/artifacts.
10. Review the result.

Technical auto-fix permission, when explicitly granted by the user with wording such as
"Запускай с автоматическим исправлением технических ошибок до 3 попыток",
allows only technical diagnosis/code execution repair and new bundle versions for up to 3 attempts.

It does NOT authorize:
- changing the research hypothesis
- changing universe
- changing data
- changing cost/risk model
- changing stop-rules
- changing test meaning
- rescue-tuning after a negative financial result

## Current GitHub connector status

In this dialog GitHub write access is working.
Repository permissions observed: admin/maintain/pull/push/triage = true.

This handoff file itself is the write-access verification.

## Next research step

Continue B15 from:
NETWORK_ALIAS_AND_NATIVE_IDENTITY_REVIEW

Required order:
1. Re-read the canonical safe export on VPS through the Runner path.
2. Confirm exact counts for ADMITTED / IDENTITY_REVIEW / EXCLUDED and route counts.
3. Inspect all IDENTITY_REVIEW cases.
4. Classify:
   - network aliases
   - native identity
   - contract/address identity where applicable
   - ambiguous chain naming
   - false-positive listing metadata if any
5. Do not auto-admit ambiguous cases.
6. Complete canonical universe/route freeze only after identity review is closed.
7. Do not advance to price/PnL work before identity/route freeze is complete.

## Research discipline

- No price/PnL work before identity/route freeze.
- No rescue tuning.
- No hidden changes to universe, data, costs, risk, or stop-rules.
- Preserve fail-closed handling for ambiguous identity cases.
- Use Runner/Reader path rather than manual Termux execution.
