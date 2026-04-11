"use client";

// ---------------------------------------------------------------------------
// /lab/test — Phase 5A + 5B: Backtest runner + results
// Per docs/23-lab-v2-ide-spec.md §6.5, Phase 5A + 5B
//
// Phase 5A: backtest form (select dataset + strategyVersion + feeBps + slippageBps)
//           POST /api/v1/lab/backtest, poll every 2s, metrics tab on completion
// Phase 5B: Trades tab, Equity curve tab, Logs tab, Dataset snapshot block (§6.5)
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, getWorkspaceId } from "../../../lib/api";
import { useLabGraphStore } from "../useLabGraphStore";
import type { IChartApi, LineData, Time } from "lightweight-charts";
import OptimisePanel from "./OptimisePanel";

type TopTab = "backtest" | "optimise";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type BacktestStatus = "PENDING" | "RUNNING" | "DONE" | "FAILED";

interface BacktestListItem {
  id: string;
  strategyId: string;
  strategyVersionId: string | null;
  datasetId: string | null;
  datasetHash: string | null;
  symbol: string;
  interval: string;
  fromTs: string;
  toTs: string;
  status: BacktestStatus;
  feeBps: number;
  slippageBps: number;
  fillAt: string;
  engineVersion: string;
  reportJson: BacktestReport | null;
  errorMessage: string | null;
  createdAt: string;
}

interface BacktestReport {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
  tradeLog: TradeRecord[];
}

interface TradeRecord {
  entryTime: number;
  exitTime: number;
  entryPrice: number;
  exitPrice: number;
  slPrice: number;
  tpPrice: number;
  outcome: "WIN" | "LOSS" | "NEUTRAL";
  pnlPct: number;
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtDate(ms: number): string {
  return new Date(ms).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" });
}

function fmtPnl(pct: number): string {
  return (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%";
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: BacktestStatus }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    PENDING: { bg: "rgba(100,100,120,0.18)", fg: "rgba(255,255,255,0.45)" },
    RUNNING: { bg: "rgba(59,130,246,0.18)",  fg: "#60a5fa" },
    DONE:    { bg: "rgba(63,185,80,0.15)",   fg: "#3fb950" },
    FAILED:  { bg: "rgba(248,81,73,0.15)",   fg: "#f85149" },
  };
  const c = colors[status] ?? colors.PENDING;
  return (
    <span style={{
      background: c.bg, color: c.fg,
      padding: "2px 7px", borderRadius: 4,
      fontSize: 10, fontWeight: 700, letterSpacing: "0.06em",
      textTransform: "uppercase",
    }}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Phase 6 (23b2) — Stale-state badge
// Shown when a backtest was run against a strategy version that is no longer
// the latest compiled version. Logic: bt.strategyVersionId !== lastCompileResult.strategyVersionId
// ---------------------------------------------------------------------------

function StaleBadge({ bt, lastCompileVersionId }: { bt: BacktestListItem; lastCompileVersionId: string | null }) {
  if (!lastCompileVersionId) return null;
  if (!bt.strategyVersionId) return null;
  if (bt.strategyVersionId === lastCompileVersionId) return null;
  return (
    <span
      title="This backtest was run against an older strategy version. Re-run to get up-to-date results."
      style={{
        background: "rgba(251,191,36,0.15)",
        color: "#fbbf24",
        padding: "2px 6px",
        borderRadius: 4,
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        marginLeft: 4,
      }}
    >
      STALE
    </span>
  );
}

// ---------------------------------------------------------------------------
// Dataset snapshot block — §6.5
// Shown at top of Results drawer
// ---------------------------------------------------------------------------

function DatasetSnapshotBlock({
  bt,
  datasets,
}: {
  bt: BacktestListItem;
  datasets: DatasetListItem[];
}) {
  const ds = datasets.find((d) => d.datasetId === bt.datasetId);

  return (
    <div style={snapshotBlockStyle}>
      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em", color: "rgba(255,255,255,0.35)", marginBottom: 8 }}>
        Dataset Snapshot
      </div>
      <div style={snapshotGridStyle}>
        <SnapRow label="Dataset ID"     value={bt.datasetId ? bt.datasetId.slice(0, 12) + "…" : "—"} mono />
        <SnapRow label="Hash"           value={bt.datasetHash ? bt.datasetHash.slice(0, 8) : "—"} mono />
        <SnapRow label="Symbol"         value={bt.symbol} />
        <SnapRow label="Interval"       value={bt.interval} />
        {ds && <SnapRow label="Candles"        value={ds.candleCount.toLocaleString()} />}
        {ds && <SnapRow label="Fetched at"     value={new Date(ds.fetchedAt).toLocaleDateString()} />}
        <SnapRow label="feeBps"         value={String(bt.feeBps)} />
        <SnapRow label="slippageBps"    value={String(bt.slippageBps)} />
        <SnapRow label="fillAt"         value={bt.fillAt} />
        <SnapRow label="Engine"         value={bt.engineVersion} mono />
      </div>
    </div>
  );
}

function SnapRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", gap: 8, padding: "3px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", width: 100, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.75)", fontFamily: mono ? "monospace" : undefined, wordBreak: "break-all" }}>{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metrics tab
// ---------------------------------------------------------------------------

function MetricsTab({ report }: { report: BacktestReport }) {
  const pnlColor = report.totalPnlPct >= 0 ? "#3fb950" : "#f85149";
  return (
    <div style={{ padding: "20px 24px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
        <MetricCard label="Total PnL" value={fmtPnl(report.totalPnlPct)} color={pnlColor} />
        <MetricCard label="Win Rate"  value={`${(report.winrate * 100).toFixed(1)}%`} />
        <MetricCard label="Max Drawdown" value={`-${report.maxDrawdownPct.toFixed(2)}%`} color={report.maxDrawdownPct > 5 ? "#f85149" : undefined} />
        <MetricCard label="Trades"    value={String(report.trades)} />
      </div>
      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
        {report.wins} wins · {report.trades - report.wins} losses · {report.candles.toLocaleString()} candles processed
      </div>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.07)",
      borderRadius: 8,
      padding: "14px 16px",
    }}>
      <div style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "rgba(255,255,255,0.35)", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: color ?? "rgba(255,255,255,0.88)", fontFamily: "monospace" }}>
        {value}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Trades tab
