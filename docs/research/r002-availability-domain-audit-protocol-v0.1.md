# R002 Availability & Domain Metadata Audit Protocol v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** pre-audit freeze  
**Purpose:** quantify whether archive bars predate actual contract availability and objectively classify current USD-M contract domain metadata before any strategy rerun

---

## 1. Why this audit is required

The completed wide-universe test used the Binance public daily archive as the point-in-time availability source.

Failure decomposition found a counterexample:

- archive first date for `XAUUSDT`: 2025-12-11;
- Binance officially states XAUUSDT TradFi perpetual became available on 2026-01-05.

Therefore `first archive bar == first tradable day` is not guaranteed.

This may make the 200-observed-bar warmup begin before true contract availability for some symbols.

The audit is metadata-only and must be completed before any corrected strategy rerun.

---

## 2. Frozen metadata source

Primary source for currently resolvable USD-M contracts:

`GET https://fapi.binance.com/fapi/v1/exchangeInfo`

Official Binance Developer documentation states that this response contains symbol-level fields including:

- `symbol`;
- `contractType`;
- `onboardDate`;
- `status`;
- `baseAsset`;
- `quoteAsset`;
- `underlyingType`;
- `underlyingSubType`.

No performance data are used to classify or filter symbols.

---

## 3. Required archive comparison

Input:

`r002_binance_full_universe_daily.csv`

For each symbol matched to official exchange metadata, compute:

1. archive first date;
2. official onboard date;
3. number of archive daily rows before onboard date;
4. calendar-day difference between archive first date and onboard date;
5. archive-based 200-observed-bar eligibility date;
6. onboard-adjusted 200-observed-bar eligibility date;
7. difference between the two eligibility dates.

No strategy signal or P&L is calculated in this audit.

---

## 4. Warmup comparison rule

The corrected availability clock, if needed later, would be:

- ignore archive observations before official `onboardDate`;
- count the first calendar date containing contract trading on/after onboard date as the first observed daily bar;
- eligibility occurs on the 200th observed bar on/after onboard date.

This protocol does **not** yet authorize a strategy rerun. It only measures how different this clock is from the current archive-based clock.

---

## 5. Domain classification

Use official Binance metadata only.

Primary fields:

- `underlyingType`;
- `underlyingSubType`;
- `baseAsset`;
- `contractType`.

Do not manually classify tickers based on names.

The audit must report counts by `underlyingType` and `underlyingSubType` for all matched symbols and separately for symbols that reach 200 bars.

The purpose is to quantify how much of the later archive-defined universe is non-crypto / TradFi without creating a hindsight-selected universe.

---

## 6. Unmatched historical symbols

Current `exchangeInfo` may not contain already-delisted historical contracts.

Rules:

- mark these as `UNMATCHED_CURRENT_METADATA`;
- do not infer their domain from ticker names;
- do not exclude them from any later strategy test merely because metadata are missing;
- if historical classification becomes necessary, obtain it from official historical Binance launch/delist announcements or another frozen performance-independent metadata source.

---

## 7. Audit outputs

Required outputs:

1. `r002_availability_domain_audit.csv` — one row per archive symbol;
2. `r002_exchange_info_snapshot.json` — exact downloaded official metadata snapshot;
3. `r002_availability_domain_audit_summary.md`;
4. `r002_availability_domain_audit_state.json`.

The summary must include:

- archive symbols;
- exchangeInfo symbols;
- matched/unmatched counts;
- counts by `underlyingType`;
- number of symbols with archive bars before onboard date;
- maximum and median pre-onboard bar counts;
- number of symbols whose archive-based eligibility occurs earlier than onboard-adjusted eligibility;
- distribution of eligibility-date shifts;
- specific XAUUSDT cross-check.

---

## 8. Decision rule

### PASS — archive clock materially valid

If pre-onboard bars are rare and do not materially shift eligibility for the ever-eligible universe, retain the existing wide-universe result and continue universe-domain diagnosis.

### BUG / RERUN REQUIRED

If a meaningful number of symbols become eligible materially earlier because of pre-onboard/backfilled archive bars:

1. document the implementation bug;
2. version the engine;
3. replace archive-first availability with official onboard availability where objectively available;
4. resolve historical-symbol availability with a pre-specified source;
5. rerun the **exact same frozen SMA120 / Donchian 100/50 / passive protocol**;
6. do not change any signal parameter, cost grid, disappearance grid, warmup length, or weighting rule.

### DOMAIN MISMATCH

A non-crypto / TradFi domain slice may be considered only after objective metadata classification is complete. Any subsequent crypto-native retest must be a separately frozen universe hypothesis, not a performance-based exclusion rule.
