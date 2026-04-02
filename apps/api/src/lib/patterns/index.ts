/**
 * SMC (Smart Money Concepts) pattern detection primitives.
 *
 * Each module exports pure, deterministic detection functions
 * that consume Candle[] and return typed pattern results.
 */

export { detectFairValueGaps, findFvgFillIndex } from "./fairValueGap.js";
export type { DetectFvgOptions } from "./fairValueGap.js";
export type { Candle, SmcDirection, FairValueGap } from "./types.js";
