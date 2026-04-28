/**
 * DSL sweep parameter injection utilities.
 *
 * `applyDslSweepParams` clones a compiled DSL once and then walks the tree
 * exactly once, applying every matching `{ blockId, paramName, value }` to
 * objects whose `nodeId` matches. The same nodeId may appear in multiple
 * locations (e.g. `entry.signal.fast` AND `entry.indicators[]`), so every
 * occurrence is patched.
 *
 * `applyDslSweepParam` is a thin single-param wrapper preserved for
 * backward compatibility — existing call sites keep working unchanged.
 *
 * Determinism:
 *   - Order of application = order of `params` array. If two entries
 *     target the same `(blockId, paramName)`, the LAST one wins. The HTTP
 *     layer (47-T1) rejects duplicate (blockId, paramName) tuples up front,
 *     so this is only a defensive contract.
 *   - The input DSL is never mutated; `structuredClone` produces a deep
 *     copy, then patches happen in place on the clone.
 */
export function applyDslSweepParams(
  dsl: Record<string, unknown>,
  params: Array<{ blockId: string; paramName: string; value: number }>,
): Record<string, unknown> {
  const cloned = structuredClone(dsl);

  function walk(obj: unknown): void {
    if (obj === null || obj === undefined || typeof obj !== "object") return;
    if (Array.isArray(obj)) {
      for (const item of obj) walk(item);
      return;
    }
    const rec = obj as Record<string, unknown>;
    // Apply every matching param at this node before recursing. Iteration
    // order matches `params` so duplicates resolve last-wins.
    for (const p of params) {
      if (rec.nodeId === p.blockId && p.paramName in rec) {
        rec[p.paramName] = p.value;
      }
    }
    for (const val of Object.values(rec)) walk(val);
  }

  walk(cloned);
  return cloned;
}

/**
 * Single-parameter sweep mutation. Equivalent to
 * `applyDslSweepParams(dsl, [{ blockId, paramName, value: paramValue }])`.
 * Retained as the legacy entry point so existing callers keep working.
 */
export function applyDslSweepParam(
  dsl: Record<string, unknown>,
  blockId: string,
  paramName: string,
  paramValue: number,
): Record<string, unknown> {
  return applyDslSweepParams(dsl, [{ blockId, paramName, value: paramValue }]);
}
