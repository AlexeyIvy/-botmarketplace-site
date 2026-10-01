# SC001 — Implementation Debugging & Repair Control v0.1

Date: 2026-10-01
Status: BINDING ENGINEERING CONTROL / NO RESEARCH OUTCOME AUTHORIZATION
Scope: BotMarketplace / SCALPING RESEARCH / SC001

Parents:
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.2.md
- docs/research/sc001-delegated-user-authorization-policy-v0.1.md (proposal lineage only until superseded/ratified)

## 1. Purpose

Prevent iterative line-by-line debugging loops that:
- consume execution budgets without increasing understanding;
- fix only the first surfaced exception while leaving adjacent defects;
- drift away from the frozen research protocol;
- weaken tests to make code pass;
- cause repeated network/outcome runs for software debugging;
- lose the original economic/research intent.

The objective is:
ROOT-CAUSE QUALITY / REPAIR CYCLE
not patches per hour.

## 2. Applicability

This control applies whenever an SC001 worker creates or modifies executable research/data code after a failed:
- compile/import check;
- synthetic/unit/property test;
- offline preflight;
- data-engineering validation;
- metadata/source preflight;
- task-local implementation handshake.

Automatic repair is allowed only when the task explicitly contains:
REPAIR_MODE = AUTO_PRE_OUTCOME

Otherwise:
REPAIR_MODE = NONE

## 3. Hard research firewall

Automatic repair is eligible only when all are true:
- outcome_accessed = false;
- protected_evidence_accessed = false;
- no strategy-performance metric was observed;
- no frozen financial/economic rule changes;
- no threshold/horizon/symbol/universe/evidence-role change;
- no new source selected after failure;
- no collector mutation;
- no paid/credentialed/trading action.

If any condition is false or uncertain:
REPAIR_ESCALATE_STRATEGY
and no automatic patch/re-run.

## 4. Failure classification before editing

Before changing code, classify the failure exactly once into one primary class.

AUTO-REPAIR ELIGIBLE classes:
- SYNTAX_IMPORT_DEFECT
- TASK_LOCAL_PATH_OR_VERSION_POINTER_DEFECT
- CLI_OR_OUTPUT_CONTRACT_DEFECT
- SYNTHETIC_FIXTURE_OR_TEST_HARNESS_DEFECT
- TASK_LOCAL_STATE_MACHINE_IMPLEMENTATION_DEFECT_AGAINST_ALREADY_FROZEN_RULE
- TASK_LOCAL_ENVIRONMENT_CONFIGURATION_DEFECT
- DETERMINISTIC_SERIALIZATION_OR_PARSING_IMPLEMENTATION_DEFECT where source semantics are already frozen and unchanged

NOT AUTO-REPAIR ELIGIBLE:
- SOURCE_SCHEMA_OR_SEMANTIC_DRIFT
- PROTOCOL_AMBIGUITY
- DATA_AVAILABILITY_OR_COVERAGE_CHANGE
- RESOURCE_OR_RATE_LIMIT_FAILURE
- NEW_DEPENDENCY_WITH_NUMERICAL_BEHAVIOR_CHANGE
- SHARED_COMMON_LIBRARY_SEMANTIC_CHANGE
- AUTHORIZATION_OR_PERMISSION_FAILURE
- PROTECTED_EVIDENCE_INCIDENT
- OUTCOME_RUN_FAILURE_AFTER_PROTECTED_ACCESS
- UNKNOWN_ROOT_CAUSE

Non-eligible failures stop the repair loop.

## 5. Diagnosis-first gate

No code edit is allowed immediately after an exception.

First create a compact REPAIR_DIAGNOSTIC containing:
- exact failure signature;
- full traceback / failing assertion identity;
- first failing invariant;
- last known-good stage;
- affected code path;
- affected input/output contract;
- whether the failing behavior can be reproduced offline/synthetically;
- primary root-cause hypothesis;
- confidence: HIGH / MEDIUM / LOW;
- adjacent-risk list;
- explicit statement that frozen research semantics remain unchanged.

If confidence is LOW:
stop and return REPAIR_ESCALATE_STRATEGY.

## 6. Mandatory adjacent-defect sweep

Before the first patch, review the full local implementation surface relevant to the failure.

At minimum:
- all call sites of the failing function/interface;
- imports and dependency versions;
- CLI argument construction;
- path/version/schema constants;
- source identity assumptions;
- state-machine transitions touching the failing state;
- error/cleanup paths;
- output schema and collision behavior;
- stale references to superseded artifact versions;
- test fixtures that exercise the same contract;
- neighboring boundary conditions likely to fail immediately after the first defect is removed.

Use repository search/static inspection to find repeated instances of the same defect pattern.

The worker must produce one:
COHERENT_REPAIR_SET
covering all mechanically justified adjacent defects found by this sweep.

Do not patch one line, rerun, and only then inspect the next line unless the next failure was genuinely not statically discoverable.

## 7. Repair budget

Default automatic budget per implementation task:

INITIAL_FAILURE_RUN = already consumed
MAX_REPAIR_CYCLES = 2
MAX_CHANGED_TASK_LOCAL_FILES = 4

A repair cycle is consumed only when materially changed executable/test code is actually run after a failure.

Static review, repository search, diff review and documentation do not consume a cycle.

Task may set a lower budget.
Task may not set a higher automatic budget without Strategy Manager authorization under an active delegated-user policy.

## 8. Loop breakers

Immediate STOP conditions:

