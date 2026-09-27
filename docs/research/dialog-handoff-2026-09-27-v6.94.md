# SC001 parallel research — dialog handoff v6.94 — 2026-09-27

Current:
- B15-P1 W1 accumulation continues.
- B14-A Sep25 P0 remains DEFER_DATA.
- B13-C S0 is terminal REJECT, but reusable block RB021 is retained.
- mandatory reusable-block extraction policy is now binding.
- B14-B is the new active independent research branch.

B14-B frozen mechanism:
- fresh funding window Jul1-Sep27 2026 exclusive end;
- OKX + Bybit;
- 12 fixed assets;
- 3 same-sign matched funding differentials;
- no magnitude threshold;
- enter after third realized settlement;
- fixed 7-day carry;
- all realized venue cashflows counted;
- non-overlapping cycles;
- 40 bps four-fill burden;
- 50 bps gross headroom hurdle;
- no price/basis/PnL.

Implementation:
`research/sc001/sc001_b14b_persistent_multisettlement_funding_carry_v0_1.py`

SHA:
`cb288810ef8871ea1de3bfe9decf6e372cb525c1c62d0123969d4f7f459793f4`

Next:
commit current preparation -> seal no-input offline self-test -> fresh Runner approval -> PASS -> separate approval for networked fresh 2026 funding-value screen.
