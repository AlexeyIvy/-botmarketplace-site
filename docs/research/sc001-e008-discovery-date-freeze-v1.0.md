# SC001-E008 — Discovery / Confirmation Date Freeze v1.0

Date: 2026-09-16  
Status: **FROZEN BEFORE E008 PROMOTIONAL L2 BODY ACCESS**

## 1. Purpose

Freeze untouched Q1 date sets without using maker outcomes, spread statistics, fill counts or P&L.

Excluded as contaminated engineering/research dates:
- 2024-01-05
- 2024-01-14
- 2024-01-31
- 2024-02-12
- 2024-02-13

March is excluded from the primary E008 holdout design because March 2024 trade tapes were already used heavily in SC001 E003-E007 alpha work.

## 2. Deterministic selection rule

Discovery uses eight fixed calendar bins across Jan-Feb 2024. Within each bin, after removing contaminated dates, select the date with lexicographically smallest SHA256 of:

`SC001-E008-DISCOVERY-v1|YYYY-MM-DD`

Bins:
1. Jan 01-07
2. Jan 08-14
3. Jan 15-21
4. Jan 22-31
5. Feb 01-07
6. Feb 08-14
7. Feb 15-21
8. Feb 22-29

Frozen Discovery dates:
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

Confirmation uses four broader bins on dates not already selected or contaminated. Within each bin select the smallest SHA256 of:

`SC001-E008-CONFIRMATION-v1|YYYY-MM-DD`

Bins:
1. Jan 01-15
2. Jan 16-31
3. Feb 01-14
4. Feb 15-29

Frozen Confirmation dates:
- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

## 3. Firewalls

- No promotional L2 body for these dates was opened to choose the dates.
- Discovery dates may be metadata/HEAD-qualified next.
- Confirmation bodies remain unopened unless Discovery later passes the fully frozen protocol.
- No replacement date may be substituted because performance looks better.
- If a frozen date is objectively unavailable/corrupt, the whole stage returns REVIEW and a new protocol version must be frozen before any replacement.
- Q2 / formal Validation / Final remain closed.
