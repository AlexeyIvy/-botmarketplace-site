"use client";

// ---------------------------------------------------------------------------
// Walk-forward validation panel (docs/48-T6).
// Mirrors the visual + polling structure of OptimisePanel.tsx.
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, getWorkspaceId } from "../../../lib/api";
import { useLabGraphStore } from "../useLabGraphStore";
import {
  DatasetBundleSelector,
  type DatasetBundle,
  type CandleInterval as BundleCandleInterval,
} from "../_shared/DatasetBundleSelector";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type FillAt = "OPEN" | "CLOSE" | "NEXT_OPEN";

const FILL_AT_LABELS: Record<FillAt, string> = {
  CLOSE: "On candle close (default)",
  OPEN: "On candle open",
  NEXT_OPEN: "Next candle open (lookahead-free)",
};

interface FoldRange {
  fromIndex: number;
  toIndex: number;
  fromTsMs: number;
  toTsMs: number;
}

interface FoldRow {
  foldIndex: number;
  isRange: FoldRange;
  oosRange: FoldRange;
  isReport: {
    trades: number;
    wins: number;
    winrate: number;
    totalPnlPct: number;
    maxDrawdownPct: number;
    candles: number;
    sharpe: number | null;
    profitFactor: number | null;
    expectancy: number | null;
  };
  oosReport: FoldRow["isReport"];
}

interface WalkForwardAggregate {
  foldCount: number;
  avgIsPnlPct: number;
  avgOosPnlPct: number;
  totalOosPnlPct: number;
  avgIsSharpe: number | null;
  avgOosSharpe: number | null;
  isOosPnlRatio: number | null;
  oosWinFoldShare: number;
}

