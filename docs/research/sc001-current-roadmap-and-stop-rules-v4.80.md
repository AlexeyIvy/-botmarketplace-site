# SC001 Current Roadmap and Stop Rules v4.80

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 DIRECTION RETENTION REJECT / READ-ONLY POSTMORTEM NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.79.md`

## 1. Binding C11 v2 Selection result

Exact terminal state:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

Binding result:

`docs/research/sc001-c11-v2-selection-stage-ab-result-v1.1.md`

## 2. What survived

Stage A:

`SURVIVE`

Observed:

- 24/24 data-valid;
- 14/24 abs residual +1s -> +60s >=20 bps;
- median abs residual ~24.11 bps;
- CPI breadth 9/12;
- Employment breadth 5/12.

Therefore residual post-decision movement remains economically material.

## 3. What failed

Stage B:

`REJECT_DIRECTION_RETENTION`

Observed:

- actionable 24/24;
- NO_TRADE 0;
- LONG 17;
- SHORT 7;
- median signed continuation ~3.63 bps;
- signed continuation >=20 bps = 6/24;
- CPI >=20 bps = 3/12;
- Employment >=20 bps = 3/12.

The first 1-second impulse sign does not capture enough of the residual movement.

## 4. Binding consequence

Do not open prospective Confirmation.

Do not build execution/PnL.

Do not rescue by changing:

- impulse window;
- sign convention;
- threshold;
- family subset;
- horizon;
- burden;
- veto features;
- entry delay.

## 5. Read-only postmortem

Protocol:

`docs/research/sc001-c11-v2-direction-retention-readonly-postmortem-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c11_v2_direction_retention_readonly_postmortem_v0_1.py`

Freeze:

`docs/research/sc001-c11-v2-direction-retention-readonly-postmortem-implementation-freeze-v0.1.json`

The postmortem reads only the existing v1.1 Selection JSON.

It may not reopen market archives or score replacement strategies.

## 6. Decision after postmortem

After read-only analysis, perform a three-role disposition review and choose one:

1. terminalize C11 as a trading-strategy candidate while retaining scheduled macro-event risk state;
2. justify a genuinely different future direction-extractor candidate under a new experiment ID and fresh evidence.

No C13+ before this disposition.

## 7. Immediate next action

Run the frozen read-only postmortem.

No market-data access is required.
