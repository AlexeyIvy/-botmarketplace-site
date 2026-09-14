# SC001-E002 OKX Q1 Midquote Confirmation — Implementation Freeze v0.1

Status: **FROZEN BEFORE FOUR-DAY MIDQUOTE CONFIRMATION RUN**

Parent statistical protocol:
`docs/research/sc001-e002-okx-midquote-q1-confirmation-freeze-v0.1.md`

Protocol commit:
`c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7`

Confirmation engine:
`research/sc001/sc001_e002_okx_midquote_q1_confirmation.py`

Engine commit:
`38d3ab050ff64555b0149c31c52e1ab1775ae579`

Termux launcher:
`research/sc001/sc001_e002_okx_midquote_q1_confirmation_termux_launcher.py`

Launcher commit:
`147f97985cfe2721b87e3822b4d2f0137a84482c`

## Frozen scope

Exactly four already preselected non-pilot 2024-Q1 OKX days:
- 2024-01-14 — ordinary weekend;
- 2024-01-31 — FOMC;
- 2024-02-12 — ordinary weekday;
- 2024-02-13 — CPI.

No replacement dates are permitted.

## Frozen mechanism

- 5-second UTC-aligned TFI from OKX taker trades;
- 5-second future L2 midquote response;
- latencies 100 / 250 / 500 ms;
- last valid L2 book state at or before each target timestamp;
- no look-ahead;
- no book-state-age filter in the primary result;
- no strategy P&L, taker execution profitability, Q2, formal Validation, or Final access.

The verdict gates remain exactly those frozen in the parent confirmation protocol.

## Engineering controls

The engine requires local PASS parents Q006R, Q009A and Q009B before calculating confirmation metrics.

The long phone computation is resumable at the **completed-day computation level**. After a day finishes, the engine writes a private computational checkpoint under:

`SC001_E002_OKX_MIDQUOTE_Q1_CONFIRMATION/_checkpoints_do_not_inspect_until_complete/`

The checkpoint exists only to avoid repeating multi-million-record L2 replay after Android/process interruption. Partial checkpoint alpha must not be inspected or interpreted before all four frozen days complete.

Each fresh day verifies the retained L2 source SHA-256 against its already-qualified parent report before calculating the midquote response. L2 replay progress is inherited from the pinned pilot implementation and prints every 1,000,000 records.

The engine uses Python standard library only and is intended to run under Termux / Python 3.14.x inside tmux with `termux-wake-lock`.

## Sequential-testing boundary

The final report, CSV, summary and verdict are written only after all four days are available to the final aggregation step.

If the run is interrupted, rerun the exact same frozen launcher. Completed-day checkpoints may be reused, but the rules, dates, thresholds, latency scenarios and gates must not change.

## Next decision

- `MIDQUOTE_CONFIRMATION_FAIL`: do not rescue the same E002 version with post-hoc windows, filters, sides, event exclusions or thresholds.
- `MIDQUOTE_CONFIRMATION_WEAK`: retain as weak predictive evidence; do not promote to executable economics without a separately justified decision.
- `MIDQUOTE_CONFIRMATION_PASS`: stop signal-screen expansion and move to a separately frozen, causal same-venue taker-execution economics design on already-open Q1 data, while preserving 2024-Q2 OKX as the next chronological same-venue holdout.