interface WalkForwardRunStatus {
  id: string;
  status: "pending" | "running" | "done" | "failed";
  progress: number; // 0..1
  foldCount: number;
  foldConfig: { isBars: number; oosBars: number; step: number; anchored: boolean };
  folds: FoldRow[] | null;
  aggregate: WalkForwardAggregate | null;
  error: string | null;
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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 2000;
const MAX_FOLDS = 20;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtPnl(pct: number): string {
  return (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%";
}

function fmtRange(r: FoldRange): string {
  return `[${r.fromIndex}…${r.toIndex})`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function WalkForwardPanel({
  datasets,
  strategyVersions,
}: {
  datasets: DatasetListItem[];
  strategyVersions: StrategyVersionItem[];
}) {
  const activeDatasetId = useLabGraphStore((s) => s.activeDatasetId);
  const lastCompileResult = useLabGraphStore((s) => s.lastCompileResult);
  const lastCompileVersionId = lastCompileResult?.strategyVersionId ?? null;

  const readyDatasets = datasets.filter((d) => d.status === "READY" || d.status === "PARTIAL");

  // Form state
  const [datasetId, setDatasetId] = useState(activeDatasetId ?? readyDatasets[0]?.datasetId ?? "");
  const [versionId, setVersionId] = useState(lastCompileVersionId ?? strategyVersions[0]?.id ?? "");
  const [isBars, setIsBars] = useState(400);
  const [oosBars, setOosBars] = useState(100);
  const [step, setStep] = useState(100);
  const [anchored, setAnchored] = useState(false);
  const [feeBps, setFeeBps] = useState(10);
  const [slippageBps, setSlippageBps] = useState(5);
  const [fillAt, setFillAt] = useState<FillAt>("CLOSE");
  const [bundle, setBundle] = useState<DatasetBundle | null>(null);

  // Reset bundle when the primary dataset changes — its (symbol, interval)
  // anchors the bundle, so any extra TFs become inconsistent (docs/52-T5b).
  useEffect(() => { setBundle(null); }, [datasetId]);

  // Run state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [activeRun, setActiveRun] = useState<WalkForwardRunStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync defaults
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

  // Local fold-count preview — same formula as the server's split() so the UI
  // can reject impossible configs before round-tripping.
  const selectedDataset = useMemo(
    () => readyDatasets.find((d) => d.datasetId === datasetId) ?? null,
    [readyDatasets, datasetId],
  );
  const candleCount = selectedDataset?.candleCount ?? 0;
  const previewFoldCount = useMemo(() => {
    if (isBars <= 0 || oosBars <= 0 || step <= 0) return 0;
    if (candleCount < isBars + oosBars) return 0;
    return Math.floor((candleCount - isBars - oosBars) / step) + 1;
  }, [candleCount, isBars, oosBars, step]);

  const overlapWarning = step < oosBars
    ? "step < oosBars — adjacent OOS blocks overlap"
    : null;

  const previewValid = previewFoldCount >= 1 && previewFoldCount <= MAX_FOLDS;
  const canSubmit = !!datasetId && !!versionId && previewValid && !submitting && !activeRun;

  // Polling
  const pollRun = useCallback(async (id: string) => {
    const res = await apiFetch<WalkForwardRunStatus>(`/lab/backtest/walk-forward/${id}`);
    if (!res.ok) return null;
    setActiveRun(res.data);
    return res.data;
  }, []);

  useEffect(() => {
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
    if (!activeRun) return;
    if (activeRun.status !== "pending" && activeRun.status !== "running") return;

    const schedule = () => {
      pollRef.current = setTimeout(async () => {
        const updated = await pollRun(activeRun.id);
        if (updated?.status === "pending" || updated?.status === "running") schedule();
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
  }, [activeRun?.id, activeRun?.status]);

  // Submit
  const handleSubmit = useCallback(async () => {
    if (!getWorkspaceId()) return;
    setSubmitting(true);
    setSubmitError(null);
    setWarnings([]);

    const body: Record<string, unknown> = {
      datasetId,
      strategyVersionId: versionId,
      fold: { isBars, oosBars, step, anchored },
      feeBps,
      slippageBps,
      fillAt,
    };
    if (bundle) body.datasetBundleJson = bundle;

    const res = await apiFetch<{ id: string; foldCount: number; status: string; warnings: string[] }>(
      "/lab/backtest/walk-forward",
      { method: "POST", body: JSON.stringify(body) },
    );

    setSubmitting(false);

    if (res.ok) {
      setWarnings(res.data.warnings ?? []);
      setActiveRun({
        id: res.data.id,
        status: "pending",
        progress: 0,
        foldCount: res.data.foldCount,
        foldConfig: { isBars, oosBars, step, anchored },
        folds: null,
        aggregate: null,
        error: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });
    } else {
      setSubmitError(res.problem.detail ?? res.problem.title ?? "Unknown error");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, versionId, isBars, oosBars, step, anchored, feeBps, slippageBps, fillAt, bundle]);

  return (
    <div style={{ padding: "20px 24px", maxWidth: 900, overflow: "auto", height: "100%" }}>
      <h3 style={titleStyle}>Walk-forward validation</h3>

      {/* Active run */}
      {activeRun && (
        <div>
          {(activeRun.status === "pending" || activeRun.status === "running") && (
            <div style={progressBarContainerStyle}>
              <div style={{ ...progressBarFillStyle, width: `${(activeRun.progress * 100).toFixed(1)}%` }} />
              <span style={progressTextStyle}>
                {(activeRun.progress * 100).toFixed(0)}% · {activeRun.foldCount} folds ({activeRun.status})
              </span>
            </div>
          )}

          {activeRun.status === "done" && activeRun.aggregate && (
            <div style={doneBannerStyle}>
              Walk-forward complete — {activeRun.aggregate.foldCount} folds.
            </div>
          )}

          {activeRun.status === "failed" && (
            <div style={errorBoxStyle}>
              Walk-forward failed{activeRun.error ? `: ${activeRun.error}` : "."}
            </div>
          )}

          {warnings.length > 0 && (
            <div style={warningBoxStyle}>
              <strong>Warnings:</strong>
              <ul style={{ margin: "4px 0 0 18px", padding: 0 }}>
                {warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          {activeRun.aggregate && (
            <div style={aggregateGridStyle}>
              <AggregateCell label="Avg IS PnL %"     value={fmtPnl(activeRun.aggregate.avgIsPnlPct)} />
              <AggregateCell label="Avg OOS PnL %"    value={fmtPnl(activeRun.aggregate.avgOosPnlPct)} />
              <AggregateCell label="Total OOS PnL %"  value={fmtPnl(activeRun.aggregate.totalOosPnlPct)} />
              <AggregateCell label="OOS win share"    value={`${(activeRun.aggregate.oosWinFoldShare * 100).toFixed(0)}%`} />
              <AggregateCell label="OOS / IS ratio"   value={activeRun.aggregate.isOosPnlRatio !== null ? activeRun.aggregate.isOosPnlRatio.toFixed(2) : "—"} />
              <AggregateCell label="Avg IS Sharpe"    value={activeRun.aggregate.avgIsSharpe !== null ? activeRun.aggregate.avgIsSharpe.toFixed(2) : "—"} />
              <AggregateCell label="Avg OOS Sharpe"   value={activeRun.aggregate.avgOosSharpe !== null ? activeRun.aggregate.avgOosSharpe.toFixed(2) : "—"} />
              <AggregateCell label="Folds"            value={String(activeRun.aggregate.foldCount)} />
            </div>
          )}

          {activeRun.folds && activeRun.folds.length > 0 && (
            <div style={{ overflow: "auto", marginTop: 12 }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={theadRowStyle}>
                    <th style={thStyle}>Fold</th>
                    <th style={thStyle}>IS</th>
                    <th style={thStyle}>OOS</th>
                    <th style={thStyle}>IS PnL %</th>
                    <th style={thStyle}>OOS PnL %</th>
                    <th style={thStyle}>OOS win rate</th>
                    <th style={thStyle}>OOS max DD %</th>
                    <th style={thStyle}>OOS Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {activeRun.folds.map((f) => (
                    <tr key={f.foldIndex} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <td style={tdStyle}>{f.foldIndex}</td>
                      <td style={tdStyle}>{fmtRange(f.isRange)}</td>
                      <td style={tdStyle}>{fmtRange(f.oosRange)}</td>
                      <td style={{ ...tdStyle, color: f.isReport.totalPnlPct >= 0 ? "#3fb950" : "#f85149" }}>
                        {fmtPnl(f.isReport.totalPnlPct)}
                      </td>
                      <td style={{ ...tdStyle, color: f.oosReport.totalPnlPct >= 0 ? "#3fb950" : "#f85149", fontWeight: 600 }}>
                        {fmtPnl(f.oosReport.totalPnlPct)}
                      </td>
                      <td style={tdStyle}>{(f.oosReport.winrate * 100).toFixed(1)}%</td>
                      <td style={tdStyle}>{f.oosReport.maxDrawdownPct.toFixed(2)}%</td>
                      <td style={tdStyle}>{f.oosReport.sharpe !== null ? f.oosReport.sharpe.toFixed(2) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {(activeRun.status === "done" || activeRun.status === "failed") && (
            <button
              style={{ ...runBtnStyle, marginTop: 14, background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.7)" }}
              onClick={() => { setActiveRun(null); setWarnings([]); }}
            >
              New walk-forward run
            </button>
          )}
        </div>
      )}

      {/* Form */}
      {!activeRun && (
        <>
          <FormRow label="Dataset">
            {readyDatasets.length === 0 ? (
              <div style={emptyHintStyle}>No ready datasets. Create one in the Data tab.</div>
            ) : (
              <select style={selectStyle} value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
                {readyDatasets.map((d) => (
                  <option key={d.datasetId} value={d.datasetId}>
                    {d.name ?? `${d.symbol} · ${d.interval}`} · {d.candleCount} candles
                  </option>
                ))}
              </select>
            )}
          </FormRow>

          {/* Multi-interval bundle (docs/52-T5b). Bundle is persisted on
              WalkForwardRun.datasetBundleJson; the fold runner currently
              ignores it (deferred follow-up). */}
          {selectedDataset && (
            <FormRow label="Multi-TF context">
              <DatasetBundleSelector
                primaryInterval={selectedDataset.interval as BundleCandleInterval}
                primaryDatasetId={selectedDataset.datasetId}
                primarySymbol={selectedDataset.symbol}
                availableDatasets={readyDatasets}
                bundle={bundle}
                onChange={setBundle}
                disabled={submitting}
              />
            </FormRow>
          )}

          <FormRow label="Strategy version">
            {strategyVersions.length === 0 ? (
              <div style={emptyHintStyle}>No compiled versions. Compile a graph in the Build tab first.</div>
            ) : (
              <select style={selectStyle} value={versionId} onChange={(e) => setVersionId(e.target.value)}>
                {strategyVersions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.strategy.name} v{v.version} · {v.strategy.symbol}
                  </option>
                ))}
              </select>
            )}
          </FormRow>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <FormRow label="IS bars">
              <input type="number" style={inputStyle} value={isBars} min={1} step={1} onChange={(e) => setIsBars(Number(e.target.value))} />
            </FormRow>
            <FormRow label="OOS bars">
              <input type="number" style={inputStyle} value={oosBars} min={1} step={1} onChange={(e) => setOosBars(Number(e.target.value))} />
            </FormRow>
            <FormRow label="Step">
              <input type="number" style={inputStyle} value={step} min={1} step={1} onChange={(e) => setStep(Number(e.target.value))} />
            </FormRow>
          </div>

          <FormRow label="Layout">
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "rgba(255,255,255,0.85)" }}>
              <input type="checkbox" checked={anchored} onChange={(e) => setAnchored(e.target.checked)} />
              Anchored — keep IS start at 0 and grow
            </label>
          </FormRow>

          <div style={hintStyle}>
            {previewFoldCount === 0
              ? `Need at least ${isBars + oosBars} candles; selected dataset has ${candleCount}.`
              : previewFoldCount > MAX_FOLDS
                ? `Too many folds (${previewFoldCount}). Max is ${MAX_FOLDS}. Increase step or shrink the window.`
                : `${previewFoldCount} fold${previewFoldCount === 1 ? "" : "s"} will be evaluated sequentially.`}
            {overlapWarning && <div style={{ color: "#d29922", marginTop: 4 }}>{overlapWarning}</div>}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <FormRow label="Fee (bps)">
              <input type="number" style={inputStyle} value={feeBps} min={0} max={1000} step={1} onChange={(e) => setFeeBps(Number(e.target.value))} />
            </FormRow>
            <FormRow label="Slippage (bps)">
              <input type="number" style={inputStyle} value={slippageBps} min={0} max={1000} step={1} onChange={(e) => setSlippageBps(Number(e.target.value))} />
            </FormRow>
          </div>

          <FormRow label="Fill price (execution model)">
            <select style={selectStyle} value={fillAt} onChange={(e) => setFillAt(e.target.value as FillAt)}>
              {(Object.keys(FILL_AT_LABELS) as FillAt[]).map((k) => (
                <option key={k} value={k}>{FILL_AT_LABELS[k]}</option>
              ))}
            </select>
          </FormRow>

          {submitError && <div style={errorBoxStyle}>{submitError}</div>}

          <button
            style={{ ...runBtnStyle, opacity: canSubmit ? 1 : 0.45, cursor: canSubmit ? "pointer" : "not-allowed" }}
            disabled={!canSubmit}
            onClick={handleSubmit}
          >
            {submitting
              ? "Starting walk-forward…"
              : `Run walk-forward (${previewFoldCount} fold${previewFoldCount === 1 ? "" : "s"})`}
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

function AggregateCell({ label, value }: { label: string; value: string }) {
  return (
    <div style={aggregateCellStyle}>
      <div style={aggregateCellLabelStyle}>{label}</div>
      <div style={aggregateCellValueStyle}>{value}</div>
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
  color: "rgba(255,255,255,0.4)",
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

const warningBoxStyle: React.CSSProperties = {
  background: "rgba(210,153,34,0.12)",
  border: "1px solid rgba(210,153,34,0.35)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#d29922",
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

const aggregateGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(4, 1fr)",
  gap: 8,
  margin: "12px 0",
};

const aggregateCellStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 6,
  padding: "8px 10px",
};

const aggregateCellLabelStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  color: "rgba(255,255,255,0.4)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  marginBottom: 4,
};

const aggregateCellValueStyle: React.CSSProperties = {
  fontSize: 14,
  color: "rgba(255,255,255,0.92)",
  fontFamily: "monospace",
  fontWeight: 600,
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
