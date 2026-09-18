# SC001 Current Roadmap and Stop Rules v4.28

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — GOLDEN PASS / C1-C6 SENTINEL IMPLEMENTATION FROZEN / MASTER PREFLIGHT NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.27.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 read-only postmortem remains complete.

No terminal strategy is reopened. No rescue-tuning is authorized.

## 2. C1 SPOT data engineering remains PASS

The frozen C1 SPOT body stage remains exact:

`C1_SPOT_BODY_INTEGRITY_PASS`

with:

- 256/256 archive files qualified;
- 240/240 reconstructed UTC asset-days;
- 224 contaminated performance asset-days;
- 16 boundary warm-up asset-days;
- no strategy/sentinel/basis/returns/PnL calculation.

Result record:

`docs/research/sc001-c1-selection-spot-body-integrity-results-v0.1.md`

## 3. Shared causal utilities golden result

The frozen synthetic/golden suite completed exact:

`SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS`

with:

- `checks_passed = 11`;
- exit code `0`;
- no market-data body required;
- no sentinel outcome/PnL;
- no protected data;
- no promotional alpha.

Result record:

`docs/research/sc001-selection-causal-utils-golden-results-v0.1.md`

## 4. C1-C6 sentinel implementation is now frozen

Executable protocol:

`docs/research/sc001-c1-c6-sentinel-executable-protocol-v0.1.md`

Run manifest:

`docs/research/sc001-c1-c6-sentinel-run-manifest-v0.1.json`

Implementation freeze:

`docs/research/sc001-c1-c6-sentinel-implementation-freeze-v0.1.json`

Common helper:

`research/sc001/sc001_selection_sentinel_common_v0_1.py`

Master implementation preflight:

`research/sc001/sc001_c1c6_sentinel_implementation_preflight_v0_1.py`

Candidate runners:

- `sc001_c1_sentinel_v0_1.py`;
- `sc001_c2_sentinel_v0_1.py`;
- `sc001_c3_sentinel_v0_1.py`;
- `sc001_c4_sentinel_v0_1.py`;
- `sc001_c5_sentinel_v0_1.py`;
- `sc001_c6_sentinel_v0_1.py`.

## 5. Frozen implementation identities

- parent sentinel/MDE plan: `6f5a76ad727990f63bfa096c442172e2b0108fa1`;
- selection ledger: `28849bd591b740fa9a519339bf9bf90681d0582a`;
- executable protocol: `9fd9dd9722f95c895a89e4bd6edcf6aae6e20f9a`;
- run manifest: `2ff476ea9434060a1b4e7d3f93ab2ca335cdd845`;
- common helper: `427d900ea0e0722c325fdef627d548b66d14da67`;
- causal utilities: `a7953274e5e47c7dd1280b20c16d479ca90badc4`;
- master preflight: `c8a0a9ebef87dfe6dbe47748bf238bfcc23af77d`;
- C1 runner: `4ea35dcab0b6f8098c91ab031045686b76038f5d`;
- C2 runner: `69996686255490c92470ea9482eb47fbf0b136f5`;
- C3 runner: `1db653eff22156142e89d32fca857c1b2bb39680`;
- C4 runner: `fdd3ff742bee97047bdfaa7d7cc5d4947ca51ef1`;
- C5 runner: `bba126b7357f0ed03bb93c4aba815910e710ecc8`;
- C6 runner: `6479502e7e11b78021bd7806a9621d4070d6bc78`.

## 6. Sentinel budget remains unchanged

Frozen first-pass count remains exactly **11 variants**:

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

No new threshold, horizon, indicator/filter, asset subset, time-of-day filter, event-day selection, or custom composite may be added after outcomes.

## 7. Important engineering corrections before freeze

Before the implementation freeze, code review corrected only causal/time-boundary mechanics, before any sentinel outcome existed:

- completed-bar performance-day boundary handling in C2/C3/C5;
- C6 exact 15-minute decision boundary start;
- C4 strict Z-crossing previous-state calculation at day boundaries, using causal prior history without carrying state across the July-to-September gap;
- stronger fail-closed parent protected/alpha firewalls;
- exact cross-check between parent ledger and run-manifest candidate counts.

These are pre-outcome implementation corrections, not rescue-tuning and not contamination events.

## 8. Current hard gate

**NO C1-C6 SENTINEL `run` BEFORE EXACT:**

`SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS`

The master preflight must:

1. verify exact frozen Git blob identities;
2. verify parent qualified reports and firewalls;
3. verify golden PASS;
4. verify ledger/run-manifest exact total 11 and per-candidate counts 1/2/2/4/1/1;
5. verify that no terminal sentinel report already exists;
6. execute all six candidate `preflight` modes and require all six exact PASS tokens;
7. calculate no sentinel outcome.

## 9. Protected periods remain closed

No access is authorized to:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 SPOT Confirmation.

## 10. Current sequence

1. pull current GitHub state;
2. syntax-check shared helper, master preflight and all six sentinel runners;
3. verify frozen identities;
4. run master implementation preflight only;
5. require exact `SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS`;
6. only after PASS authorize a frozen all-six nonpromotional sentinel run;
7. run all six C1-C6 sentinels on the contaminated sandbox without between-result adaptation;
8. assign selection dispositions only after all six results are known;
9. perform MDE/block planning for survivors;
10. freeze a diversified promotional research batch only after all dispositions are known.

Immediate next action: syntax-check and run the frozen C1-C6 master implementation preflight on VPS. Do not run any candidate `run` mode yet.
