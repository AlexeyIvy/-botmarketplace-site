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

// ══════════════════════════════════════════════════════════
// Liquidity Sweep fixtures
// ══════════════════════════════════════════════════════════

// ──────────────────────────────────────────────────────────
// Bullish sweep fixture (swingLen=2)
// ──────────────────────────────────────────────────────────
// Bars 0-4: establish a swing low at bar 2 (low=95)
// Bar 5: sweeps below 95 (low=93) but closes above it (close=96)
// ──────────────────────────────────────────────────────────
export const bullishSweepFixture: Candle[] = [
  c(0, 100, 102, 98, 101),   // low=98
  c(1, 101, 103, 97, 100),   // low=97
  c(2, 100, 101, 95, 99),    // swing low: low=95 (lowest in [0..4])
  c(3, 99,  102, 97, 101),   // low=97
  c(4, 101, 104, 98, 103),   // low=98
  c(5, 103, 104, 93, 96),    // sweep: low=93 < 95, close=96 > 95 → bullish sweep
];

// ──────────────────────────────────────────────────────────
// Bearish sweep fixture (swingLen=2)
// ──────────────────────────────────────────────────────────
// Bars 0-4: establish a swing high at bar 2 (high=110)
// Bar 5: sweeps above 110 (high=112) but closes below it (close=108)
// ──────────────────────────────────────────────────────────
export const bearishSweepFixture: Candle[] = [
  c(0, 100, 105, 99, 103),   // high=105
  c(1, 103, 108, 101, 106),  // high=108
  c(2, 106, 110, 104, 107),  // swing high: high=110 (highest in [0..4])
  c(3, 107, 108, 103, 105),  // high=108
  c(4, 105, 106, 101, 103),  // high=106
  c(5, 103, 112, 102, 108),  // sweep: high=112 > 110, close=108 < 110 → bearish sweep
];

// ──────────────────────────────────────────────────────────
// No-sweep fixture: price breaks the level but does NOT reverse
// ──────────────────────────────────────────────────────────
export const noSweepFixture: Candle[] = [
  c(0, 100, 102, 98, 101),
  c(1, 101, 103, 97, 100),
  c(2, 100, 101, 95, 99),    // swing low at 95
  c(3, 99,  102, 97, 101),
  c(4, 101, 104, 98, 103),
  c(5, 103, 104, 93, 94),    // breaks below 95, but closes below too (94 < 95) → not a sweep
];

// ══════════════════════════════════════════════════════════
// Order Block fixtures
// ══════════════════════════════════════════════════════════

/**
 * Bullish Order Block fixture.
 * Bars 0-14: build ATR baseline (steady small moves).
 * Bar 15: bearish candle (close < open) — this is the OB candidate.
 * Bar 16: strong bullish impulse (body >> ATR) — confirms the OB.
 */
export function makeBullishObFixture(): Candle[] {
  const candles: Candle[] = [];
  // 15 bars of small-range price action to establish ATR ~1.0
  for (let i = 0; i < 15; i++) {
    const base = 100 + (i % 2 === 0 ? 0.3 : -0.3);
    candles.push(c(i, base, base + 0.5, base - 0.5, base + (i % 2 === 0 ? 0.2 : -0.2)));
  }
  // Bar 15: bearish candle (the order block)
  candles.push(c(15, 100.5, 101, 99, 99.5));
  // Bar 16: strong bullish impulse — body = 3 >> ATR ~1
  candles.push(c(16, 99.5, 103, 99.3, 102.5));
  return candles;
}

/**
 * Bearish Order Block fixture.
 * Same structure, reversed direction.
 */
export function makeBearishObFixture(): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < 15; i++) {
    const base = 100 + (i % 2 === 0 ? 0.3 : -0.3);
    candles.push(c(i, base, base + 0.5, base - 0.5, base + (i % 2 === 0 ? 0.2 : -0.2)));
  }
  // Bar 15: bullish candle (the order block)
  candles.push(c(15, 99.5, 101, 99, 100.5));
  // Bar 16: strong bearish impulse — body = 3 >> ATR ~1
  candles.push(c(16, 100.5, 100.7, 97, 97.5));
  return candles;
}

// ══════════════════════════════════════════════════════════
// Market Structure Shift fixtures
// ══════════════════════════════════════════════════════════

/**
 * Uptrend → BOS fixture (swingLen=2).
 *
 * Creates higher highs and higher lows, then a candle that breaks
 * the most recent swing high — confirming a bullish BOS.
 */
export function makeBosBullishFixture(): Candle[] {
  // Build an uptrend with clear swing points (swingLen=2)
  // Swing low at bar 2 (low=95), swing high at bar 5 (high=108)
  // Swing low at bar 8 (low=98 > 95 → HL), swing high at bar 11 (high=112 > 108 → HH)
  // Bar 14: breaks above swing high at bar 11 (112) → BOS bullish
  return [
    c(0,  100, 102, 98,  101),  // setup
    c(1,  101, 103, 97,  100),  // setup
    c(2,  100, 101, 95,  99),   // swing low (95)
    c(3,  99,  104, 97,  103),  // recovery
    c(4,  103, 107, 101, 106),  // up
    c(5,  106, 108, 103, 105),  // swing high (108)
    c(6,  105, 106, 101, 102),  // pullback
    c(7,  102, 103, 101, 101),  // pullback (low=101, above bar 8)
    c(8,  101, 102, 98,  101),  // swing low (98 > 95 → HL)
    c(9,  101, 105, 101, 104),  // recovery
    c(10, 104, 110, 103, 109),  // up
    c(11, 109, 112, 106, 110),  // swing high (112 > 108 → HH) → uptrend confirmed
    c(12, 110, 111, 107, 108),  // pullback
    c(13, 108, 110, 106, 109),  // pullback
    c(14, 109, 115, 108, 113),  // close=113 > 112 → BOS bullish
  ];
}

/**
 * Uptrend → CHoCH fixture (swingLen=2).
 *
 * Creates higher highs and higher lows (uptrend), then a candle that
 * breaks below the most recent swing low — signaling a bearish CHoCH.
 */
export function makeChochBearishFixture(): Candle[] {
  return [
    c(0,  100, 102, 98,  101),
    c(1,  101, 103, 97,  100),
    c(2,  100, 101, 95,  99),   // swing low (95)
    c(3,  99,  104, 97,  103),
    c(4,  103, 107, 101, 106),
    c(5,  106, 108, 103, 105),  // swing high (108)
    c(6,  105, 106, 101, 102),
    c(7,  102, 103, 101, 101),  // pullback (low=101, above bar 8)
    c(8,  101, 102, 98,  101),  // swing low (98 > 95 → HL) → uptrend
    c(9,  101, 105, 101, 104),
    c(10, 104, 110, 103, 109),
    c(11, 109, 112, 106, 110),  // swing high (112 > 108 → HH) → uptrend confirmed
    c(12, 110, 111, 107, 108),
    c(13, 108, 109, 106, 107),
    c(14, 107, 108, 95,  97),   // close=97 < 98 (swing low at 8) → CHoCH bearish
  ];
}
