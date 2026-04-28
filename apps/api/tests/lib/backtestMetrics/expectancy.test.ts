import { describe, it, expect } from "vitest";
import { expectancy } from "../../../src/lib/backtestMetrics/expectancy.js";

describe("expectancy", () => {
  it("returns null on an empty array", () => {
    expect(expectancy([])).toBeNull();
  });

  it("matches a hand-calculated reference (mixed wins/losses)", () => {
    // pnl = [2, -1, 3, -2, 1]
    //   wins=[2,3,1] losses-abs=[1,2]
    //   winRate=3/5=0.6  lossRate=2/5=0.4
    //   avgWin=(2+3+1)/3=2  avgLoss=(1+2)/2=1.5
    //   E = 0.6*2 - 0.4*1.5 = 1.2 - 0.6 = 0.60
    expect(expectancy([2, -1, 3, -2, 1])).toBe(0.6);
  });

  it("returns 0 for a balanced 50/50 win/loss with equal magnitudes", () => {
    // winRate=0.5, avgWin=2, lossRate=0.5, avgLoss=2 → 0
    expect(expectancy([2, -2, 2, -2])).toBe(0);
  });

  it("matches a hand-calculated asymmetric series", () => {
    // 60% wins at +2, 40% losses at -1: 5 trades [2,2,2,-1,-1]
    //   winRate=0.6 avgWin=2  lossRate=0.4 avgLoss=1
    //   E = 0.6*2 - 0.4*1 = 1.2 - 0.4 = 0.80
    expect(expectancy([2, 2, 2, -1, -1])).toBe(0.8);
  });

  it("returns the trade's own pnl% for a single winning trade", () => {
    expect(expectancy([3.5])).toBe(3.5);
  });

  it("returns the trade's own pnl% (negative) for a single losing trade", () => {
    expect(expectancy([-1.25])).toBe(-1.25);
  });

  it("returns positive expectancy for an all-wins series", () => {
    // winRate=1, avgWin=mean, lossRate=0, avgLoss=0 → mean of wins.
    // [1.5, 2.0, 0.5] → mean = 4/3 ≈ 1.3333 → rounded 1.33
    expect(expectancy([1.5, 2.0, 0.5])).toBe(1.33);
  });

  it("returns negative expectancy for an all-losses series", () => {
    // [-1, -2, -0.5] → avgLoss = 3.5/3 ≈ 1.1667 → -1.17
    expect(expectancy([-1, -2, -0.5])).toBe(-1.17);
  });

  it("counts zero-pnl entries in totalTrades but contributes nothing", () => {
    // [2, 0, -1, 0] → wins=[2] losses=[1]
    //   winRate=1/4=0.25 lossRate=1/4=0.25
    //   avgWin=2 avgLoss=1
    //   E = 0.25*2 - 0.25*1 = 0.25
    expect(expectancy([2, 0, -1, 0])).toBe(0.25);
  });
});
