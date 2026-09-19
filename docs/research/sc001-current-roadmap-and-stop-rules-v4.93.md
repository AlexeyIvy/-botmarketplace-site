# SC001 Current Roadmap and Stop Rules v4.93

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-B PROSPECTIVE ADMISSION FROZEN / HISTORICAL BRANCH CLOSED**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.92.md`

## 1. Binding states

C11:
`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:
`C12_S0_REJECT_PARITY_REVERSION`

B13-A:
`B13A_REJECT_STRUCTURAL`

B13-B historical S0:
`B13B_S0_DEFER_SAMPLE`

B13-B remains:
`B13-B_NOT_YET_C13`

## 2. Historical B13-B is closed

Raw S0 runner output is preserved but not binding.

Two of seven historical pairs were ticker collisions:

- BB equity vs BounceBit crypto;
- QNT equity vs Quant crypto.

No historical replacement/convergence is authorized.

## 3. Prospective path

Binding protocol:

`docs/research/sc001-b13b-prospective-launch-event-admission-protocol-v0.1.md`

Future event admission now requires:

- exact underlying identity;
- asset class;
- full name/project/company;
- price denomination compatibility;
- >=90-day mature Bybit reference;
- metadata-only source availability.

Ticker match alone is forbidden.

## 4. Current B13-B state

No price-bearing action is currently due.

Future qualifying launch events may be appended prospectively under the frozen admission protocol.

## 5. Parallel research

Because B13-B now depends on future events, SC001 may continue independent-base source/design work in parallel.

Preferred next parallel task:

`B13-C explicit liquidation-flow data-feasibility audit`

or, if no qualified free historical liquidation source exists, return to a new independent-base pool.

## 6. Hard boundaries

Do not use future B13-B prospective admissions to alter:

- historical S0 rules;
- 50 bps threshold;
- 40 bps structural burden;
- identity semantics.

No C13 assignment yet.

## 7. Immediate next action

Perform B13-C source/data-feasibility audit only.

No B13-C alpha/outcome run is authorized.
