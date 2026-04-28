/**
 * Cartesian enumeration for multi-parameter sweep grids (47-T3).
 *
 * Given an array of SweepParam descriptors, produce every combination
 * of `(blockId, paramName, value)` tuples — one inner array per run.
 * Order is lexicographic by index: the LAST parameter iterates fastest
 * (`[0,0,0], [0,0,1], …`). This is fixed in the contract for
 * reproducibility and is asserted in the unit tests.
 *
 * Each value is rounded to 8 decimal places to avoid float drift across
 * accumulating `from + step + step + …` steps — same convention as the
 * legacy 1-D loop in routes/lab.ts.
 *
 * Pure function. No I/O, no side effects.
 */

export interface SweepParamDescriptor {
  blockId: string;
  paramName: string;
  from: number;
  to: number;
  step: number;
}

export interface ParamAssignment {
  blockId: string;
  paramName: string;
  value: number;
}

function expandValues(p: SweepParamDescriptor): number[] {
  const out: number[] = [];
  // The 1e-9 epsilon protects against float drift when `to` should be
  // included (e.g. from=1, step=0.1, to=2.0 — without it the last value
  // would drop out due to 1.999999999 vs 2.0 comparison).
  for (let v = p.from; v <= p.to + 1e-9; v += p.step) {
    out.push(Math.round(v * 1e8) / 1e8);
  }
  return out;
}

export function enumerateGrid(
  params: SweepParamDescriptor[],
): ParamAssignment[][] {
  if (params.length === 0) return [];
  const valuesByParam = params.map(expandValues);

  const combinations: ParamAssignment[][] = [];
  const current: ParamAssignment[] = [];
  function recurse(depth: number): void {
    if (depth === params.length) {
      combinations.push(current.map((c) => ({ ...c })));
      return;
    }
    const p = params[depth];
    for (const value of valuesByParam[depth]) {
      current.push({ blockId: p.blockId, paramName: p.paramName, value });
      recurse(depth + 1);
      current.pop();
    }
  }
  recurse(0);
  return combinations;
}
