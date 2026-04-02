/**
 * SMC (Smart Money Concepts) pattern detection primitives.
 *
 * Each module exports pure, deterministic detection functions
 * that consume Candle[] and return typed pattern results.
 */

export { detectFairValueGaps, findFvgFillIndex } from "./fairValueGap.js";
export type { DetectFvgOptions } from "./fairValueGap.js";
export { detectLiquiditySweeps, findSwingPoints } from "./liquiditySweep.js";
export type { DetectSweepOptions } from "./liquiditySweep.js";
export { detectOrderBlocks } from "./orderBlock.js";
export type { DetectObOptions } from "./orderBlock.js";
export { detectMarketStructureShifts } from "./marketStructureShift.js";
export type { DetectMssOptions } from "./marketStructureShift.js";
export type {
  Candle,
  SmcDirection,
  FairValueGap,
  LiquiditySweep,
  OrderBlock,
  MssType,
  MarketStructureShift,
} from "./types.js";
