# SC001 Current Roadmap and Stop Rules v3.7

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — E008 TERMINAL FAIL / DEEP READ-ONLY FORENSIC OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.6.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact:

`E008_DISCOVERY_FAIL`

No rescue-tuning, no promotional rerun, no Confirmation/Q2/formal Validation/Final.

## 2. First read-only postmortem result

`E008_READONLY_POSTMORTEM_PASS` completed without strategy rerun.

Observed primary decomposition:
- completed cycles = 2058;
- forced taker share = ~99.514%;
- mean realized fee drag = ~6.9853 bps/cycle;
- mean net edge = ~-8.5296 bps/cycle;
- implied/recorded mean gross edge is materially negative before fees (~-1.544 bps/cycle);
- forced-cycle gross edge is also negative (~-1.547 bps);
- maker-only cycles = 10, with negative mean gross edge (~-1.05 bps) and negative mean net edge (~-5.05 bps);
- level-disappear cancels = 15,740;
- best-move cancel requests counter = 433,658 (diagnostic counter includes repeated requests while cancellation may already be pending and is not equal to distinct cancel acknowledgements);
- placement activations = 37,733;
- semantic snapshots = 11,520;
- >5s semantic gaps = 0;
- same-ms zero-credit share of trade rows ~= 3.016%.

Interpretation: fee drag is large but does not explain the whole loss; frozen realized gross edge is already negative. At the same time, several queue/execution assumptions can bias passive completion strongly downward.

## 3. Expert implementation/microstructure concerns retained

Before opening a new experiment, distinguish robust economics from model artifacts:

- hypothetical own resting orders are absent from the exogenous historical book;
- historical disappearance of an external level can therefore falsely imply that our resting level disappears;
- zero credit for all displayed-size decreases is a strict lower-bound assumption, not a central FIFO estimate;
- all post-placement displayed-size additions being added ahead is also an adversarial lower bound; under actual price-time priority, orders arriving after a resting order normally queue behind it;
- periodic full snapshots should be treated as feed state/resynchronization information, not automatically as venue-side cancellation of a real resting order unless a separate trust failure requires it;
- forced taker exit should ultimately be modeled from executable opposite-side book depth, not an arbitrary next public trade;
- separate trade/book feeds do not provide exact cross-feed ordering for equal timestamps;
- best-move cancel-request count is not a distinct-cancel count in the frozen runner;
- historical instrument specs (`lotSz`, `minSz`, `tickSz`, `ctVal`) and applicable fee basis must be frozen explicitly for future promotional work.

These observations do not reopen E008.

## 4. Current hard gate: deep read-only microstructure forensic

Protocol:
`docs/research/sc001-e008-readonly-microstructure-forensic-protocol-v1.0.md`

Runner:
`research/sc001/sc001_e008_readonly_microstructure_forensic.py`

This stage replays only already-qualified L2 bodies and computes no hypothetical orders/fills. It measures:
- time-weighted quoted spread vs 4/5/7 bps economic thresholds;
- best-price churn;
- same-price best-size increases/decreases;
- prior-best disappearance events;
- periodic snapshot cadence;
- frozen terminal-cycle duration/side diagnostics from the existing report only.

Required exact terminal token:

`E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS`

## 5. Why this gate matters before E009/new family

If the quoted spread itself is almost always below the regular-user round-trip maker fee floor, a naive two-sided top-of-book spread-capture family is structurally unattractive regardless of queue-model refinements.

If aggregate size decreases/additions, level disappearance and snapshots are extremely frequent, the E008 adversarial queue rules may explain much of the ~99.5% forced-exit rate and should not be reused as a central estimator in a new family.

Both can be true simultaneously: the specific E008 strategy can be genuinely uneconomic while the frozen E008 simulator is also too pessimistic to estimate realistic passive fill probability.

## 6. Immediate next action

On VPS:
1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_e008_readonly_microstructure_forensic.py`;
3. run it in tmux because full eight-day L2 replay can take significant time;
4. preserve output log;
5. require `E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS`;
6. review spread/queue/churn diagnostics;
7. only then freeze a new independent SC001 experiment family.

No E008 strategy command may be executed.
