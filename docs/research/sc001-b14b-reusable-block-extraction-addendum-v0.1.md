# SC001 — B14-B Reusable-Block Extraction Addendum v0.1

Date: 2026-09-27
Status: **POSTMORTEM REUSABLE-BLOCK EXTRACTION COMPLETE**

Parent:

`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`

Retain:

`RB022 — Persistent cross-venue funding-differential direction state v0.1`

Reason:
- 60.91% of frozen cycles were positive;
- 8 symbols had positive median carry;
- 3 represented months had positive median carry.

Do not retain as standalone carry alpha:
- median gross carry only +1.3863 bps;
- p75 only +3.6405 bps;
- four-fill structural burden 40 bps;
- gross headroom hurdle 50 bps.

Future use is limited to prospectively frozen R2/R3/R4/R6 roles under a new mechanism.
