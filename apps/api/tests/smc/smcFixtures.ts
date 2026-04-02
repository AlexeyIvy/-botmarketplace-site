/**
 * Canonical SMC test fixtures — hand-crafted candle sequences with
 * known pattern outcomes for deterministic regression testing.
 */

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const T0 = 1_700_000_000_000;
const M1 = 60_000; // 1-minute interval

/**
 * Helper: build a candle with sensible defaults.
 */
function c(i: number, open: number, high: number, low: number, close: number, volume = 1000): Candle {
  return { openTime: T0 + i * M1, open, high, low, close, volume };
}

// ──────────────────────────────────────────────────────────
// Bullish FVG fixture
// ──────────────────────────────────────────────────────────
// Candle 0: high = 102        (first candle ceiling)
// Candle 1: big bullish move  (impulse candle)
// Candle 2: low = 104         (third candle floor)
// Gap zone: [102, 104] — candle 0 high < candle 2 low
//
// Then candle 3 fills the gap by dipping to 101.
// ──────────────────────────────────────────────────────────
export const bullishFvgFixture: Candle[] = [
  c(0, 100, 102, 99, 101),   // first: high = 102
  c(1, 101, 108, 100, 107),  // impulse: big bullish body
  c(2, 107, 110, 104, 109),  // third: low = 104 → gap [102, 104]
  c(3, 109, 109, 101, 103),  // fills the gap: low=101 ≤ 102
];

// ──────────────────────────────────────────────────────────
// Bearish FVG fixture
// ──────────────────────────────────────────────────────────
// Candle 0: low = 98          (first candle floor)
// Candle 1: big bearish move  (impulse candle)
// Candle 2: high = 96         (third candle ceiling)
// Gap zone: [96, 98] — candle 0 low > candle 2 high
//
// Then candle 3 fills the gap by rallying to 99.
// ──────────────────────────────────────────────────────────
export const bearishFvgFixture: Candle[] = [
  c(0, 100, 102, 98, 99),    // first: low = 98
  c(1, 99, 100, 91, 92),     // impulse: big bearish body
  c(2, 92, 96, 90, 93),      // third: high = 96 → gap [96, 98]
  c(3, 93, 99, 92, 98),      // fills the gap: high=99 ≥ 98
];

// ──────────────────────────────────────────────────────────
// No-FVG fixture: overlapping wicks, no gap forms
// ──────────────────────────────────────────────────────────
export const noFvgFixture: Candle[] = [
  c(0, 100, 105, 99, 103),   // high = 105
  c(1, 103, 107, 101, 106),  // move up
  c(2, 106, 108, 104, 107),  // low = 104 < 105 → wicks overlap, no bullish FVG
  c(3, 107, 109, 105, 108),
];

// ──────────────────────────────────────────────────────────
// Multiple FVGs in a strong trend
// ──────────────────────────────────────────────────────────
export const multiFvgFixture: Candle[] = [
  c(0, 100, 102, 99, 101),    // first[0]: high = 102
  c(1, 101, 108, 100, 107),   // impulse
  c(2, 107, 112, 104, 111),   // gap 1: [102, 104] bullish; window[1,2,3]: c1.h=108 vs c3.l=108 → no gap
  c(3, 111, 115, 108, 114),   // first[1]: high = 115; window[2,3,4]: c2.h=112 vs c4.l=112 → no gap
  c(4, 114, 122, 112, 121),   // impulse; c4.low=112 = c2.high → no FVG for window [2,3,4]
  c(5, 121, 127, 117, 126),   // gap 2: [115, 117] bullish
];

// ──────────────────────────────────────────────────────────
// Unfilled FVG fixture — gap forms but is never filled
// ──────────────────────────────────────────────────────────
export const unfilledFvgFixture: Candle[] = [
  c(0, 100, 102, 99, 101),
  c(1, 101, 108, 100, 107),
  c(2, 107, 110, 104, 109),   // bullish FVG [102, 104]
  c(3, 109, 112, 108, 111),   // does not fill: low=108 > 102
  c(4, 111, 115, 110, 114),   // does not fill: low=110 > 102
];

// ──────────────────────────────────────────────────────────
// Flat market — no FVGs expected
// ──────────────────────────────────────────────────────────
export const flatMarketFixture: Candle[] = [
  c(0, 100, 100.5, 99.5, 100),
  c(1, 100, 100.5, 99.5, 100),
  c(2, 100, 100.5, 99.5, 100),
  c(3, 100, 100.5, 99.5, 100),
  c(4, 100, 100.5, 99.5, 100),
];
