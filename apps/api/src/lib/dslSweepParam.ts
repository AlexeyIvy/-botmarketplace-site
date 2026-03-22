/**
 * DSL sweep parameter injection utility.
 *
 * Clones a compiled DSL and sets `paramName = paramValue` on every object
 * whose `nodeId` matches the sweep `blockId`.
 *
 * Compiled DSL blocks carry a `nodeId` field (from the graph compiler) that
 * corresponds to the sweep's `blockId`.  The same nodeId may appear in
 * multiple locations (e.g. entry.signal.fast AND entry.indicators[]), so we
 * walk the entire tree and patch every occurrence.
 */
export function applyDslSweepParam(
  dsl: Record<string, unknown>,
  blockId: string,
  paramName: string,
  paramValue: number,
): Record<string, unknown> {
  const cloned = structuredClone(dsl);

  function walk(obj: unknown): void {
    if (obj === null || obj === undefined || typeof obj !== "object") return;
    if (Array.isArray(obj)) {
      for (const item of obj) walk(item);
      return;
    }
    const rec = obj as Record<string, unknown>;
    if (rec.nodeId === blockId && paramName in rec) {
      rec[paramName] = paramValue;
    }
    for (const val of Object.values(rec)) walk(val);
  }

  walk(cloned);
  return cloned;
}
