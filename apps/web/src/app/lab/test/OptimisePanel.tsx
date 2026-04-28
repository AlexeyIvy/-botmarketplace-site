"use client";

// ---------------------------------------------------------------------------
// Phase C1 — Parametric Optimisation (Grid Search) panel
// Per docs/25-lab-improvements-plan.md §Phase C1
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, getWorkspaceId } from "../../../lib/api";
import { useLabGraphStore } from "../useLabGraphStore";
import { BLOCK_DEF_MAP } from "../build/blockDefs";
import type { LabNode } from "../useLabGraphStore";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SweepParam {
  blockId: string;
  paramName: string;
  from: number;
  to: number;
  step: number;
}

interface SweepRow {
  paramValue: number;
  /** 47-T3 multi-param values keyed by `${blockId}.${paramName}`. Optional —
   *  legacy server responses (pre-47-T3) carry only `paramValue`. */
  paramValues?: Record<string, number>;
  backtestResultId: string;
  pnlPct: number;
  winRate: number;
  maxDrawdownPct: number;
  tradeCount: number;
  sharpe: number | null;
}

interface SweepResult {
  id: string;
  status: "pending" | "running" | "done" | "failed";
  progress: number;
  runCount: number;
  /** 47-T1 multi-param echo. Old servers return only `sweepParam` (singular). */
  sweepParams?: SweepParam[];
  sweepParam?: SweepParam;
  rankBy?: RankBy;
  bestParamValue?: number | null;
  bestParamValuesJson?: Record<string, number> | null;
  results: SweepRow[];
  bestRow?: SweepRow;
  createdAt: string;
  updatedAt: string;
}

interface DatasetListItem {
  datasetId: string;
  name: string | null;
  symbol: string;
  interval: string;
  fromTsMs: string;
  toTsMs: string;
  candleCount: number;
  datasetHash: string;
  fetchedAt: string;
  status: "READY" | "PARTIAL" | "FAILED";
}

interface StrategyVersionItem {
  id: string;
  version: number;
  createdAt: string;
  strategy: { id: string; name: string; symbol: string };
}

// 47-T5: SortKey is a union of fixed metric columns plus dynamic
// `param:${blockId}.${paramName}` entries (one per sweep param) and the
// legacy `paramValue` literal used when the server response predates 47-T3.
type FixedSortKey = "pnlPct" | "winRate" | "maxDrawdownPct" | "tradeCount" | "sharpe";
type ParamSortKey = `param:${string}`;
type SortKey = FixedSortKey | ParamSortKey | "paramValue";
type SortDir = "asc" | "desc";

type OptimiseMetric = "pnl" | "winRate" | "sharpe" | "maxDrawdown";

/** Server-side rankBy values accepted by POST /lab/backtest/sweep (47-T4). */
type RankBy = "pnlPct" | "winRate" | "sharpe" | "profitFactor" | "expectancy";

/** Map UI `OptimiseMetric` to the server `rankBy` parameter. Missing entries
 *  signal "client-side sort only" — the server keeps its `pnlPct` default. */
const METRIC_TO_RANK_BY: Partial<Record<OptimiseMetric, RankBy>> = {
  pnl: "pnlPct",
  sharpe: "sharpe",
};