// ---------------------------------------------------------------------------

function TradesTab({ tradeLog }: { tradeLog: TradeRecord[] }) {
  if (tradeLog.length === 0) {
    return (
      <div style={{ padding: "24px", fontSize: 13, color: "rgba(255,255,255,0.35)" }}>
        No trades in this backtest.
      </div>
    );
  }

  return (
    <div style={{ overflow: "auto", height: "100%" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            {["#", "Entry time", "Exit time", "Entry price", "Exit price", "PnL %", "Outcome"].map((h) => (
              <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", color: "rgba(255,255,255,0.4)", whiteSpace: "nowrap" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tradeLog.map((t, i) => {
            const pnlColor = t.outcome === "WIN" ? "#3fb950" : t.outcome === "LOSS" ? "#f85149" : "rgba(255,255,255,0.45)";
            return (
              <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                <td style={tdStyle}>{i + 1}</td>
                <td style={tdStyle}>{fmtDate(t.entryTime)}</td>
                <td style={tdStyle}>{fmtDate(t.exitTime)}</td>
                <td style={{ ...tdStyle, fontFamily: "monospace" }}>{t.entryPrice.toFixed(2)}</td>
                <td style={{ ...tdStyle, fontFamily: "monospace" }}>{t.exitPrice.toFixed(2)}</td>
                <td style={{ ...tdStyle, color: pnlColor, fontFamily: "monospace", fontWeight: 600 }}>{fmtPnl(t.pnlPct)}</td>
                <td style={{ ...tdStyle, color: pnlColor, fontWeight: 700, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>{t.outcome}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const tdStyle: React.CSSProperties = {
  padding: "7px 12px",
  color: "rgba(255,255,255,0.72)",
  whiteSpace: "nowrap",
};

// ---------------------------------------------------------------------------
// Equity curve tab — lightweight-charts line chart
// ---------------------------------------------------------------------------

function EquityTab({ tradeLog }: { tradeLog: TradeRecord[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let chart: IChartApi | null = null;

    // Dynamic import to avoid SSR issues
    import("lightweight-charts").then(({ createChart, ColorType, LineStyle, LineSeries: LcLineSeries }) => {
      if (!containerRef.current) return;

      chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
        layout: {
          background: { type: ColorType.Solid, color: "rgba(8,12,18,0)" },
          textColor: "rgba(255,255,255,0.5)",
        },
        grid: {
          vertLines: { color: "rgba(255,255,255,0.05)" },
          horzLines: { color: "rgba(255,255,255,0.05)" },
        },
        crosshair: {
          vertLine: { color: "rgba(255,255,255,0.3)", style: LineStyle.Dotted },
          horzLine: { color: "rgba(255,255,255,0.3)", style: LineStyle.Dotted },
        },
        rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" },
        timeScale: { borderColor: "rgba(255,255,255,0.1)", timeVisible: true },
      });

      chartRef.current = chart;

      const lineSeries = chart.addSeries(LcLineSeries, {
        color: "#3b82f6",
        lineWidth: 2,
        priceFormat: { type: "percent" },
      });

      // Build cumulative PnL equity curve from tradeLog
      let cumPnl = 0;
      const points: LineData[] = [
        { time: (tradeLog[0]?.entryTime ?? Date.now()) / 1000 as Time, value: 0 },
      ];
      for (const t of tradeLog) {
        cumPnl += t.pnlPct;
        points.push({ time: t.exitTime / 1000 as Time, value: cumPnl });
      }
      lineSeries.setData(points);
      chart.timeScale().fitContent();
    });

    const resizeObs = new ResizeObserver(() => {
      if (chartRef.current && containerRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    });
    if (containerRef.current) resizeObs.observe(containerRef.current);

    return () => {
      resizeObs.disconnect();
      chart?.remove();
      chartRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (tradeLog.length === 0) {
    return (
      <div style={{ padding: "24px", fontSize: 13, color: "rgba(255,255,255,0.35)" }}>
        No trades — equity curve unavailable.
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: "100%", height: "100%", minHeight: 220 }} />;
}

// ---------------------------------------------------------------------------
// Logs tab — structured event log from BacktestReport trades
// ---------------------------------------------------------------------------

function LogsTab({ report }: { report: BacktestReport }) {
  const events = [
    { time: null, msg: `Backtest started. Processing ${report.candles.toLocaleString()} candles.` },
    ...report.tradeLog.map((t, i) => ({
      time: t.entryTime,
      msg: `Trade ${i + 1}: ${t.outcome} — entry ${t.entryPrice.toFixed(2)} → exit ${t.exitPrice.toFixed(2)} (${fmtPnl(t.pnlPct)})`,
      outcome: t.outcome,
    })),
    { time: null, msg: `Backtest complete. ${report.trades} trades, winrate ${(report.winrate * 100).toFixed(1)}%, PnL ${fmtPnl(report.totalPnlPct)}.` },
  ];

  return (
    <div style={{ overflow: "auto", height: "100%", padding: "12px 16px", fontFamily: "monospace" }}>
      {events.map((e, i) => {
        const color =
          "outcome" in e && e.outcome === "WIN"  ? "#3fb950" :
          "outcome" in e && e.outcome === "LOSS" ? "#f85149" :
          "rgba(255,255,255,0.6)";
        return (
          <div key={i} style={{ display: "flex", gap: 10, padding: "3px 0", fontSize: 11 }}>
            <span style={{ color: "rgba(255,255,255,0.25)", flexShrink: 0, minWidth: 120 }}>
              {e.time ? fmtDate(e.time) : "—"}
            </span>
            <span style={{ color }}>{e.msg}</span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Backtest form
// ---------------------------------------------------------------------------

function BacktestForm({
  datasets,
  strategyVersions,
  onSubmit,
  submitting,
  error,
  activeDatasetId,
  lastCompileVersionId,
}: {
  datasets: DatasetListItem[];
  strategyVersions: StrategyVersionItem[];
  onSubmit: (params: { strategyVersionId: string; datasetId: string; feeBps: number; slippageBps: number }) => void;
  submitting: boolean;
  error: string | null;
  activeDatasetId: string | null;
  lastCompileVersionId: string | null;
}) {
  const readyDatasets = datasets.filter((d) => d.status === "READY" || d.status === "PARTIAL");

  const [datasetId, setDatasetId] = useState(activeDatasetId ?? readyDatasets[0]?.datasetId ?? "");
  const [versionId, setVersionId] = useState(lastCompileVersionId ?? strategyVersions[0]?.id ?? "");
  const [feeBps, setFeeBps] = useState(10);
  const [slippageBps, setSlippageBps] = useState(5);

  // Sync default dataset when props change
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

  const canSubmit = !!datasetId && !!versionId && !submitting;

  const selectedVersion = strategyVersions.find((v) => v.id === versionId);
  const selectedDataset = datasets.find((d) => d.datasetId === datasetId);

  return (
    <div style={{ padding: "20px 24px", maxWidth: 480 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: "rgba(255,255,255,0.88)", marginBottom: 18 }}>
        Run Backtest
      </h3>

      {/* Dataset select */}
      <FormRow label="Dataset">
        {readyDatasets.length === 0 ? (
          <div style={emptyHintStyle}>No ready datasets. Create one in the Data tab.</div>
        ) : (
          <select style={selectStyle} value={datasetId} onChange={(e) => setDatasetId(e.target.value)} disabled={submitting}>
            {readyDatasets.map((d) => (
              <option key={d.datasetId} value={d.datasetId}>
                {d.name ?? `${d.symbol} · ${d.interval}`} ({new Date(Number(d.fromTsMs)).toLocaleDateString()} → {new Date(Number(d.toTsMs)).toLocaleDateString()})
              </option>
            ))}
          </select>
        )}
        {selectedDataset && (
          <div style={hintStyle}>{selectedDataset.candleCount.toLocaleString()} candles · hash {selectedDataset.datasetHash.slice(0, 8)}</div>
        )}
      </FormRow>

      {/* Strategy version select */}
      <FormRow label="Strategy version">
        {strategyVersions.length === 0 ? (
          <div style={emptyHintStyle}>No compiled versions. Compile a graph in the Build tab first.</div>
        ) : (
          <select style={selectStyle} value={versionId} onChange={(e) => setVersionId(e.target.value)} disabled={submitting}>
            {strategyVersions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.strategy.name} v{v.version} · {v.strategy.symbol} · {new Date(v.createdAt).toLocaleDateString()}
              </option>
            ))}
          </select>
        )}
        {selectedVersion && (
          <div style={hintStyle}>ID: {selectedVersion.id.slice(0, 12)}…</div>
        )}
      </FormRow>

      {/* Fee + slippage */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <FormRow label="Fee (bps)">
          <input
            type="number"
            style={inputStyle}
            value={feeBps}
            min={0}
            max={1000}
            step={1}
            onChange={(e) => setFeeBps(Number(e.target.value))}
            disabled={submitting}
          />
          <div style={hintStyle}>{(feeBps / 100).toFixed(2)}%</div>
        </FormRow>
        <FormRow label="Slippage (bps)">
          <input
            type="number"
            style={inputStyle}
            value={slippageBps}
            min={0}
            max={1000}
            step={1}
            onChange={(e) => setSlippageBps(Number(e.target.value))}
            disabled={submitting}
          />
          <div style={hintStyle}>{(slippageBps / 100).toFixed(2)}%</div>
        </FormRow>
      </div>

      {error && <div style={errorBoxStyle}>{error}</div>}

      <button
        style={{
          ...runBtnStyle,
          opacity: canSubmit ? 1 : 0.45,
          cursor: canSubmit ? "pointer" : "not-allowed",
        }}
        disabled={!canSubmit}
        onClick={() => onSubmit({ strategyVersionId: versionId, datasetId, feeBps, slippageBps })}
      >
        {submitting ? "Starting…" : "Run Backtest"}
      </button>

      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", marginTop: 8 }}>
        Fill price: CLOSE (fixed per spec). Same inputs produce identical results.
      </div>
    </div>
  );
}

function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={formLabelStyle}>{label}</label>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Phase 6 (23b1) — Compare Runs Tab
// ---------------------------------------------------------------------------

interface LineageInfo {
  graphVersionId: string;
  graphVersion: number;
  label: string | null;
  isBaseline: boolean;
  graphName: string;
}

interface CompareRunItem extends BacktestListItem {
  lineage?: LineageInfo | null;
}

interface CompareResult {
  a: CompareRunItem;
  b: CompareRunItem;
  delta: {
    pnlDelta: number | null;
    winrateDelta: number | null;
    drawdownDelta: number | null;
    tradeDelta: number | null;
    sharpeDelta: number | null;
  };
}

function CompareRunsTab({ runs, currentRunId, lastCompileVersionId }: { runs: BacktestListItem[]; currentRunId: string | null; lastCompileVersionId: string | null }) {
  const [idA, setIdA] = useState<string>(currentRunId ?? runs[0]?.id ?? "");
  const [idB, setIdB] = useState<string>(() => {
    const other = runs.find((r) => r.id !== (currentRunId ?? runs[0]?.id));
    return other?.id ?? runs[1]?.id ?? "";
  });
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = useCallback(async (a: string, b: string) => {
    if (!a || !b || a === b) { setResult(null); return; }
    setLoading(true);
    setError(null);
    const res = await apiFetch<CompareResult>(`/lab/backtests/compare?a=${a}&b=${b}`);
    setLoading(false);
    if (res.ok) { setResult(res.data); }
    else { setError("Failed to load comparison"); setResult(null); }
  }, []);

  useEffect(() => { fetchComparison(idA, idB); }, [idA, idB, fetchComparison]);

  const fmt = (v: number | null | undefined, suffix = "%") => {
    if (v === null || v === undefined) return "—";
    return `${v >= 0 ? "+" : ""}${v.toFixed(2)}${suffix}`;
  };
  const fmtInt = (v: number | null | undefined) => {
    if (v === null || v === undefined) return "—";
    return `${v >= 0 ? "+" : ""}${v}`;
  };
  const deltaColor = (v: number | null | undefined, invert = false) => {
    if (v === null || v === undefined) return "rgba(255,255,255,0.4)";
    const positive = invert ? v < 0 : v > 0;
    return positive ? "#4ade80" : v === 0 ? "rgba(255,255,255,0.4)" : "#f87171";
  };

  const runLabel = (r: BacktestListItem) => {
    const date = new Date(r.createdAt).toLocaleDateString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
    return `${r.symbol} ${r.interval} — ${date}`;
  };

  const reportA = result?.a.reportJson as BacktestReport | null;
  const reportB = result?.b.reportJson as BacktestReport | null;

  const metrics: { label: string; a: string; b: string; delta: string; deltaColor: string }[] = result ? [
    { label: "Total PnL", a: fmt(reportA?.totalPnlPct), b: fmt(reportB?.totalPnlPct), delta: fmt(result.delta.pnlDelta), deltaColor: deltaColor(result.delta.pnlDelta) },
    { label: "Win Rate", a: fmt(reportA?.winrate), b: fmt(reportB?.winrate), delta: fmt(result.delta.winrateDelta), deltaColor: deltaColor(result.delta.winrateDelta) },
    { label: "Max Drawdown", a: fmt(reportA?.maxDrawdownPct), b: fmt(reportB?.maxDrawdownPct), delta: fmt(result.delta.drawdownDelta), deltaColor: deltaColor(result.delta.drawdownDelta, true) },
    { label: "Trades", a: String(reportA?.trades ?? "—"), b: String(reportB?.trades ?? "—"), delta: fmtInt(result.delta.tradeDelta), deltaColor: deltaColor(result.delta.tradeDelta) },
    { label: "Fee (bps)", a: String(result.a.feeBps), b: String(result.b.feeBps), delta: "", deltaColor: "transparent" },
    { label: "Engine", a: result.a.engineVersion?.slice(0, 8) ?? "—", b: result.b.engineVersion?.slice(0, 8) ?? "—", delta: "", deltaColor: "transparent" },
  ] : [];

  return (
    <div style={{ padding: 16 }}>
      {/* Run selectors */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <label style={compareLabelStyle}>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", marginBottom: 4 }}>Run A</span>
          <select value={idA} onChange={(e) => setIdA(e.target.value)} style={compareSelectStyle}>
            {runs.map((r) => <option key={r.id} value={r.id}>{runLabel(r)}</option>)}
          </select>
        </label>
        <label style={compareLabelStyle}>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", marginBottom: 4 }}>Run B</span>
          <select value={idB} onChange={(e) => setIdB(e.target.value)} style={compareSelectStyle}>
            {runs.map((r) => <option key={r.id} value={r.id}>{runLabel(r)}</option>)}
          </select>
        </label>
      </div>

      {idA === idB && <div style={{ color: "#fbbf24", fontSize: 12, marginBottom: 12 }}>Select two different runs to compare.</div>}
      {loading && <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>Loading comparison...</div>}
      {error && <div style={{ color: "#f87171", fontSize: 12 }}>{error}</div>}

      {/* Provenance blocks */}
      {result && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
          <ProvenanceBlock label="Run A" bt={result.a} lastCompileVersionId={lastCompileVersionId} lineage={result.a.lineage} />
          <ProvenanceBlock label="Run B" bt={result.b} lastCompileVersionId={lastCompileVersionId} lineage={result.b.lineage} />
        </div>
      )}

      {/* Metrics comparison table */}
      {result && metrics.length > 0 && (
        <table style={compareTableStyle}>
          <thead>
            <tr>
              <th style={compareTh}>Metric</th>
              <th style={compareTh}>Run A</th>
              <th style={compareTh}>Run B</th>
              <th style={compareTh}>Delta</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => (
              <tr key={m.label}>
                <td style={compareTd}>{m.label}</td>
                <td style={compareTdVal}>{m.a}</td>
                <td style={compareTdVal}>{m.b}</td>
                <td style={{ ...compareTdVal, color: m.deltaColor, fontWeight: 600 }}>{m.delta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function ProvenanceBlock({ label, bt, lastCompileVersionId, lineage }: { label: string; bt: BacktestListItem; lastCompileVersionId: string | null; lineage?: LineageInfo | null }) {
  const isStale = lastCompileVersionId && bt.strategyVersionId && bt.strategyVersionId !== lastCompileVersionId;
  return (
    <div style={{ ...provenanceStyle, ...(isStale ? { borderColor: "rgba(251,191,36,0.3)" } : {}), ...(lineage?.isBaseline ? { borderColor: "rgba(251,191,36,0.4)" } : {}) }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <span style={{ fontWeight: 700, fontSize: 11, color: "#3b82f6" }}>{label}</span>
        {isStale && (
          <span style={{ fontSize: 9, fontWeight: 700, color: "#fbbf24", background: "rgba(251,191,36,0.15)", padding: "1px 5px", borderRadius: 3, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            STALE
          </span>
        )}
        {lineage?.isBaseline && (
          <span style={{ fontSize: 9, fontWeight: 700, color: "#fbbf24", background: "rgba(251,191,36,0.15)", padding: "1px 5px", borderRadius: 3, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            BASELINE
          </span>
        )}
      </div>
      {lineage?.graphName && <div style={provenanceRow}><span>Graph</span><span>{lineage.graphName}</span></div>}
      {lineage?.label && <div style={provenanceRow}><span>Label</span><span style={{ color: "#60a5fa" }}>{lineage.label}</span></div>}
      {lineage && <div style={provenanceRow}><span>Graph v</span><span>{lineage.graphVersion}</span></div>}
      <div style={provenanceRow}><span>Symbol</span><span>{bt.symbol}</span></div>
      <div style={provenanceRow}><span>Interval</span><span>{bt.interval}</span></div>
      <div style={provenanceRow}><span>Dataset</span><span>{bt.datasetId?.slice(0, 12) ?? "—"}...</span></div>
      <div style={provenanceRow}><span>Hash</span><span>{bt.datasetHash?.slice(0, 8) ?? "—"}</span></div>
      <div style={provenanceRow}><span>Version</span><span>{bt.strategyVersionId?.slice(0, 12) ?? "—"}...</span></div>
      <div style={provenanceRow}><span>Date</span><span>{new Date(bt.createdAt).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}</span></div>
    </div>
  );
}

const compareLabelStyle: React.CSSProperties = { display: "flex", flexDirection: "column", flex: 1 };
const compareSelectStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6, padding: "6px 8px", color: "#e0e0e0", fontSize: 12, fontFamily: "inherit",
};
const compareTableStyle: React.CSSProperties = {
  width: "100%", borderCollapse: "collapse", fontSize: 12,
};
const compareTh: React.CSSProperties = {
  textAlign: "left", padding: "6px 10px", borderBottom: "1px solid rgba(255,255,255,0.1)",
  color: "rgba(255,255,255,0.45)", fontWeight: 600, fontSize: 11,
};
const compareTd: React.CSSProperties = {
  padding: "8px 10px", borderBottom: "1px solid rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.7)",
};
const compareTdVal: React.CSSProperties = {
  ...compareTd, fontFamily: "'SF Mono', 'Fira Code', monospace", textAlign: "right",
};
const provenanceStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 8, padding: "10px 12px", fontSize: 11,
};
const provenanceRow: React.CSSProperties = {
  display: "flex", justifyContent: "space-between", padding: "2px 0",
  color: "rgba(255,255,255,0.5)",
};

// Result detail — tabs: Run | Metrics | Trades | Equity | Logs | Compare
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Task 28 — Research Journal Tab
// ---------------------------------------------------------------------------

type JournalStatus = "BASELINE" | "PROMOTE" | "DISCARD" | "KEEP_TESTING";

interface JournalEntry {
  id: string;
  strategyGraphVersionId: string;
  backtestResultId: string | null;
  hypothesis: string;
  whatChanged: string;
  expectedResult: string;
  actualResult: string | null;
  nextStep: string | null;
  status: JournalStatus;
  createdAt: string;
  updatedAt: string;
}

const JOURNAL_STATUSES: { value: JournalStatus; label: string; color: string }[] = [
  { value: "KEEP_TESTING", label: "Keep Testing", color: "rgba(255,255,255,0.5)" },
  { value: "BASELINE",     label: "Baseline",     color: "#D4A44C" },
  { value: "PROMOTE",      label: "Promote",      color: "#3fb950" },
  { value: "DISCARD",      label: "Discard",      color: "#f85149" },
];

function JournalTab({ backtestResultId, graphVersionId }: { backtestResultId: string; graphVersionId: string | null }) {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [hypothesis, setHypothesis] = useState("");
  const [whatChanged, setWhatChanged] = useState("");
  const [expectedResult, setExpectedResult] = useState("");
  const [actualResult, setActualResult] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [status, setStatus] = useState<JournalStatus>("KEEP_TESTING");

  const fetchEntries = useCallback(async () => {
    if (!graphVersionId) { setLoading(false); return; }
    const res = await apiFetch<JournalEntry[]>(`/lab/journal?graphVersionId=${graphVersionId}`);
    if (res.ok) setEntries(res.data);
    setLoading(false);
  }, [graphVersionId]);

  useEffect(() => { fetchEntries(); }, [fetchEntries]);

  const resetForm = () => {
    setHypothesis(""); setWhatChanged(""); setExpectedResult("");
    setActualResult(""); setNextStep(""); setStatus("KEEP_TESTING");
    setEditingId(null); setShowForm(false); setError(null);
  };

  const startEdit = (e: JournalEntry) => {
    setHypothesis(e.hypothesis); setWhatChanged(e.whatChanged);
    setExpectedResult(e.expectedResult); setActualResult(e.actualResult ?? "");
    setNextStep(e.nextStep ?? ""); setStatus(e.status);
    setEditingId(e.id); setShowForm(true);
  };

  const handleSave = async () => {
    if (!graphVersionId) return;
    setSaving(true); setError(null);

    const body = {
      strategyGraphVersionId: graphVersionId,
      backtestResultId,
      hypothesis, whatChanged, expectedResult,
      actualResult: actualResult || null,
      nextStep: nextStep || null,
      status,
    };

    const res = editingId
      ? await apiFetch<JournalEntry>(`/lab/journal/${editingId}`, { method: "PATCH", body: JSON.stringify(body) })
      : await apiFetch<JournalEntry>("/lab/journal", { method: "POST", body: JSON.stringify(body) });

    setSaving(false);
    if (res.ok) { resetForm(); fetchEntries(); }
    else setError(res.problem?.detail ?? "Failed to save");
  };

  const handleDelete = async (id: string) => {
    await apiFetch(`/lab/journal/${id}`, { method: "DELETE" });
    fetchEntries();
  };

  if (loading) return <div style={{ padding: 24, color: "rgba(255,255,255,0.4)" }}>Loading journal…</div>;
  if (!graphVersionId) return <div style={{ padding: 24, color: "rgba(255,255,255,0.4)" }}>Compile a strategy first to use the research journal.</div>;

  const jInputStyle: React.CSSProperties = {
    background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 6, padding: "7px 10px", color: "rgba(255,255,255,0.85)",
    fontSize: 12, width: "100%", boxSizing: "border-box" as const, fontFamily: "inherit",
  };
  const jLabelStyle: React.CSSProperties = {
    display: "block", fontSize: 10, fontWeight: 700, color: "rgba(255,255,255,0.35)",
    marginBottom: 4, textTransform: "uppercase" as const, letterSpacing: "0.06em",
  };

  return (
    <div style={{ padding: "16px 24px", maxWidth: 700 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.88)" }}>Research Journal</span>
        {!showForm && (
          <button onClick={() => setShowForm(true)} style={{
            background: "#3b82f6", color: "#fff", border: "none", borderRadius: 6,
            padding: "5px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
          }}>+ New Entry</button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ marginBottom: 10 }}>
            <label style={jLabelStyle}>Hypothesis</label>
            <textarea rows={2} style={jInputStyle} value={hypothesis} onChange={(e) => setHypothesis(e.target.value)} placeholder="What do you expect to happen?" />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={jLabelStyle}>What Changed</label>
            <textarea rows={2} style={jInputStyle} value={whatChanged} onChange={(e) => setWhatChanged(e.target.value)} placeholder="What parameters or logic did you change?" />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={jLabelStyle}>Expected Result</label>
            <textarea rows={2} style={jInputStyle} value={expectedResult} onChange={(e) => setExpectedResult(e.target.value)} placeholder="What metrics do you expect to improve?" />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={jLabelStyle}>Actual Result</label>
            <textarea rows={2} style={jInputStyle} value={actualResult} onChange={(e) => setActualResult(e.target.value)} placeholder="What actually happened? (fill after backtest)" />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={jLabelStyle}>Next Step</label>
            <textarea rows={1} style={jInputStyle} value={nextStep} onChange={(e) => setNextStep(e.target.value)} placeholder="What will you try next?" />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={jLabelStyle}>Status</label>
            <select style={jInputStyle} value={status} onChange={(e) => setStatus(e.target.value as JournalStatus)}>
              {JOURNAL_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          {error && <div style={{ color: "#f85149", fontSize: 12, marginBottom: 8 }}>{error}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button disabled={saving || !hypothesis || !whatChanged || !expectedResult} onClick={handleSave} style={{
              background: "#3b82f6", color: "#fff", border: "none", borderRadius: 6,
              padding: "7px 18px", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
              opacity: saving || !hypothesis || !whatChanged || !expectedResult ? 0.45 : 1,
            }}>{saving ? "Saving…" : editingId ? "Update" : "Save"}</button>
            <button onClick={resetForm} style={{
              background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.7)", border: "none",
              borderRadius: 6, padding: "7px 14px", fontSize: 12, cursor: "pointer", fontFamily: "inherit",
            }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Entries list */}
      {entries.length === 0 && !showForm && (
        <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 12 }}>No journal entries yet. Click "+ New Entry" to start documenting your research.</div>
      )}
      {entries.map((e) => {
        const statusInfo = JOURNAL_STATUSES.find((s) => s.value === e.status) ?? JOURNAL_STATUSES[0];
        return (
          <div key={e.id} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 8, padding: "12px 14px", marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: statusInfo.color, textTransform: "uppercase", letterSpacing: "0.06em" }}>{statusInfo.label}</span>
              <span style={{ fontSize: 10, color: "rgba(255,255,255,0.25)" }}>{new Date(e.createdAt).toLocaleDateString()}</span>
            </div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.8)", marginBottom: 4 }}><strong>Hypothesis:</strong> {e.hypothesis}</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 4 }}><strong>Changed:</strong> {e.whatChanged}</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 4 }}><strong>Expected:</strong> {e.expectedResult}</div>
            {e.actualResult && <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 4 }}><strong>Actual:</strong> {e.actualResult}</div>}
            {e.nextStep && <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 4 }}><strong>Next:</strong> {e.nextStep}</div>}
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button onClick={() => startEdit(e)} style={{ background: "none", border: "none", color: "#3b82f6", fontSize: 11, cursor: "pointer", padding: 0, fontFamily: "inherit" }}>Edit</button>
              <button onClick={() => handleDelete(e.id)} style={{ background: "none", border: "none", color: "#f85149", fontSize: 11, cursor: "pointer", padding: 0, fontFamily: "inherit" }}>Delete</button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------

type ResultTab = "run" | "metrics" | "trades" | "equity" | "logs" | "compare" | "journal";

function ResultDetail({
  bt,
  datasets,
  strategyVersions,
  allBacktests,
  onStartNew,
  submitting,
  submitError,
  activeDatasetId,
  lastCompileVersionId,
  lastCompileGraphVersionId,
  onSubmit,
}: {
  bt: BacktestListItem | null;
  datasets: DatasetListItem[];
  strategyVersions: StrategyVersionItem[];
  allBacktests: BacktestListItem[];
  onStartNew: () => void;
  submitting: boolean;
  submitError: string | null;
  activeDatasetId: string | null;
  lastCompileVersionId: string | null;
  lastCompileGraphVersionId: string | null;
  onSubmit: (params: { strategyVersionId: string; datasetId: string; feeBps: number; slippageBps: number }) => void;
}) {
  const [activeTab, setActiveTab] = useState<ResultTab>("run");

  // Reset to run tab when bt changes
  useEffect(() => {
    if (!bt) setActiveTab("run");
  }, [bt?.id]);

  const report = bt?.reportJson as BacktestReport | null | undefined;
  const isDone = bt?.status === "DONE";

  const doneRuns = allBacktests.filter((b) => b.status === "DONE");
  const tabs: { id: ResultTab; label: string; disabled?: boolean }[] = [
    { id: "run",     label: "New run" },
    { id: "metrics", label: "Metrics",      disabled: !isDone },
    { id: "trades",  label: "Trades",       disabled: !isDone },
    { id: "equity",  label: "Equity curve", disabled: !isDone },
    { id: "logs",    label: "Logs",         disabled: !isDone },
    { id: "compare", label: "Compare",      disabled: doneRuns.length < 2 },
    { id: "journal", label: "Journal",      disabled: !isDone },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Tab bar */}
      <div style={resultTabBarStyle}>
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => !t.disabled && setActiveTab(t.id)}
            style={{
              ...resultTabStyle,
              ...(activeTab === t.id ? resultTabActiveStyle : {}),
              opacity: t.disabled ? 0.35 : 1,
              cursor: t.disabled ? "not-allowed" : "pointer",
            }}
            disabled={t.disabled}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Scroll area */}
      <div style={{ flex: 1, overflow: "auto", minHeight: 0 }}>
        {/* Dataset snapshot block at top — shown whenever a bt is selected and tab is not "run" */}
        {bt && activeTab !== "run" && (
          <>
            <DatasetSnapshotBlock bt={bt} datasets={datasets} />
            {/* Task 26: lineage provenance block in results view */}
            {activeTab === "metrics" && (
              <div style={{ padding: "0 24px 8px" }}>
                <ProvenanceBlock label="Lineage" bt={bt} lastCompileVersionId={lastCompileVersionId} />
              </div>
            )}
          </>
        )}

        {/* Tab content */}
        {activeTab === "run" && (
          <BacktestForm
            datasets={datasets}
            strategyVersions={strategyVersions}
            onSubmit={onSubmit}
            submitting={submitting}
            error={submitError}
            activeDatasetId={activeDatasetId}
            lastCompileVersionId={lastCompileVersionId}
          />
        )}

        {activeTab !== "run" && bt && (
          <>
            {/* Running/Pending indicator */}
            {(bt.status === "RUNNING" || bt.status === "PENDING") && (
              <div style={runningBannerStyle}>
                <span style={{ fontSize: 13 }}>⟳</span>
                {bt.status === "PENDING" ? "Queued — waiting to start…" : "Running backtest… (polling every 2s)"}
              </div>
            )}

            {bt.status === "FAILED" && (
              <div style={errorBoxStyle}>{bt.errorMessage ?? "Backtest failed."}</div>
            )}

            {isDone && report && activeTab === "metrics" && (
              <MetricsTab report={report} />
            )}
            {isDone && report && activeTab === "trades" && (
              <TradesTab tradeLog={report.tradeLog} />
            )}
            {isDone && report && activeTab === "equity" && (
              <div style={{ height: 280, padding: "16px 16px 0" }}>
                <EquityTab tradeLog={report.tradeLog} />
              </div>
            )}
            {isDone && report && activeTab === "logs" && (
              <LogsTab report={report} />
            )}
          </>
        )}

        {activeTab === "compare" && (
          <CompareRunsTab runs={doneRuns} currentRunId={bt?.id ?? null} lastCompileVersionId={lastCompileVersionId} />
        )}

        {isDone && activeTab === "journal" && bt && (
          <JournalTab
            backtestResultId={bt.id}
            graphVersionId={lastCompileGraphVersionId}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function LabTestPage() {
  const activeDatasetId = useLabGraphStore((s) => s.activeDatasetId);
  const lastCompileResult = useLabGraphStore((s) => s.lastCompileResult);
  const lastCompileVersionId = lastCompileResult?.strategyVersionId ?? null;

  const [topTab, setTopTab] = useState<TopTab>("backtest");
  const [backtests, setBacktests]               = useState<BacktestListItem[]>([]);
  const [datasets, setDatasets]                 = useState<DatasetListItem[]>([]);
  const [strategyVersions, setStrategyVersions] = useState<StrategyVersionItem[]>([]);
  const [selectedBtId, setSelectedBtId]         = useState<string | null>(null);
  const [submitting, setSubmitting]             = useState(false);
  const [submitError, setSubmitError]           = useState<string | null>(null);

  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const selectedBt = backtests.find((b) => b.id === selectedBtId) ?? null;

  // ── Load lists ──────────────────────────────────────────────────────────

  const loadBacktests = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<BacktestListItem[]>("/lab/backtests");
    if (res.ok) setBacktests(res.data);
  }, []);

  const loadDatasets = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<DatasetListItem[]>("/lab/datasets");
    if (res.ok) setDatasets(res.data);
  }, []);

  const loadStrategyVersions = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<StrategyVersionItem[]>("/lab/strategy-versions");
    if (res.ok) setStrategyVersions(res.data);
  }, []);

  useEffect(() => {
    loadBacktests();
    loadDatasets();
    loadStrategyVersions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Polling — every 2s while selected backtest is running/pending ─────────

  const pollOnce = useCallback(async (btId: string) => {
    const res = await apiFetch<BacktestListItem>(`/lab/backtest/${btId}`);
    if (!res.ok) return;
    const updated = res.data;
    setBacktests((prev) => prev.map((b) => b.id === btId ? updated : b));
    return updated;
  }, []);

  useEffect(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }

    if (!selectedBtId) return;
    if (selectedBt?.status !== "RUNNING" && selectedBt?.status !== "PENDING") return;

    const scheduleNext = () => {
      pollTimerRef.current = setTimeout(async () => {
        const updated = await pollOnce(selectedBtId);
        if (updated?.status === "RUNNING" || updated?.status === "PENDING") {
          scheduleNext();
        }
      }, POLL_INTERVAL_MS);
    };

    scheduleNext();

    return () => {
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBtId, selectedBt?.status]);

  // ── Submit new backtest ───────────────────────────────────────────────────

  const handleSubmit = useCallback(async (params: {
    strategyVersionId: string;
    datasetId: string;
    feeBps: number;
    slippageBps: number;
  }) => {
    if (!getWorkspaceId()) return;
    setSubmitting(true);
    setSubmitError(null);

    const res = await apiFetch<BacktestListItem>("/lab/backtest", {
      method: "POST",
      body: JSON.stringify({ ...params, fillAt: "CLOSE" }),
    });

    setSubmitting(false);

    if (res.ok) {
      const newBt = res.data;
      setBacktests((prev) => [newBt, ...prev]);
      setSelectedBtId(newBt.id);
    } else {
      const detail = res.problem.detail ?? res.problem.title ?? "Unknown error";
      setSubmitError(detail);
    }
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={pageStyle}>
      {/* Left: sidebar (shown only in backtest mode) */}
      {topTab === "backtest" && (
        <div style={sidebarStyle}>
          <div style={sidebarHeaderStyle}>
            <span style={sectionLabelStyle}>Backtest runs</span>
            <button
              style={newBtnStyle}
              onClick={() => setSelectedBtId(null)}
              title="New run"
            >
              + New
            </button>
          </div>

          {backtests.length === 0 && (
            <div style={{ padding: "14px 16px", fontSize: 12, color: "rgba(255,255,255,0.3)" }}>
              No runs yet. Configure and start a backtest.
            </div>
          )}

          {backtests.map((bt) => {
            const isSelected = bt.id === selectedBtId;
            const report = bt.reportJson as BacktestReport | null | undefined;
            const label = `${bt.symbol} · ${bt.interval}`;
            const pnl = report ? fmtPnl(report.totalPnlPct) : null;
            return (
              <div
                key={bt.id}
                onClick={() => setSelectedBtId(bt.id)}
                style={{
                  padding: "10px 14px",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                  cursor: "pointer",
                  background: isSelected ? "rgba(59,130,246,0.08)" : "transparent",
                  borderLeft: isSelected ? "3px solid #3b82f6" : "3px solid transparent",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.8)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {label}
                  </span>
                  <StatusBadge status={bt.status} />
                  <StaleBadge bt={bt} lastCompileVersionId={lastCompileVersionId} />
                </div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>
                  {new Date(bt.createdAt).toLocaleDateString()}
                  {pnl && <span style={{ marginLeft: 6, color: (report?.totalPnlPct ?? 0) >= 0 ? "#3fb950" : "#f85149", fontWeight: 600 }}>{pnl}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Right: main content area */}
      <div style={mainStyle}>
        {/* Top-level tab bar: Run Backtest | Optimise */}
        <div style={topTabBarStyle}>
          {([
            { id: "backtest" as TopTab, label: "Run Backtest" },
            { id: "optimise" as TopTab, label: "Optimise" },
          ]).map((t) => (
            <button
              key={t.id}
              onClick={() => setTopTab(t.id)}
              style={{
                ...topTabStyle,
                ...(topTab === t.id ? topTabActiveStyle : {}),
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {topTab === "backtest" && (
          <ResultDetail
            bt={selectedBt}
            datasets={datasets}
            strategyVersions={strategyVersions}
            allBacktests={backtests}
            onStartNew={() => setSelectedBtId(null)}
            submitting={submitting}
            submitError={submitError}
            activeDatasetId={activeDatasetId}
            lastCompileVersionId={lastCompileVersionId}
            lastCompileGraphVersionId={lastCompileResult?.graphVersionId ?? null}
            onSubmit={handleSubmit}
          />
        )}

        {topTab === "optimise" && (
          <OptimisePanel
            datasets={datasets}
            strategyVersions={strategyVersions}
            onSelectBacktest={(id) => {
              setSelectedBtId(id);
              setTopTab("backtest");
            }}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const pageStyle: React.CSSProperties = {
  display: "flex",
  height: "100%",
  overflow: "hidden",
  background: "rgba(8,12,18,0.98)",
};

const sidebarStyle: React.CSSProperties = {
  width: 220,
  flexShrink: 0,
  borderRight: "1px solid rgba(255,255,255,0.07)",
  display: "flex",
  flexDirection: "column",
  overflow: "auto",
};

const sidebarHeaderStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "10px 14px",
  borderBottom: "1px solid rgba(255,255,255,0.07)",
  flexShrink: 0,
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.07em",
  color: "rgba(255,255,255,0.3)",
};

const mainStyle: React.CSSProperties = {
  flex: 1,
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
};

const resultTabBarStyle: React.CSSProperties = {
  display: "flex",
  borderBottom: "1px solid rgba(255,255,255,0.07)",
  background: "rgba(10,14,20,0.98)",
  flexShrink: 0,
};

const resultTabStyle: React.CSSProperties = {
  padding: "7px 14px",
  fontSize: 12,
  fontWeight: 500,
  background: "none",
  border: "none",
  borderBottom: "2px solid transparent",
  color: "rgba(255,255,255,0.4)",
  fontFamily: "inherit",
};

const resultTabActiveStyle: React.CSSProperties = {
  color: "rgba(255,255,255,0.88)",
  borderBottom: "2px solid #3B82F6",
};

const snapshotBlockStyle: React.CSSProperties = {
  margin: "16px 20px",
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.07)",
  borderRadius: 8,
  padding: "12px 14px",
};

const snapshotGridStyle: React.CSSProperties = {};

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
  fontSize: 10,
  color: "rgba(255,255,255,0.3)",
  marginTop: 4,
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
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,81,73,0.12)",
  border: "1px solid rgba(248,81,73,0.35)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#f85149",
  margin: "12px 20px",
};

const runningBannerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "10px 20px",
  fontSize: 12,
  color: "#60a5fa",
  background: "rgba(59,130,246,0.06)",
  borderBottom: "1px solid rgba(59,130,246,0.15)",
};

const newBtnStyle: React.CSSProperties = {
  background: "#3b82f6",
  color: "#fff",
  border: "none",
  borderRadius: 4,
  padding: "3px 9px",
  fontSize: 11,
  fontWeight: 700,
  cursor: "pointer",
};

const topTabBarStyle: React.CSSProperties = {
  display: "flex",
  borderBottom: "1px solid rgba(255,255,255,0.07)",
  background: "rgba(8,12,18,0.98)",
  flexShrink: 0,
};

const topTabStyle: React.CSSProperties = {
  padding: "9px 18px",
  fontSize: 12,
  fontWeight: 600,
  background: "none",
  border: "none",
  borderBottom: "2px solid transparent",
  color: "rgba(255,255,255,0.4)",
  fontFamily: "inherit",
  cursor: "pointer",
};

const topTabActiveStyle: React.CSSProperties = {
  color: "rgba(255,255,255,0.88)",
  borderBottom: "2px solid #3B82F6",
};
