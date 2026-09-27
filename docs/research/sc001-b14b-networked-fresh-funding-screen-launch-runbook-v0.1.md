# SC001 — B14-B Networked Fresh Funding Screen Launch Runbook v0.1

Date: 2026-09-27
Status: **USER APPROVED REAL FUNDING-VALUE ACCESS / READY FOR VPS LAUNCH**

Approved stage:
`SC001-B14B / PERSISTENT MULTI-SETTLEMENT FUNDING CARRY / FRESH 2026 STRUCTURAL SCREEN`

User explicitly approved proceeding after offline self-test PASS.

## Exact implementation

Repository HEAD at preparation:

`7c2ba8272ffaf35bc6b0ca75ba77901d4a37b1b4`

Entrypoint:

`research/sc001/sc001_b14b_persistent_multisettlement_funding_carry_v0_1.py`

SHA256:

`cb288810ef8871ea1de3bfe9decf6e372cb525c1c62d0123969d4f7f459793f4`

Protocol SHA256:

`8b54d27166d290c53b4490aafeab400e0955cd1202235179c8d96e49cd491012`

## Fresh evidence window

`2026-07-01T00:00:00Z <= fundingTime < 2026-09-27T00:00:00Z`

Venues:
- OKX public funding history;
- Bybit public funding history.

Frozen 12 assets:
BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI.

## Frozen architecture

- 3 same-sign matched funding differentials;
- no magnitude threshold;
- signal settlement excluded from new-cycle cashflow;
- fixed 7-calendar-day hold;
- all realized venue funding cashflows inside hold counted;
- fixed direction;
- non-overlapping cycles per symbol;
- 40 bps structural burden;
- 50 bps gross-headroom hurdle.

## Execution

Run as transient systemd oneshot:

`sc001-b14b-fresh-funding-v01.service`

Working directory:

`/var/lib/botmarket-github-control/repo`

Output root:

`/home/botmarket/sc001_data/SC001_B14B_PERSISTENT_FUNDING`

Log:

`/home/botmarket/sc001_data/SC001_B14B_PERSISTENT_FUNDING/b14b_live.log`

Expected terminal classification is exactly one of:
- `B14B_PERSISTENT_CARRY_STRUCTURAL_SURVIVE`;
- `B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`;
- `B14B_DEFER_SOURCE_OR_SAMPLE`.

## Firewalls

This run MAY access realized funding histories only.

It MUST NOT access:
- price;
- basis;
- trade bodies;
- L2;
- price PnL;
- alternate horizons;
- funding magnitude threshold search;
- symbol selection.

After any terminal result, reusable-block extraction policy applies.