interface SweepParamForm {
  blockId: string;
  paramName: string;
  from: number;
  to: number;
  step: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 2000;
const MAX_RUNS = 20;
const MAX_PARAMS = 3;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtPnl(pct: number): string {
  return (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%";
}

function getNumericParams(node: LabNode) {
  const def = BLOCK_DEF_MAP[node.data.blockType];
  if (!def) return [];
  return def.params.filter((p) => p.type === "number");
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OptimisePanel({
  datasets,
  strategyVersions,
  onSelectBacktest,
}: {
  datasets: DatasetListItem[];
  strategyVersions: StrategyVersionItem[];
  onSelectBacktest?: (backtestResultId: string) => void;
}) {
  const nodes = useLabGraphStore((s) => s.nodes);
  const activeDatasetId = useLabGraphStore((s) => s.activeDatasetId);
  const lastCompileResult = useLabGraphStore((s) => s.lastCompileResult);
  const lastCompileVersionId = lastCompileResult?.strategyVersionId ?? null;

  // ── Form state ──────────────────────────────────────────────────────────
  const readyDatasets = datasets.filter((d) => d.status === "READY" || d.status === "PARTIAL");
  const [datasetId, setDatasetId] = useState(activeDatasetId ?? readyDatasets[0]?.datasetId ?? "");
  const [versionId, setVersionId] = useState(lastCompileVersionId ?? strategyVersions[0]?.id ?? "");
  // 47-T5: multi-param grid state. `sweepParams.length` ∈ [1, MAX_PARAMS].
  const [sweepParams, setSweepParams] = useState<SweepParamForm[]>([
    { blockId: "", paramName: "", from: 5, to: 50, step: 5 },
  ]);
  const [feeBps, setFeeBps] = useState(10);
  const [slippageBps, setSlippageBps] = useState(5);
  const [metric, setMetric] = useState<OptimiseMetric>("pnl");

  // ── Sweep state ─────────────────────────────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [activeSweep, setActiveSweep] = useState<SweepResult | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Sort state ──────────────────────────────────────────────────────────
  const [sortKey, setSortKey] = useState<SortKey>("paramValue");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  // ── Sync defaults ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!datasetId && readyDatasets.length > 0) setDatasetId(readyDatasets[0].datasetId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readyDatasets.length]);

  useEffect(() => {
    if (activeDatasetId) setDatasetId(activeDatasetId);
  }, [activeDatasetId]);

  useEffect(() => {
    if (lastCompileVersionId) setVersionId(lastCompileVersionId);
  }, [lastCompileVersionId]);

  useEffect(() => {
    if (!versionId && strategyVersions.length > 0) setVersionId(strategyVersions[0].id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategyVersions.length]);

  // Nodes with numeric params (blocks user can sweep)
  const sweepableNodes = nodes.filter((n) => getNumericParams(n).length > 0);

  // Numeric params for a given block id (helper used per row)
  const numericParamsFor = useCallback((blockId: string) => {
    const node = sweepableNodes.find((n) => n.id === blockId);
    return node ? getNumericParams(node) : [];
  }, [sweepableNodes]);

  // Auto-fill the first row when sweepable blocks become available.
  useEffect(() => {
    if (sweepableNodes.length === 0) return;
    setSweepParams((prev) => {
      const first = prev[0];
      if (first.blockId && first.paramName) return prev;
      const node = sweepableNodes[0];
      const param = getNumericParams(node)[0];
      if (!param) return prev;
      return prev.map((p, i) => i === 0 ? { ...p, blockId: node.id, paramName: param.id } : p);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sweepableNodes.length]);

  // Keep paramName valid when the row's block changes or its block is removed.
  useEffect(() => {
    setSweepParams((prev) => prev.map((p) => {
      const params = numericParamsFor(p.blockId);
      if (params.length === 0) return p;
      if (params.find((np) => np.id === p.paramName)) return p;
      return { ...p, paramName: params[0].id };
    }));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sweepableNodes.length]);

  // ── Computed ────────────────────────────────────────────────────────────
  // Per-row run counts (0 marks an invalid row).
  const runCounts = sweepParams.map((p) =>
    p.step > 0 && p.to > p.from ? Math.floor((p.to - p.from) / p.step) + 1 : 0,
  );
  const everyRowValid = runCounts.every((c) => c >= 2);
  const totalRunCount = everyRowValid ? runCounts.reduce((a, b) => a * b, 1) : 0;
  const runCountValid = everyRowValid && totalRunCount > 0 && totalRunCount <= MAX_RUNS;
  const allRowsFilled = sweepParams.every((p) => p.blockId && p.paramName);
  // Reject duplicate (blockId, paramName) tuples client-side as well —
  // server does the same in 47-T1.
  const duplicateRow = (() => {
    const seen = new Set<string>();
    for (const p of sweepParams) {
      const key = `${p.blockId}.${p.paramName}`;
      if (seen.has(key)) return key;
      seen.add(key);
    }
    return null;
  })();
  const canSubmit = !!datasetId && !!versionId && allRowsFilled && runCountValid && !duplicateRow && !submitting && !activeSweep;

  // ── Polling ─────────────────────────────────────────────────────────────
  const pollSweep = useCallback(async (sweepId: string) => {
    const res = await apiFetch<SweepResult>(`/lab/backtest/sweep/${sweepId}`);
    if (!res.ok) return null;
    setActiveSweep(res.data);
    return res.data;
  }, []);

  useEffect(() => {
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
    if (!activeSweep) return;
    if (activeSweep.status !== "pending" && activeSweep.status !== "running") return;

    const schedule = () => {
      pollRef.current = setTimeout(async () => {
        const updated = await pollSweep(activeSweep.id);
        if (updated?.status === "pending" || updated?.status === "running") {
          schedule();
        }
      }, POLL_INTERVAL_MS);
    };
    schedule();

    return () => {
      if (pollRef.current) {
        clearTimeout(pollRef.current);
        pollRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSweep?.id, activeSweep?.status]);

  // ── Submit sweep ────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (!getWorkspaceId()) return;
    setSubmitting(true);
    setSubmitError(null);

    // 47-T5: send the full sweepParams array. `rankBy` is forwarded only
    // for metrics the server supports natively (pnl, sharpe). Win-rate /
    // max-drawdown remain UI-only sorts; the server keeps its `pnlPct`
    // default for best-row selection.
    const rankBy = METRIC_TO_RANK_BY[metric];
    const body: Record<string, unknown> = {
      datasetId,
      strategyVersionId: versionId,
      sweepParams,
      feeBps,
      slippageBps,
    };
    if (rankBy) body.rankBy = rankBy;

    const res = await apiFetch<{ sweepId: string; runCount: number; estimatedSeconds: number }>(
      "/lab/backtest/sweep",
      { method: "POST", body: JSON.stringify(body) },
    );

    setSubmitting(false);

    if (res.ok) {
      setActiveSweep({
        id: res.data.sweepId,
        status: "pending",
        progress: 0,
        runCount: res.data.runCount,
        sweepParams,
        results: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });
    } else {
      setSubmitError(res.problem.detail ?? res.problem.title ?? "Unknown error");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, versionId, sweepParams, feeBps, slippageBps, metric]);

  // ── Sort results ────────────────────────────────────────────────────────
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  // 47-T5: param-column sort reads from `paramValues[`${blockId}.${paramName}`]`.
  // Legacy "paramValue" sort still works against the singular field.
  const readSortValue = (row: SweepRow, key: SortKey): number => {
    if (key === "paramValue") return row.paramValue ?? 0;
    if (typeof key === "string" && key.startsWith("param:")) {
      const k = key.slice("param:".length);
      return row.paramValues?.[k] ?? row.paramValue ?? 0;
    }
    const v = (row as unknown as Record<string, unknown>)[key];
    return typeof v === "number" ? v : 0;
  };

  const sortedResults = activeSweep?.results
    ? [...activeSweep.results].sort((a, b) => {
        const aVal = readSortValue(a, sortKey);
        const bVal = readSortValue(b, sortKey);
        return sortDir === "asc" ? aVal - bVal : bVal - aVal;
      })
    : [];

  const bestId = activeSweep?.bestRow?.backtestResultId;

  // ── Param-column metadata for the results table ───────────────────────
  // Prefer `sweepParams` from the server response (47-T1 echo). Fall back
  // to the keys present on the first row's `paramValues`. If neither is
  // available (legacy server), the table falls back to a single Param
  // column reading `paramValue`.
  const responseSweepParams: SweepParam[] | null = (() => {
    if (activeSweep?.sweepParams && activeSweep.sweepParams.length > 0) {
      return activeSweep.sweepParams;
    }
    const firstRow = activeSweep?.results?.[0];
    if (firstRow?.paramValues) {
      const keys = Object.keys(firstRow.paramValues);
      if (keys.length > 0) {
        return keys.map((k) => {
          const dot = k.indexOf(".");
          return {
            blockId: dot >= 0 ? k.slice(0, dot) : k,
            paramName: dot >= 0 ? k.slice(dot + 1) : "",
            from: 0, to: 0, step: 0,
          };
        });
      }
    }
    return null;
  })();
  const useLegacyParamColumn = responseSweepParams === null;

  const paramColumnLabel = (p: SweepParam): string => {
    const node = nodes.find((n) => n.id === p.blockId);
    if (!node) return `${p.blockId.slice(0, 6)}.${p.paramName}`;
    const def = BLOCK_DEF_MAP[node.data.blockType];
    if (!def) return `${node.id.slice(0, 6)}.${p.paramName}`;
    const paramDef = def.params.find((pd) => pd.id === p.paramName);
    return `${def.label} · ${paramDef?.label ?? p.paramName}`;
  };

  const paramColumnValue = (row: SweepRow, p: SweepParam): number | undefined => {
    const key = `${p.blockId}.${p.paramName}`;
    if (row.paramValues && key in row.paramValues) return row.paramValues[key];
    return row.paramValue;
  };

  // Per-metric best/worst for highlighting
  const metricExtremes = (() => {
    const rows = activeSweep?.results;
    if (!rows || rows.length < 2) return null;
    const keys: (keyof SweepRow)[] = ["pnlPct", "winRate", "maxDrawdownPct", "tradeCount", "sharpe"];
    const best: Record<string, number> = {};
    const worst: Record<string, number> = {};
    for (const key of keys) {
      const vals = rows.map((r) => r[key] as number | null).filter((v): v is number => v != null);
      if (vals.length === 0) continue;
      if (key === "maxDrawdownPct") {
        // Lower drawdown is better
        best[key] = Math.min(...vals);
        worst[key] = Math.max(...vals);
      } else {
        best[key] = Math.max(...vals);
        worst[key] = Math.min(...vals);
      }
    }
    return { best, worst };
  })();

  const cellColor = (key: string, val: number | null): string | undefined => {
    if (val == null || !metricExtremes) return undefined;
    const { best, worst } = metricExtremes;
    if (best[key] === worst[key]) return undefined; // all same value
    if (val === best[key]) return "#3fb950";  // green
    if (val === worst[key]) return "#f85149"; // red
    return undefined;
  };

  // ── Block label helper ──────────────────────────────────────────────────
  const blockLabel = (node: LabNode) => {
    const def = BLOCK_DEF_MAP[node.data.blockType];
    return def ? `${def.label} (${node.id.slice(0, 6)})` : node.id;
  };

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: "20px 24px", maxWidth: 700, overflow: "auto", height: "100%" }}>
      <h3 style={titleStyle}>Optimise — Grid Search</h3>

      {/* Active sweep — results view */}
      {activeSweep && (
        <div>
          {/* Progress */}
          {(activeSweep.status === "pending" || activeSweep.status === "running") && (
            <div style={progressBarContainerStyle}>
              <div style={{ ...progressBarFillStyle, width: `${(activeSweep.progress / activeSweep.runCount) * 100}%` }} />
              <span style={progressTextStyle}>
                {activeSweep.progress} / {activeSweep.runCount} runs ({activeSweep.status})
              </span>
            </div>
          )}

          {activeSweep.status === "done" && (
            <div style={doneBannerStyle}>
              Sweep complete — {activeSweep.runCount} runs. Best params:{" "}
              {(() => {
                // Multi-param: render as `label1=v1, label2=v2`. Falls back
                // to the single legacy `paramValue` if no `paramValues` map
                // is available on either bestRow or bestParamValuesJson.
                const map =
                  activeSweep.bestRow?.paramValues
                  ?? activeSweep.bestParamValuesJson
                  ?? null;
                if (map && Object.keys(map).length > 0 && responseSweepParams) {
                  return responseSweepParams
                    .map((p) => {
                      const v = map[`${p.blockId}.${p.paramName}`];
                      return `${paramColumnLabel(p)}=${v ?? "—"}`;
                    })
                    .join(", ");
                }
                return activeSweep.bestRow?.paramValue ?? activeSweep.bestParamValue ?? "—";
              })()}
            </div>
          )}

          {activeSweep.status === "failed" && (
            <div style={errorBoxStyle}>Sweep failed.</div>
          )}

          {/* Results table */}
          {sortedResults.length > 0 && (
            <div style={{ overflow: "auto", marginTop: 12 }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={theadRowStyle}>
                    {/* 47-T5: dynamic param columns. Falls back to a single
                        `paramValue` column when the response is from a
                        legacy server that doesn't return `sweepParams`. */}
                    {useLegacyParamColumn ? (
                      <th
                        style={{ ...thStyle, cursor: "pointer" }}
                        onClick={() => handleSort("paramValue")}
                      >
                        Param {sortKey === "paramValue" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                      </th>
                    ) : (
                      responseSweepParams!.map((p) => {
                        const key: ParamSortKey = `param:${p.blockId}.${p.paramName}`;
                        return (
                          <th
                            key={key}
                            style={{ ...thStyle, cursor: "pointer" }}
                            onClick={() => handleSort(key)}
                          >
                            {paramColumnLabel(p)} {sortKey === key ? (sortDir === "asc" ? "▲" : "▼") : ""}
                          </th>
                        );
                      })
                    )}
                    {(
                      [
                        ["pnlPct", "PnL %"],
                        ["winRate", "Win Rate"],
                        ["maxDrawdownPct", "Max DD %"],
                        ["tradeCount", "Trades"],
                        ["sharpe", "Sharpe"],
                      ] as [FixedSortKey, string][]
                    ).map(([key, label]) => (
                      <th
                        key={key}
                        style={{ ...thStyle, cursor: "pointer" }}
                        onClick={() => handleSort(key)}
                      >
                        {label} {sortKey === key ? (sortDir === "asc" ? "▲" : "▼") : ""}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedResults.map((r) => {
                    const isBest = r.backtestResultId === bestId;
                    return (
                      <tr
                        key={r.backtestResultId}
                        style={{
                          borderBottom: "1px solid rgba(255,255,255,0.04)",
                          background: isBest ? "rgba(212,164,76,0.08)" : "transparent",
                          borderLeft: isBest ? "3px solid #D4A44C" : "3px solid transparent",
                          cursor: onSelectBacktest ? "pointer" : "default",
                        }}
                        onClick={() => onSelectBacktest?.(r.backtestResultId)}
                        title={onSelectBacktest ? "Click to view backtest detail" : undefined}
                      >
                        {useLegacyParamColumn ? (
                          <td style={tdStyle}>{r.paramValue}</td>
                        ) : (
                          responseSweepParams!.map((p) => (
                            <td key={`${p.blockId}.${p.paramName}`} style={tdStyle}>
                              {paramColumnValue(r, p) ?? "—"}
                            </td>
                          ))
                        )}
                        <td style={{ ...tdStyle, color: cellColor("pnlPct", r.pnlPct) ?? (r.pnlPct >= 0 ? "#3fb950" : "#f85149"), fontWeight: 600 }}>{fmtPnl(r.pnlPct)}</td>
                        <td style={{ ...tdStyle, color: cellColor("winRate", r.winRate) }}>{(r.winRate * 100).toFixed(1)}%</td>
                        <td style={{ ...tdStyle, color: cellColor("maxDrawdownPct", r.maxDrawdownPct) }}>{r.maxDrawdownPct.toFixed(2)}%</td>
                        <td style={{ ...tdStyle, color: cellColor("tradeCount", r.tradeCount) }}>{r.tradeCount}</td>
                        <td style={{ ...tdStyle, color: cellColor("sharpe", r.sharpe) }}>{r.sharpe != null ? r.sharpe.toFixed(2) : "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* New sweep button */}
          {(activeSweep.status === "done" || activeSweep.status === "failed") && (
            <button
              style={{ ...runBtnStyle, marginTop: 14, background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.7)" }}
              onClick={() => setActiveSweep(null)}
            >
              New Sweep
            </button>
          )}
        </div>
      )}

      {/* Form — shown when no active sweep */}
      {!activeSweep && (
        <>
          {/* Sweep param rows (1..MAX_PARAMS) */}
          {sweepableNodes.length === 0 ? (
            <div style={emptyHintStyle}>No blocks with numeric parameters in the graph.</div>
          ) : (
            sweepParams.map((row, idx) => {
              const rowParams = numericParamsFor(row.blockId);
              const rowRuns = runCounts[idx];
              return (
                <div key={idx} style={paramRowCardStyle}>
                  <div style={paramRowHeaderStyle}>
                    <span style={paramRowTitleStyle}>Parameter {idx + 1}</span>
                    {sweepParams.length > 1 && (
                      <button
                        type="button"
                        style={removeBtnStyle}
                        onClick={() =>
                          setSweepParams((prev) => prev.filter((_, i) => i !== idx))
                        }
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <FormRow label="Target block">
                    <select
                      style={selectStyle}
                      value={row.blockId}
                      onChange={(e) =>
                        setSweepParams((prev) =>
                          prev.map((p, i) => (i === idx ? { ...p, blockId: e.target.value } : p)),
                        )
                      }
                    >
                      {sweepableNodes.map((n) => (
                        <option key={n.id} value={n.id}>{blockLabel(n)}</option>
                      ))}
                    </select>
                  </FormRow>
                  <FormRow label="Parameter">
                    {rowParams.length === 0 ? (
                      <div style={emptyHintStyle}>Select a block with numeric parameters.</div>
                    ) : (
                      <select
                        style={selectStyle}
                        value={row.paramName}
                        onChange={(e) =>
                          setSweepParams((prev) =>
                            prev.map((p, i) => (i === idx ? { ...p, paramName: e.target.value } : p)),
                          )
                        }
                      >
                        {rowParams.map((p) => (
                          <option key={p.id} value={p.id}>{p.label} (default: {String(p.defaultValue)})</option>
                        ))}
                      </select>
                    )}
                  </FormRow>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                    <FormRow label="From">
                      <input
                        type="number"
                        style={inputStyle}
                        value={row.from}
                        onChange={(e) =>
                          setSweepParams((prev) =>
                            prev.map((p, i) => (i === idx ? { ...p, from: Number(e.target.value) } : p)),
                          )
                        }
                      />
                    </FormRow>
                    <FormRow label="To">
                      <input
                        type="number"
                        style={inputStyle}
                        value={row.to}
                        onChange={(e) =>
                          setSweepParams((prev) =>
                            prev.map((p, i) => (i === idx ? { ...p, to: Number(e.target.value) } : p)),
                          )
                        }
                      />
                    </FormRow>
                    <FormRow label="Step">
                      <input
                        type="number"
                        style={inputStyle}
                        value={row.step}
                        min={0.01}
                        onChange={(e) =>
                          setSweepParams((prev) =>
                            prev.map((p, i) => (i === idx ? { ...p, step: Number(e.target.value) } : p)),
                          )
                        }
                      />
                    </FormRow>
                  </div>
                  <div style={paramRowFooterStyle}>
                    {rowRuns >= 2
                      ? `${rowRuns} values`
                      : "Invalid range — ensure from < to and step > 0 (≥ 2 values)."}
                  </div>
                </div>
              );
            })
          )}

          {sweepableNodes.length > 0 && (
            <button
              type="button"
              style={{
                ...addParamBtnStyle,
                opacity: sweepParams.length >= MAX_PARAMS ? 0.4 : 1,
                cursor: sweepParams.length >= MAX_PARAMS ? "not-allowed" : "pointer",
              }}
              disabled={sweepParams.length >= MAX_PARAMS}
              onClick={() => {
                const node = sweepableNodes[0];
                const param = node ? getNumericParams(node)[0] : null;
                setSweepParams((prev) => [
                  ...prev,
                  { blockId: node?.id ?? "", paramName: param?.id ?? "", from: 5, to: 50, step: 5 },
                ]);
              }}
            >
              + Add parameter ({sweepParams.length}/{MAX_PARAMS})
            </button>
          )}

          <div style={hintStyle}>
            {duplicateRow
              ? `Duplicate parameter ${duplicateRow}. Each (block, param) pair must be unique.`
              : runCountValid
                ? `${totalRunCount} runs (Π of per-row counts) will be executed sequentially.`
                : everyRowValid && totalRunCount > MAX_RUNS
                  ? `Too many runs (${totalRunCount}). Max ${MAX_RUNS} (product of run-counts across all parameters). Narrow ranges or raise step.`
                  : "Set a valid range for each parameter (from < to, step > 0, ≥ 2 values per row)."}
          </div>

          {/* Dataset */}
          <FormRow label="Dataset">
            {readyDatasets.length === 0 ? (
              <div style={emptyHintStyle}>No ready datasets. Create one in the Data tab.</div>
            ) : (
              <select style={selectStyle} value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
                {readyDatasets.map((d) => (
                  <option key={d.datasetId} value={d.datasetId}>
                    {d.name ?? `${d.symbol} · ${d.interval}`} ({new Date(Number(d.fromTsMs)).toLocaleDateString()} → {new Date(Number(d.toTsMs)).toLocaleDateString()})
                  </option>
                ))}
              </select>
            )}
          </FormRow>

          {/* Strategy version */}
          <FormRow label="Strategy version">
            {strategyVersions.length === 0 ? (
              <div style={emptyHintStyle}>No compiled versions. Compile a graph in the Build tab first.</div>
            ) : (
              <select style={selectStyle} value={versionId} onChange={(e) => setVersionId(e.target.value)}>
                {strategyVersions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.strategy.name} v{v.version} · {v.strategy.symbol} · {new Date(v.createdAt).toLocaleDateString()}
                  </option>
                ))}
              </select>
            )}
          </FormRow>

          {/* Fee + slippage */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <FormRow label="Fee (bps)">
              <input type="number" style={inputStyle} value={feeBps} min={0} max={1000} step={1} onChange={(e) => setFeeBps(Number(e.target.value))} />
            </FormRow>
            <FormRow label="Slippage (bps)">
              <input type="number" style={inputStyle} value={slippageBps} min={0} max={1000} step={1} onChange={(e) => setSlippageBps(Number(e.target.value))} />
            </FormRow>
          </div>

          {/* Metric — `pnl`/`sharpe` are forwarded to the server as
              `rankBy`; `winRate`/`maxDrawdown` remain UI-only sorts. */}
          <FormRow label="Optimise for">
            <select style={selectStyle} value={metric} onChange={(e) => setMetric(e.target.value as OptimiseMetric)}>
              <option value="pnl">Total PnL %</option>
              <option value="winRate">Win Rate (UI sort only)</option>
              <option value="sharpe">Sharpe Ratio</option>
              <option value="maxDrawdown">Min Drawdown (UI sort only)</option>
            </select>
          </FormRow>

          {submitError && <div style={errorBoxStyle}>{submitError}</div>}

          <button
            style={{ ...runBtnStyle, opacity: canSubmit ? 1 : 0.45, cursor: canSubmit ? "pointer" : "not-allowed" }}
            disabled={!canSubmit}
            onClick={handleSubmit}
          >
            {submitting ? "Starting sweep…" : `Run Sweep (${totalRunCount || 0} runs)`}
          </button>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={formLabelStyle}>{label}</label>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const titleStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  color: "rgba(255,255,255,0.88)",
  marginBottom: 18,
};

const formLabelStyle: React.CSSProperties = {
  display: "block",
  fontSize: 10,
  fontWeight: 700,
  color: "rgba(255,255,255,0.35)",
  marginBottom: 5,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
};

const selectStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.07)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6,
  padding: "7px 10px",
  color: "rgba(255,255,255,0.85)",
  fontSize: 12,
  width: "100%",
  boxSizing: "border-box",
};

const inputStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.07)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6,
  padding: "7px 10px",
  color: "rgba(255,255,255,0.85)",
  fontSize: 12,
  width: "100%",
  boxSizing: "border-box",
};

const hintStyle: React.CSSProperties = {
  fontSize: 11,
  color: "rgba(255,255,255,0.3)",
  marginBottom: 14,
};

const emptyHintStyle: React.CSSProperties = {
  fontSize: 11,
  color: "rgba(255,255,255,0.3)",
  padding: "6px 0",
};

const runBtnStyle: React.CSSProperties = {
  background: "#3b82f6",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  padding: "9px 20px",
  fontSize: 13,
  fontWeight: 600,
  width: "100%",
  marginTop: 8,
  fontFamily: "inherit",
  cursor: "pointer",
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,81,73,0.12)",
  border: "1px solid rgba(248,81,73,0.35)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#f85149",
  margin: "12px 0",
};

const progressBarContainerStyle: React.CSSProperties = {
  position: "relative",
  height: 28,
  background: "rgba(255,255,255,0.06)",
  borderRadius: 6,
  overflow: "hidden",
  marginBottom: 12,
};

const progressBarFillStyle: React.CSSProperties = {
  position: "absolute",
  top: 0,
  left: 0,
  height: "100%",
  background: "rgba(59,130,246,0.35)",
  transition: "width 0.3s ease",
};

const progressTextStyle: React.CSSProperties = {
  position: "relative",
  zIndex: 1,
  display: "flex",
  alignItems: "center",
  height: "100%",
  padding: "0 12px",
  fontSize: 12,
  color: "rgba(255,255,255,0.7)",
  fontWeight: 500,
};

const doneBannerStyle: React.CSSProperties = {
  background: "rgba(63,185,80,0.1)",
  border: "1px solid rgba(63,185,80,0.3)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#3fb950",
  marginBottom: 12,
};

const theadRowStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  borderBottom: "1px solid rgba(255,255,255,0.07)",
};

const thStyle: React.CSSProperties = {
  padding: "8px 10px",
  textAlign: "left",
  fontWeight: 600,
  fontSize: 10,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "rgba(255,255,255,0.4)",
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  padding: "7px 10px",
  color: "rgba(255,255,255,0.72)",
  whiteSpace: "nowrap",
  fontFamily: "monospace",
  fontSize: 12,
};

const paramRowCardStyle: React.CSSProperties = {
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 6,
  padding: "12px 14px 4px",
  marginBottom: 10,
  background: "rgba(255,255,255,0.02)",
};

const paramRowHeaderStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 8,
};

const paramRowTitleStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "rgba(255,255,255,0.5)",
};

const removeBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "1px solid rgba(248,81,73,0.35)",
  borderRadius: 4,
  padding: "3px 9px",
  fontSize: 11,
  color: "#f85149",
  cursor: "pointer",
  fontFamily: "inherit",
};

const paramRowFooterStyle: React.CSSProperties = {
  fontSize: 11,
  color: "rgba(255,255,255,0.35)",
  marginTop: 2,
  marginBottom: 6,
};

const addParamBtnStyle: React.CSSProperties = {
  background: "rgba(59,130,246,0.12)",
  border: "1px dashed rgba(59,130,246,0.35)",
  borderRadius: 6,
  padding: "8px 12px",
  fontSize: 12,
  color: "rgba(255,255,255,0.85)",
  fontFamily: "inherit",
  width: "100%",
  marginBottom: 12,
};
