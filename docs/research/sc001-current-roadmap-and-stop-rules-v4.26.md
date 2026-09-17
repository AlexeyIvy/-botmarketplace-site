# SC001 Current Roadmap and Stop Rules v4.26

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — C1 SPOT METADATA PASS / BODY INTEGRITY FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.25.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 read-only postmortem remains complete.

No terminal strategy is reopened. No rescue-tuning is authorized.

## 2. C1-C6 no-alpha preflight remains PASS

The corrected C1-C6 selection preflight v0.2 remains exact:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

Protected-data firewalls remained clean and the old v0.1 FAIL remains a mechanical false-positive only.

## 3. C1 SPOT metadata preflight result

The frozen metadata-only C1 runner completed exact:

`C1_SPOT_METADATA_PREFLIGHT_PASS`

with:

- exit code `0`;
- complete SPOT assets `8/8`;
- each admitted asset `32/32` labels;
- expected body bytes `273358764`;
- disk PASS;
- all metadata query days whitelisted;
- market-data body download false;
- strategy/sentinel/basis/returns/PnL false;
- promotional alpha false.

Result record:

`docs/research/sc001-c1-selection-spot-metadata-preflight-results-v0.1.md`

Frozen local manifest identity:

- SHA256 `bfa403c5b53b2a95c0df28fd41d3382667fe0c6ced223b65f451e7b99ecd1023`;
- bytes `118273`.

## 4. Frozen body acquisition/integrity stage

Protocol:

`docs/research/sc001-c1-selection-spot-body-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c1_selection_spot_body_integrity_v0_1.py`

Implementation freeze:

`docs/research/sc001-c1-selection-spot-body-integrity-implementation-freeze-v0.1.json`

Frozen implementation identities:

- runner blob SHA `1ad980bb9da126f79c004082fbd24dd75d957c3e`;
- protocol blob SHA `1d3e4c9171f2cabbe76bb560b095e30f72b1b441`.

Exact preflight PASS token:

`C1_SPOT_BODY_PREFLIGHT_PASS`

Exact body terminal PASS token:

`C1_SPOT_BODY_INTEGRITY_PASS`

## 5. Body scope

Only the exact 256 archive identities in the frozen manifest are authorized:

- 8 SPOT assets;
- 32 labels per asset;
- labels only in `2024-06-30..2024-07-15` and `2024-08-31..2024-09-15`.

No metadata rediscovery is authorized.

The body stage must qualify exact archive identity/size, SHA256, ZIP CRC/schema/order and 240 reconstructed UTC asset-days using D + D+1 causal stitching.

Performance evidence remains only the already contaminated July/September sandbox. Boundary dates remain source-support only.

## 6. Protected periods remain closed

No access is authorized to:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 SPOT Confirmation.

## 7. Economic and sentinel rules unchanged

No candidate, feature, threshold, cost hurdle, chronology, MDE rule, execution rule, or universe changes.

Frozen first-pass C1-C6 sentinel budget remains exactly **11 variants**:

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

## 8. Current hard gate

**NO C1 SENTINEL OUTCOME BEFORE EXACT `C1_SPOT_BODY_INTEGRITY_PASS`.**

**NO C1-C6 SENTINEL OUTCOME BEFORE shared causal trade/bar utilities and synthetic/golden causality tests are complete.**

A C1 body PASS is data readiness only, not alpha evidence.

## 9. Current sequence

1. pull current GitHub state;
2. verify frozen runner/protocol Git blob identities;
3. syntax-check body runner;
4. run `preflight` and require exact `C1_SPOT_BODY_PREFLIGHT_PASS`;
5. only after exact preflight PASS, run frozen body acquisition/integrity in `tmux`;
6. require exact `C1_SPOT_BODY_INTEGRITY_PASS`;
7. implement shared causal trade/bar utilities and synthetic/golden tests;
8. implement/freeze six C1-C6 sentinel runners under unchanged 11-variant budget;
9. run nonpromotional sentinels on contaminated sandbox;
10. assign dispositions and perform MDE/block planning for survivors;
11. freeze diversified promotional research batch only after all selection dispositions are known.

Immediate next action: syntax-check and run C1 SPOT body `preflight` on VPS; body GET is authorized only if that preflight returns exact PASS.
