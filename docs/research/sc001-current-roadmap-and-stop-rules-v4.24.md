# SC001 Current Roadmap and Stop Rules v4.24

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — C1-C6 PREFLIGHT V0.2 FROZEN / MECHANICAL RERUN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.23.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 postmortem remains complete.

No strategy is reopened.

## 2. What happened in selection preflight v0.1

The first C1-C6 no-alpha selection preflight successfully re-verified:

- July E007R1 archive identities `128/128`;
- September E009 archive identities `128/128`.

It then emitted `SC001_C1C6_SELECTION_PREFLIGHT_FAIL` only because the protected-body scanner treated pre-existing BTC perpetual archives dated `2024-03-22..30` under `SC001_E003_OKX_MARCH_TRADES` as proof of E006 Confirmation access.

That inference was a preflight implementation defect. The files belonged to the earlier E003 source inventory. The failed preflight did not calculate strategy signals, sentinel outcomes, returns or PnL.

Therefore the v0.1 FAIL is **not a research/sentinel FAIL** and does not contaminate any new promotional evidence.

## 3. Corrected frozen preflight

Protocol:

`docs/research/sc001-c1-c6-selection-preflight-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c1c6_selection_preflight_v0_2.py`

Identity freeze:

`docs/research/sc001-c1-c6-selection-preflight-implementation-freeze-v1.1.json`

Runner blob SHA:

`750bcf75ae500a9b4da7643a4e6889658ad6326c`

Protocol blob SHA:

`4b0102d82d37e138299b140a55cc2c13624499ec`

Exact PASS token remains:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

## 4. Corrected protected-body semantics

The hard firewall remains fail-closed for:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- E006 SPOT Confirmation bodies March 22-30.

However, pre-existing March 22-30 BTC perpetual archives inside the legacy E003 source root are now classified as **source presence only**, not E006 role access.

The v0.2 preflight may observe those filenames but must not open/hash those March 22-30 bodies. Optional E006 verification is limited to March 1-21.

Current contamination clarification:

`docs/research/sc001-contamination-registry-v0.5.json`

## 5. Economic and sentinel rules unchanged

This correction changes no:

- candidate definition;
- feature/indicator rule;
- sentinel threshold;
- cost hurdle;
- variant budget;
- MDE rule;
- chronology;
- asset universe.

The frozen first-pass sentinel budget remains exactly 11 variants.

## 6. Current hard gate

**NO C1-C6 SENTINEL OUTCOME BEFORE EXACT V0.2 PREFLIGHT PASS.**

A mechanical rerun of the no-alpha preflight is authorized.

## 7. After exact PASS

1. inspect C1 spot-gap state;
2. if needed, freeze contaminated-date-only SPOT acquisition for C1;
3. implement shared causal trade/bar utilities and synthetic/golden tests;
4. implement and freeze C1-C6 sentinel runners;
5. run all nonpromotional sentinels on contaminated sandbox;
6. assign selection dispositions;
7. perform MDE/block planning for survivors;
8. freeze diversified promotional research batch only after all selection dispositions are known.

Immediate next action: syntax-check and rerun `sc001_c1c6_selection_preflight_v0_2.py` on VPS.