### SAME FAILURE SIGNATURE
If the same normalized failure signature recurs after a repair:
REPAIR_LOOP_SAME_SIGNATURE_STOP

Do not spend the second repair cycle on another local tweak unless the first run is proven to have executed stale code rather than the repaired identity.

### SECOND DISTINCT FAILURE
If cycle 1 exposes a different failure:
- re-run diagnosis-first gate;
- allow cycle 2 only if it is independently AUTO-REPAIR ELIGIBLE and was not reasonably detectable in the prior adjacent-defect sweep.

Otherwise:
REPAIR_BUDGET_STOP_REVIEW

### THIRD CODE IDENTITY
No third automatic repair cycle.
Return:
REPAIR_BUDGET_EXHAUSTED

### SCOPE DRIFT
If a fix would require changing:
- frozen formula;
- test expectation derived from frozen formula;
- source semantics;
- evidence role;
- parameter/horizon/symbol budget;
- common shared library semantics;
stop immediately.

## 9. Tests may not be weakened

After a failure, a worker must not:
- delete the failing test;
- relax an assertion;
- widen tolerance;
- skip a case;
- change expected output;
- reduce sample/schema checks

merely to obtain PASS.

A test may be changed automatically only when the diagnosis proves:
TEST_HARNESS_DEFECT
and the frozen protocol/contract independently determines the correct expectation.

The repair report must show why production semantics, not desired PASS status, determine the new test.

## 10. Required validation ladder after each patch

Run from cheapest to most complete:

1. STATIC/SYNTAX
   - language parser/compile check for all touched files;
   - import/module load where safe;
   - task contract/hash/path validation.

2. TARGETED REGRESSION
   - deterministic fixture that reproduced the original failure;
   - at least one negative/boundary case around the repaired behavior.

3. ADJACENT TEST SET
   - all task-local synthetic/unit/property/metamorphic checks relevant to the touched surface.

4. FULL PREFLIGHT
   - rerun the entire frozen implementation preflight from a clean output path;
   - never rerun only the previously failing assertion as the acceptance criterion.

5. OUTPUT FIREWALL
   - confirm no forbidden price/return/PnL/protected outcome fields or files were emitted.

6. IDENTITY
   - record new code/implementation hashes;
   - invalidate stale prior implementation authorization;
   - re-freeze the exact passing implementation identity before any later data/outcome stage.

A target test PASS without full preflight PASS is not a repaired implementation.

## 11. Adversarial diff review before acceptance

After full preflight PASS, perform a separate read-only review of the final diff from the frozen protocol outward, not from the error message inward.

Ask:
- Did this change only implementation semantics?
- Did any constant/threshold/horizon/sign/universe/source change?
- Did error handling hide a failure?
- Did the patch reduce checks?
- Did the patch add a silent fallback?
- Did a new dependency or default alter behavior?
- Are all touched paths covered by tests?
- Could the same failure pattern exist elsewhere?

If any answer is uncertain:
REPAIR_REVIEW_REQUIRED.

## 12. Branch / PR rule for repairs

Every executable-code repair uses:
sc001/<worker-id>/<task-id>-repair

No direct repair commit to main.

Automatic merge is eligible only if ALL are true:
- active delegated-user authorization permits AUTO_PRE_OUTCOME repair;
- repair is task-local;
- no shared/common library changed;
- no binding research/control document changed;
- repair budget not exhausted;
- full validation ladder PASS;
- adversarial diff review PASS;
- outcome_accessed=false;
- protected_evidence_accessed=false;
- PR head SHA matches the validated code identity.

Merge with expected head SHA.

Any mismatch or shared-code change:
STRATEGY_MANAGER_REVIEW_REQUIRED
before merge.

## 13. Outcome-stage failure boundary

Once an OUTCOME_BEARING process has opened protected evidence or emitted/read any outcome-bearing value:
- automatic implementation repair is disabled;
- do not rerun same evidence after patch;
- preserve failed output/logs;
- create a technical incident result;
- return to Strategy Manager.

A failure in an outcome-capable runner may remain repair-eligible only if a machine-verifiable firewall proves:
- protected_evidence_accessed=false;
- outcome_accessed=false;
- failure occurred before data-body/outcome path access.

Uncertainty means STOP.

## 14. Network use for debugging

Do not use repeated public_research runs as a debugger.

Preferred order:
synthetic/offline reproduction -> full offline preflight -> at most one already-authorized same-contract network smoke.

A network failure must not trigger code edits unless diagnosis proves a task-local implementation defect rather than source/rate/environment behavior.

## 15. Completion artifact

Every repaired implementation must record:
- original failure signature;
- failure class;
- root-cause hypothesis;
- adjacent-defect sweep summary;
- repair cycles consumed;
- files changed;
- old/new hashes;
- validation ladder results;
- whether tests changed and why;
- full preflight terminal token;
- outcome_accessed=false;
- protected_evidence_accessed=false;
- remaining known risks.

## 16. Delegation intent

The user may delegate routine pre-outcome implementation repair so workers do not ask for permission on every code edit.

Delegation means:
permission to diagnose and repair within this contract.

It does NOT mean:
permission to keep trying until something passes.

The default automatic debugging budget is intentionally small.

## 17. No architectural agent added

No separate debugging agent is required.

The same execution worker performs:
diagnosis pass -> repair pass -> adversarial diff-review pass

as three distinct phases.

If repeated real use shows workers cannot reliably self-review repairs, a separate code-review agent may be reconsidered later.
