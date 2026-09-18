# SC001 Current Roadmap and Stop Rules v4.39

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9 OCTOBER FUNDING INCIDENT RECORDED / D1 v0.3 EXACT-SEPTEMBER REPAIR FROZEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.38.md`

## 1. Binding terminal states

All prior terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9 still has no strategy verdict.

## 2. C9-D1 v0.2 incident

The D1 v0.2 runner downloaded and opened both September and October historical funding ZIPs for the eight frozen C9 assets before applying timestamp bounds.

Binding incident record:

`docs/research/sc001-c9-d1-v0.2-october-funding-body-access-incident-v0.1.md`

This is a contamination/evidence-chronology incident, not a C9 strategy result.

## 3. Contamination consequence

Current registry:

`docs/research/sc001-contamination-registry-v0.8.json`

For any future C9 implementation using funding state:

- September 2024 funding remains nonpromotional Selection/Calibration;
- October 2024 funding is also nonpromotional because its body was opened by v0.2;
- October 2024 funding can no longer serve as clean C9 Confirmation evidence.

The incident does not imply access to October trade, SPOT, L2, mark or index bodies.

Those channels remain separately governed.

## 4. Audit-artifact rule

Do not delete locally downloaded October funding ZIPs.

Retain them as audit artifacts.

Local presence is not authorization for future use.

Repaired code must never enumerate/open/hash those October bodies.

## 5. C9-D1 v0.3 repair

Protocol:

`docs/research/sc001-c9-d1-september-funding-archive-integrity-protocol-v0.3.md`

Runner:

`research/sc001/sc001_c9_d1_v03_exact_september_funding_integrity.py`

Freeze:

`docs/research/sc001-c9-d1-v0.3-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `00cd89fe69862e8e47c509feb67f8205ec5a4322`;
- runner: `57da4b3f81a86e46e1887bad40d638158be3fe11`;
- contamination registry: `f4ba14c247fbdd357935fa1563f421b89afe3edc`.

## 6. Exact-file rule

For each instrument v0.3 may access only:

`INST-fundingrates-2024-09.zip`

Metadata entries for any other month are ignored.

v0.3 must not:

- HEAD October funding archive;
- download October funding archive;
- hash October funding archive;
- open October ZIP;
- parse October funding CSV.

## 7. September reuse

Previously downloaded September ZIPs may be reused only after:

- exact September filename match;
- D0 Content-Length match;
- current official metadata match;
- current HEAD size match;
- local byte-size match;
- SHA256 recomputation;
- ZIP CRC and CSV validation.

## 8. Exact timestamp rule

Rows from the exact September ZIP must satisfy:

`2024-08-31T16:00:00Z <= funding_time <= 2024-09-30T16:00:00Z`

Any timestamp outside that range is REVIEW.

## 9. Exact D1 v0.3 terminal states

PASS:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS`

REVIEW:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

REVIEW remains implementation/data state only.

## 10. Accurate reporting requirement

v0.3 must report:

- October funding body accessed by v0.3 = false;
- prior October funding contamination known = true;
- October funding clean C9 Confirmation eligible = false.

It must not claim October funding has never been accessed.

## 11. Immediate next action

Run frozen C9-D1 v0.3 exact-September integrity stage on VPS.

Only after exact PASS may a C9 state-transition sentinel be designed prospectively.
