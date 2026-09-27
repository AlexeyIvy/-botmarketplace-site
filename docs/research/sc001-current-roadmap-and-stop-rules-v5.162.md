# SC001 Current Roadmap and Stop Rules v5.162

Date: 2026-09-27
Status: **B15-P2 V0.1.2 HOST PREFLIGHT SCHEMA-DRIFT FIXED / V0.1.3 NETWORKED BOUNDARY FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.161.md`

## V0.1.2 attempt

The approved v0.1.2 wrapper stopped before any network call with:

`AssertionError: external_reference_price_access`

This was a wrapper contract bug, not a source/API/research result.

The self-test result does not define that field. The corresponding firewall is canonically stored in the implementation freeze as:

`external_reference_access_authorized=false`

Canonical diagnostic:

`docs/research/sc001-b15p2-networked-source-census-v012-preflight-failure-diagnostic-v0.1.json`

## V0.1.3 correction

Research implementation remains byte-identical:

`7da36641ed71e0195320f0cc7cc389d629d4f843a646f64c41c1739fc0cd6b35`

Only the host wrapper changes.

New wrapper:

`scripts/research/run-b15p2-bybit-delisting-source-census-v0.1.3.sh`

SHA256:

`dcc5899575ac614d64de2960605cb0887c0598d5a70c7c28d37e19dc6dd25016`

The v0.1.3 wrapper:

- validates self-test fields only from the self-test result schema;
- validates external-reference and outcome-ranking firewalls from implementation freeze;
- uses named `PRECHECK_FAILED:<code>` diagnostics instead of opaque assertions;
- adds explicit `--preflight` mode that performs no network calls;
- has been cross-checked against the current canonical self-test result and implementation freeze;
- retains PASS / DEFER / REVIEW handling;
- retains persistent logs/exit/marker;
- retains the 900-second runtime bound.

Cross-document preflight simulation:

`PASS`

## Approval boundary

Launch contract:

`docs/research/sc001-b15p2-networked-bybit-source-only-event-census-launch-contract-v0.1.3.json`

Approval code:

`BM-DCC5899575AC`

Network execution remains unauthorized until fresh explicit approval.

## Research strategy

No market/source-feasibility outcome was observed in the v0.1.2 attempt.

No strategy review is triggered.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_NETWORKED_V013_BM-DCC5899575AC`
