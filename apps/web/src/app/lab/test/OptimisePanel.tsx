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

type SortKey = "paramValue" | "pnlPct" | "winRate" | "maxDrawdownPct" | "tradeCount" | "sharpe";
type SortDir = "asc" | "desc";

type OptimiseMetric = "pnl" | "winRate" | "sharpe" | "maxDrawdown";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 2000;
const MAX_RUNS = 50;

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
}: {
  datasets: DatasetListItem[];
  strategyVersions: StrategyVersionItem[];
}) {
  const nodes = useLabGraphStore((s) => s.nodes);
  const activeDatasetId = useLabGraphStore((s) => s.activeDatasetId);
  const lastCompileResult = useLabGraphStore((s) => s.lastCompileResult);
  const lastCompileVersionId = lastCompileResult?.strategyVersionId ?? null;

  // ── Form state ──────────────────────────────────────────────────────────
  const readyDatasets = datasets.filter((d) => d.status === "READY" || d.status === "PARTIAL");
  const [datasetId, setDatasetId] = useState(activeDatasetId ?? readyDatasets[0]?.datasetId ?? "");
  const [versionId, setVersionId] = useState(lastCompileVersionId ?? strategyVersions[0]?.id ?? "");
  const [selectedBlockId, setSelectedBlockId] = useState("");
  const [selectedParamName, setSelectedParamName] = useState("");
  const [rangeFrom, setRangeFrom] = useState(5);
  const [rangeTo, setRangeTo] = useState(50);
  const [rangeStep, setRangeStep] = useState(5);
  const [feeBps, setFeeBps] = useState(10);
  const [slippageBps, setSlippageBps] = useState(5);
  const [_metric, setMetric] = useState<OptimiseMetric>("pnl");

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

  // Params for selected block
  const selectedNode = sweepableNodes.find((n) => n.id === selectedBlockId);
  const numericParams = selectedNode ? getNumericParams(selectedNode) : [];

  // Auto-select first block/param
  useEffect(() => {
    if (!selectedBlockId && sweepableNodes.length > 0) {
      setSelectedBlockId(sweepableNodes[0].id);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sweepableNodes.length]);

  useEffect(() => {
    if (numericParams.length > 0 && !numericParams.find((p) => p.id === selectedParamName)) {
      setSelectedParamName(numericParams[0].id);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBlockId, numericParams.length]);

  // ── Computed ────────────────────────────────────────────────────────────
  const runCount = rangeStep > 0 && rangeTo > rangeFrom
    ? Math.floor((rangeTo - rangeFrom) / rangeStep) + 1
    : 0;
  const runCountValid = runCount > 0 && runCount <= MAX_RUNS;
  const canSubmit = !!datasetId && !!versionId && !!selectedBlockId && !!selectedParamName && runCountValid && !submitting && !activeSweep;

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

    const body = {
      datasetId,
      strategyVersionId: versionId,
      sweepParam: {
        blockId: selectedBlockId,
        paramName: selectedParamName,
        from: rangeFrom,
        to: rangeTo,
        step: rangeStep,
      },
      feeBps,
      slippageBps,
    };

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
        results: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });
    } else {
      setSubmitError(res.problem.detail ?? res.problem.title ?? "Unknown error");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, versionId, selectedBlockId, selectedParamName, rangeFrom, rangeTo, rangeStep, feeBps, slippageBps]);

  // ── Sort results ────────────────────────────────────────────────────────
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sortedResults = activeSweep?.results
    ? [...activeSweep.results].sort((a, b) => {
        const aVal = a[sortKey] ?? 0;
        const bVal = b[sortKey] ?? 0;
        return sortDir === "asc" ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
      })
    : [];

  const bestId = activeSweep?.bestRow?.backtestResultId;

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
              Sweep complete — {activeSweep.runCount} runs. Best param: {activeSweep.bestRow?.paramValue ?? "—"}
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
                    {(
                      [
                        ["paramValue", "Param"],
                        ["pnlPct", "PnL %"],
                        ["winRate", "Win Rate"],
                        ["maxDrawdownPct", "Max DD %"],
                        ["tradeCount", "Trades"],
                        ["sharpe", "Sharpe"],
                      ] as [SortKey, string][]
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
                    const pnlColor = r.pnlPct >= 0 ? "#3fb950" : "#f85149";
                    return (
                      <tr
                        key={r.paramValue}
                        style={{
                          borderBottom: "1px solid rgba(255,255,255,0.04)",
                          background: isBest ? "rgba(212,164,76,0.08)" : "transparent",
                          borderLeft: isBest ? "3px solid #D4A44C" : "3px solid transparent",
                        }}
                      >
                        <td style={tdStyle}>{r.paramValue}</td>
                        <td style={{ ...tdStyle, color: pnlColor, fontWeight: 600 }}>{fmtPnl(r.pnlPct)}</td>
                        <td style={tdStyle}>{(r.winRate * 100).toFixed(1)}%</td>
                        <td style={tdStyle}>{r.maxDrawdownPct.toFixed(2)}%</td>
                        <td style={tdStyle}>{r.tradeCount}</td>
                        <td style={tdStyle}>{r.sharpe != null ? r.sharpe.toFixed(2) : "—"}</td>
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
          {/* Block selector */}
          <FormRow label="Target block">
            {sweepableNodes.length === 0 ? (
              <div style={emptyHintStyle}>No blocks with numeric parameters in the graph.</div>
            ) : (
              <select style={selectStyle} value={selectedBlockId} onChange={(e) => setSelectedBlockId(e.target.value)}>
                {sweepableNodes.map((n) => (
                  <option key={n.id} value={n.id}>{blockLabel(n)}</option>
                ))}
              </select>
            )}
          </FormRow>

          {/* Param selector */}
          <FormRow label="Parameter">
            {numericParams.length === 0 ? (
              <div style={emptyHintStyle}>Select a block with numeric parameters.</div>
            ) : (
              <select style={selectStyle} value={selectedParamName} onChange={(e) => setSelectedParamName(e.target.value)}>
                {numericParams.map((p) => (
                  <option key={p.id} value={p.id}>{p.label} (default: {String(p.defaultValue)})</option>
                ))}
              </select>
            )}
          </FormRow>

          {/* Range */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <FormRow label="From">
              <input type="number" style={inputStyle} value={rangeFrom} onChange={(e) => setRangeFrom(Number(e.target.value))} />
            </FormRow>
            <FormRow label="To">
              <input type="number" style={inputStyle} value={rangeTo} onChange={(e) => setRangeTo(Number(e.target.value))} />
            </FormRow>
            <FormRow label="Step">
              <input type="number" style={inputStyle} value={rangeStep} min={0.01} onChange={(e) => setRangeStep(Number(e.target.value))} />
            </FormRow>
          </div>

          <div style={hintStyle}>
            {runCountValid
              ? `${runCount} runs will be executed sequentially.`
              : runCount > MAX_RUNS
                ? `Too many runs (${runCount}). Max is ${MAX_RUNS}. Increase the step or narrow the range.`
                : "Invalid range. Ensure from < to and step > 0."}
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

          {/* Metric */}
          <FormRow label="Optimise for">
            <select style={selectStyle} value={_metric} onChange={(e) => setMetric(e.target.value as OptimiseMetric)}>
              <option value="pnl">Total PnL %</option>
              <option value="winRate">Win Rate</option>
              <option value="sharpe">Sharpe Ratio</option>
              <option value="maxDrawdown">Min Drawdown</option>
            </select>
          </FormRow>

          {submitError && <div style={errorBoxStyle}>{submitError}</div>}

          <button
            style={{ ...runBtnStyle, opacity: canSubmit ? 1 : 0.45, cursor: canSubmit ? "pointer" : "not-allowed" }}
            disabled={!canSubmit}
            onClick={handleSubmit}
          >
            {submitting ? "Starting sweep…" : `Run Sweep (${runCount} runs)`}
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
