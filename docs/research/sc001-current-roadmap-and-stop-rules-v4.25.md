# SC001 Current Roadmap and Stop Rules v4.25

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — C1-C6 PREFLIGHT PASS / C1 SPOT METADATA PREFLIGHT NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.24.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 read-only postmortem remains complete.

No terminal strategy is reopened and no rescue-tuning is authorized.

## 2. C1-C6 selection preflight v0.2 result

The corrected no-alpha preflight has now run on the qualified VPS and returned exact:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

with:

- `PREFLIGHT_EXIT_CODE=0`;
- July E007R1 archive identities `128/128`;
- September E009 archive identities `128/128`;
- hard protected market-body hits `0`;
- legacy E003 March 22-30 source-presence count `9`;
- legacy E003 March 22-30 bodies opened/hashed by this preflight `False`;
- `strategy_signal_calculated=False`;
- `sentinel_outcome_calculated=False`;
- `pnl_calculated=False`;
- `promotional_alpha_accessed=False`.

Result record:

`docs/research/sc001-c1-c6-selection-preflight-v0.2-results-v0.1.md`

The old v0.1 FAIL remains classified as a mechanical false-positive, not a research FAIL and not a contamination event.

## 3. C1 SPOT data gap confirmed

The PASS report returned:

`C1 multi-asset spot data gap expected = True`

Therefore C1 requires contaminated-date-only same-venue SPOT data engineering before any C1 sentinel outcome.

No fresh promotional date is authorized.

## 4. Frozen C1 SPOT metadata/acquisition scope

Protocol:

`docs/research/sc001-c1-selection-spot-metadata-and-acquisition-protocol-v0.1.md`

Metadata runner:

`research/sc001/sc001_c1_selection_spot_metadata_preflight_v0_1.py`

Implementation freeze:

`docs/research/sc001-c1-selection-spot-metadata-preflight-implementation-freeze-v0.1.json`

Frozen identities:

- runner blob SHA: `e86d94086efcec078614af974c2bff64900fa665`;
- protocol blob SHA: `c760eb186d554ce33def65e835b8a63022509741`.

Exact metadata PASS token:

`C1_SPOT_METADATA_PREFLIGHT_PASS`

The metadata runner is HEAD/metadata only and is not authorized to download any market-data body.

## 5. Frozen C1 SPOT scope

Candidate SPOT instruments are exactly:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP and BCH versus USDT on OKX.

Permitted archive-label windows only:

- `2024-06-30..2024-07-15`;
- `2024-08-31..2024-09-15`.

Performance-role dates remain only:

- `2024-07-01..14`;
- `2024-09-01..14`.

Boundary/source-only labels:

- June 30;
- July 15;
- August 31;
- September 15.

Protected holdouts, July 16-30, August 1-30, October Confirmation and legacy E006 March Confirmation remain closed.

## 6. Economic and sentinel rules unchanged

No candidate definition, threshold, feature rule, cost hurdle, MDE rule, chronology or asset universe is changed.

The frozen first-pass C1-C6 sentinel budget remains exactly **11 variants**:

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

## 7. Current hard gate

**NO C1 BODY DOWNLOAD BEFORE EXACT C1 SPOT METADATA PREFLIGHT PASS AND A FROZEN DOWNLOADER/INTEGRITY IMPLEMENTATION.**

**NO C1-C6 SENTINEL OUTCOME BEFORE REQUIRED DATA ENGINEERING AND SHARED UTILITY TESTS ARE COMPLETE.**

## 8. Current sequence

1. syntax-check and run `sc001_c1_selection_spot_metadata_preflight_v0_1.py` on VPS;
2. inspect complete SPOT assets, exact expected bytes and disk feasibility;
3. only after exact metadata PASS, implement/freeze body downloader + integrity/UTC qualification for the exact manifest;
4. acquire only frozen contaminated-date SPOT bodies;
5. implement shared causal trade/bar utilities and synthetic/golden causality tests;
6. implement and freeze six C1-C6 sentinel runners under the unchanged 11-variant budget;
7. run all nonpromotional sentinels on the contaminated sandbox;
8. assign selection dispositions;
9. perform MDE/block planning for survivors;
10. freeze a diversified promotional research batch only after all selection dispositions are known.

Immediate next action: run the frozen C1 SPOT metadata-only preflight on VPS.
