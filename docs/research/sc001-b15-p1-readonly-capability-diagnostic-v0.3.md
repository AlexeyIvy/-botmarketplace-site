# SC001 — B15-P1 Read-Only Capability Diagnostic v0.3

Date: 2026-09-20
Status: **DIAGNOSTIC / IPV4-ONLY AUTHENTICATED REST / NO PRICE OUTCOME**

## Purpose

Supersede v0.2 transport behavior after the VPS was observed to choose IPv6 for OKX while the exchange API-key whitelist workflow is being configured with a stable VPS IPv4.

## Transport freeze

All B15-P1 capability REST requests must resolve/connect over IPv4 only.

This is process-local to the B15 runner.

Do not modify:
- system-wide VPS routing;
- B13-C networking;
- B14-A networking.

Rationale:
- deterministic API-key whitelist source address;
- avoid dual-stack source-IP switching;
- Bybit UI currently accepted the VPS IPv4 and rejected the supplied IPv6;
- one stable authenticated REST egress family is simpler to audit.

## Security and research rules

All v0.2 redaction and no-price/no-order/no-transfer/no-withdraw rules remain binding.

PASS:
`B15_P1_READONLY_CAPABILITY_PASS`

Failure:
`B15_P1_READONLY_CAPABILITY_REVIEW`
