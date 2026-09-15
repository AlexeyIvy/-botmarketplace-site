# SC001-E004 — Implementation Preflight Specification v1.0

Date: 2026-09-15  
Status: **FROZEN PREFLIGHT SPECIFICATION — NOT YET EXECUTED**  
Protocol: `sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

## 1. Purpose

Prove that the implementation reproduces the frozen E004 v1.0 semantics without reading or emitting E004 returns. Preflight is a non-alpha software/data audit. DEV-DISCOVERY is forbidden until a complete machine-readable report returns `PREFLIGHT_PASS`.

## 2. Output suppression firewall

Preflight may output counts, timestamps, hashes, schema checks, state-transition counts on synthetic fixtures and invariant results.

On real March data it must not output or persist:

- entry or exit prices;
- signed directions paired with future prices;
- per-trade returns;
- aggregate or daily return statistics;
- latency performance comparisons;
- any information that reveals whether E004 is profitable.

If the engine architecture cannot suppress these fields reliably, preflight FAILs.

## 3. Required code identity

Before execution record:

- repository and branch;
- full Git commit SHA;
- SHA256 of the frozen configuration file;
- Python version, OS and timezone;
- exact command;
- output directory;
- input manifest path.

Working tree must be clean or the report must hash and enumerate every modified executable/config file. Preferred result is a clean committed state.

## 4. Data checks

For every already-open March 2024 trade archive used for warm-up or Discovery:

- explicit expected filename/date mapping;
- SHA256;
- readable archive/CSV;
- required columns resolved unambiguously;
- finite positive prices;
- timestamps parse as UTC;
- min/max timestamp lie on expected UTC date;
- no timestamp outside its expected day;
- raw row count > 0;
- source-order key exists or deterministic original row index is assigned before sorting;
- sorted order is nondecreasing by `(timestamp_ms, original_sequence)`;
- duplicate timestamp and exact-row duplicate counts reported;
- no silent deduplication;
- all dates needed for 2024-03-01..20 exist.

Any missing/unqualified file is FAIL. No network acquisition is authorized by this preflight.

## 5. Synthetic causal fixtures

The test suite must use hand-built prices with analytically known outcomes and assert all of the following:

1. a trade exactly at minute boundary `t` is excluded from `[t-15m,t)`;
2. a trade one millisecond before `t` is included;
3. `H_t`, `L_t`, `M_t`, and `C_t` match hand calculations;
4. the threshold uses exactly the preceding 1,440 minute values and excludes `C_t`;
5. nearest-rank q20 selects 1-based rank 288 with no interpolation;
6. eligibility is false with 1,439 prior values and true with 1,440;
7. compression equality `C_t == Q_t` is true and its tie is counted;
8. arming occurs only on false-to-true transition;
9. a band freezes at arming and does not drift with later prices;
10. equality to `U` or `D` does not trigger;
11. strict crossing does trigger;
12. original sequence deterministically resolves same-timestamp ordering;
13. arm expiry boundary semantics match the protocol;
14. 250 ms entry uses the first trade at or after target time;
15. no trade within the 5,000 ms entry tolerance creates an incomplete episode;
16. exit horizon begins at actual entry, not decision;
17. exit uses first trade at or after 900,000 ms;
18. no exit within tolerance creates an incomplete trade;
19. UTC-day crossing is incomplete and never carried;
20. no overlap, pyramiding or reversal occurs;
21. cooldown blocks arming for exactly 15 minutes;
22. the fifth daily decision is blocked;
23. day reset clears transient state but not historical indicator warm-up;
24. LONG and SHORT gross-return sign formulas match hand calculations;
25. 500/1,000 ms variants reuse decisions and change latency only.

Every fixture must have an expected-output object checked by exact equality where possible and tight numeric tolerance only for floating-point formulas.

## 6. Metamorphic/property tests

The implementation must PASS:

- multiplying every price by a positive constant leaves compression bps, flags, decisions and gross returns unchanged within tolerance;
- adding future trades cannot change any earlier indicator, arm or decision;
- chunked/day-by-day processing equals single-stream processing exactly;
- two consecutive identical runs produce byte-identical deterministic artifacts except explicitly excluded runtime timestamps;
- diagnostic configurations cannot execute before the primary verdict file exists;
- Confirmation paths cannot be addressed while Discovery status is not the exact PASS token;
- Q2/Validation/Final paths are rejected;
- TFI/FLOW_IMPULSE fields are absent from configuration and decision code paths.

## 7. Real-data dry run without alpha

Run the parser and causal state machine on 2024-03-01..20 with return calculation and future-price export disabled.

Allowed checks:

- first eligible minute equals 2024-03-02 00:15 UTC: 15 minutes to form the first complete statistic plus 1,440 prior minute statistics;
- number of evaluated/eligible minutes;
- missing-window counts;
- compression/tie counts without values;
- arm, expiry, decision, incomplete and daily-lock counts, aggregated only;
- maximum concurrent positions;
- maximum decisions per day;
- earliest/latest decision timestamps without direction;
- invariant violations;
- memory peak and wall time.

No count may be used to retune the protocol. A surprising but valid count does not authorize parameter changes.

## 8. Artifact/schema assertions

Preflight must verify that a future authorized Discovery run will write:

- frozen config and config SHA256;
- input manifest;
- deterministic event/trade schema;
- daily metrics schema;
- aggregate metrics schema;
- run-state with explicit phase and terminal token;
- atomic writes via temporary file then rename;
- refusal to overwrite an existing completed output directory unless a new explicit directory is supplied.

Forbidden fields/files during preflight are scanned after execution. Presence of any return or price output is FAIL.

## 9. Resource and failure behavior

On the qualified Ubuntu 24.04 VPS:

- memory peak must remain below 6 GiB;
- free disk before run must exceed estimated input + output + 10 GiB;
- nonzero exit on malformed data, missing file, invariant breach or output collision;
- exceptions must identify the file/date and check without dumping credentials;
- IPs, passwords, SSH keys, API keys and credentials must never enter artifacts.

Performance alone cannot change financial semantics.

## 10. PASS gate

Preflight status is `PREFLIGHT_PASS` only if:

- all data checks PASS;
- all synthetic tests PASS;
- all metamorphic/property tests PASS;
- real-data no-alpha dry run PASSes;
- output firewall scan finds zero forbidden fields/files;
- every state invariant holds;
- resource gates PASS;
- configuration hash and code commit are recorded;
- report contains no E004 alpha.

Otherwise status is `PREFLIGHT_FAIL`; DEV-DISCOVERY remains blocked. Fixes are permitted only for implementation defects and must not alter the frozen financial protocol. After a fix, commit a new code identity and rerun the entire preflight.

## 11. Required report

Write `sc001_e004_preflight_report.json` containing at least:

- protocol version;
- status;
- code commit SHA;
- config SHA256;
- environment;
- input hashes;
- test counts and failures;
- real-data no-alpha audit counts;
- invariant results;
- forbidden-output scan;
- resource results;
- started/completed UTC timestamps.

Also write a short Markdown summary. Only the terminal status and non-alpha audit facts may be discussed before Discovery authorization.
