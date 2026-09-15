# SC001 Current Roadmap and Stop Rules v1.3

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**

Supersedes for current SC001 execution order: `sc001-current-roadmap-and-stop-rules-v1.2.md`.

## 1. Preserved terminal decisions

- E001: terminal `FAIL`; no rescue tuning.
- E002: terminal standalone `TAKER_ECONOMICS_FAIL`; TFI preserved only as a future auxiliary/filter/ranking/execution-timing/meta-model feature.
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation, no E003 L2, no rescue tuning.
- Q2, formal Validation and Final remain closed.

SC001 remains fully independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. No SC001 result changes their rules, decisions or forward clocks.

## 2. E004 review outcome

The conceptual E004 plan v0.1 has been converted into a frozen executable protocol:

`docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

The audit rejected the former approximate 15 bps pooled-mean target as insufficiently protected. With an approximately 10 bps regular-user round-trip taker fee before spread/depth/model error, the frozen primary pooled-mean promotion hurdle is 20 bps, accompanied by trimmed-mean, median, daily breadth, concentration, side-balance, completion, turnover and latency gates.

Primary mechanism:

- 15-minute causal trade-price range;
- rolling 24-hour nearest-rank q20 compression threshold;
- false-to-true compression episode;
- fixed upper/lower band with 2 bps breakout buffer;
- 15-minute arm;
- 250 ms entry latency;
- fixed 15-minute holding horizon;
- one position maximum, 15-minute cooldown, four decisions/day maximum;
- no stop/target, no pyramiding, no overnight carry;
- no TFI or FLOW_IMPULSE in base E004.

## 3. Current gate

E004 is **FROZEN, NOT YET AUTHORIZED FOR DEV-DISCOVERY**.

The mandatory next artifact is governed by:

`docs/research/sc001-e004-implementation-preflight-spec-v1.0.md`

The implementation must run synthetic causal tests, metamorphic tests, data/hash checks and a real-data no-alpha dry run. Preflight may emit structural counts and invariants only. It may not emit prices, returns or any E004 alpha.

Only exact terminal token `PREFLIGHT_PASS` authorizes DEV-DISCOVERY.

## 4. Discovery and stop rule

After preflight PASS, run only DEV-DISCOVERY 2024-03-01..20; first eligibility follows the frozen 24-hour warm-up. Do not open March 21..30 before a complete terminal Discovery PASS.

All primary gates must pass. Any one failure produces terminal `E004_DISCOVERY_FAIL` and blocks:

- E004 Confirmation;
- E004 L2 acquisition/economics;
- Q2;
- formal Validation;
- Final;
- rescue tuning.

The eight one-factor diagnostic variants are read-only and cannot change the primary verdict or select a replacement.

## 5. Promotion order

`protocol v1.0 freeze -> implementation commit -> PREFLIGHT_PASS -> DEV-DISCOVERY -> unchanged one-time DEV-CONFIRMATION -> separately frozen L2 taker economics -> later protected temporal validation`

No stage may be skipped.

## 6. Infrastructure

Primary heavy compute remains the qualified Timeweb Cloud VPS: Ubuntu 24.04, 4 vCPU, 8 GB RAM, 80 GB NVMe, non-root `botmarket`, SSH key authentication and tmux. Android/Termux is the control client.

Never store IPs, passwords, private keys, API keys or credentials in GitHub.

## 7. Immediate next action

Implement the frozen E004 engine/config in a clean commit. Run the complete v1.0 preflight on the VPS with alpha output disabled. Do not run DEV-DISCOVERY unless the report returns exact `PREFLIGHT_PASS`.
