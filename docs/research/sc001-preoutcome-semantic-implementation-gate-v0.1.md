# SC001 — Pre-Outcome Semantic & Implementation Gate v0.1

Date: 2026-09-19
Status: **BINDING KERNEL GATE FOR ALL FUTURE OUTCOME-BEARING SC001 RUNS**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-current-four-role-critical-review-v0.1.md`

## 1. Purpose

Prevent avoidable engineering and semantic failures from reaching an outcome-bearing run.

This gate is required before every new price/funding/return/strategy outcome stage.

## 2. Implementation handshake

Before remote run require PASS on:

- Python syntax compile;
- freeze file exists;
- runner expected freeze-status equals actual freeze-status;
- every frozen parent path resolves;
- every frozen git blob SHA matches;
- output version/path does not collide with a prior terminal result;
- frozen event/universe counts match runner constants.

Failure:

`PREOUTCOME_IMPLEMENTATION_HANDSHAKE_REVIEW`

No outcome run.

## 3. Parser fixture gate

For every external data schema used by the runner:

- accepted schema fixtures are explicitly enumerated;
- each accepted fixture parses successfully;
- at least one unknown/malformed fixture is rejected fail-closed;
- response-wrapper traversal is tested independently from one exact JSON nesting;
- optional fields cannot silently change the meaning of required fields.

Failure:

`PREOUTCOME_SCHEMA_FIXTURE_REVIEW`

## 4. Economic-identity gate

Required for cross-venue or cross-product comparisons.

Before any price ratio / basis / spread / relative return:

- asset class must match;
- full underlying identity must match;
- price economic unit must be compatible;
- quote/settlement currencies must be compatible;
- contract denomination / face-value semantics must be recorded;
- pre-market versus standard-market state must be recorded;
- the reference maturity clock must start from economically comparable standard trading;
- ticker equality alone is forbidden as proof of identity.

Failure:

`PREOUTCOME_ECONOMIC_IDENTITY_REVIEW`

## 5. Event-time gate

For scheduled/exogenous event research:

record at least two independent authoritative time fields where available.

Examples:

- API listTime;
- official announcement trading-open time.

If authoritative sources disagree materially, do not choose one by convenience.

Status:

`PREOUTCOME_EVENT_TIME_REVIEW`

until resolved.

## 6. Denomination normalization gate

Any multiplicative normalization between venue prices must be frozen before price outcome.

Allowed sources:

- official contract spec;
- official listing announcement;
- official instrument metadata with stable semantics.

Forbidden:

- infer multiplier from observed price ratio;
- choose multiplier that makes basis look reasonable.

## 7. Research-role gate

Before outcome classify evidence role:

- engineering only;
- nonpromotional Selection/Calibration;
- prospective stream;
- Confirmation.

Role must already exist in contamination registry.

No output may promote its own evidence role.

## 8. Candidate-search / multiple-testing gate

A positive Selection/sentinel outcome does not establish a strategy.

Required invariant:

`SELECTION_SURVIVE != CONFIRMATION`

If the candidate arose after multiple prior mechanism searches, later promotional evidence must be prospective or otherwise protected before design.

## 9. Operator checklist

Before giving a VPS command, the assistant must have checked:

- implementation handshake;
- source semantics;
- identity/denomination;
- contamination role;
- exact expected terminal states;
- what data fields are authorized;
- what fields remain forbidden.

## 10. Governance

This is a kernel-level control.

Future candidate protocols may be stricter, but may not weaken this gate without a versioned kernel amendment.
