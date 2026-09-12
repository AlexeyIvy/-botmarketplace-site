# SC001-DATA-Q006 Implementation Freeze v0.1

Status: **FROZEN BEFORE Q006 RUN**

Protocol: `docs/research/sc001-data-q006-okx-trades-acquisition-protocol-v0.1.md`

Pinned engine commit:
`64897957fcae86ece5e8385080e1e2469e447903`

Pinned launcher commit:
`6ae144223df87c5d859495f0990b47d52510ca35`

Frozen boundaries:
- exactly five Q005R-qualified 2024-Q1 OKX trade archives;
- expected compressed total 30,080,404 bytes;
- data/schema qualification only;
- no E002 TFI, response labels, Spearman/deciles or P&L;
- no 2024-Q2 OKX acquisition;
- no formal Validation or Final.

Any parser repair required after archive schema inspection must be versioned separately and may not inspect strategy output while engineering the repair.
