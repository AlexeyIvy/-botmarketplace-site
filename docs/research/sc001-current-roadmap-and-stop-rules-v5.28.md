# SC001 Current Roadmap and Stop Rules v5.28

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B15-P1 SOURCE FEASIBILITY PASS / READ-ONLY CREDENTIAL PREFLIGHT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.27.md`

## 1. Background branches

B13-C and B14-A remain protected under systemd.

No rule changes.

## 2. B15 lead

`B15-P1_TRANSFERABILITY_SHOCK_CAPITAL_SEGMENTATION`

No candidate ID.

No price outcome.

## 3. Source/access audit

Binding:

`docs/research/sc001-b15-p1-transferability-shock-source-access-semantic-feasibility-audit-v0.1.md`

Verdict:

`B15_P1_SOURCE_FEASIBILITY_PASS_AUTH_READ_ONLY_REQUIRED`

## 4. Preferred source pair

- OKX;
- Bybit.

Both provide chain-level deposit/withdraw status metadata through authenticated APIs.

## 5. Security contract

Binding:

`docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md`

Only dedicated read-only keys may be used.

Secrets stay off Git and out of chat/logs.

## 6. Next hard gate

`LIVE_READ_ONLY_CREDENTIAL_CAPABILITY_PREFLIGHT`

Need to prove:

- OKX Read-only credential can call currencies endpoint;
- Bybit read-only credential can call coin-info endpoint;
- response schemas include required chain/state fields;
- correct regional API domains are resolved;
- no Trade/Withdraw permissions are granted.

## 7. Before credential PASS

Forbidden:

- B15 price feed;
- cross-venue spread/basis calculation;
- threshold selection;
- asset winner selection;
- PnL.

## 8. After credential PASS

Freeze and implement the prospective status collector:

- 30-second cadence;
- append-only snapshots;
- explicit state transitions;
- causal transition intervals;
- fail-closed network identity mapping.

No price analysis until at least one clean status-event path is available and Edge-to-Fill is frozen.
