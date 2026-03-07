"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getWorkspaceId, apiFetch, apiFetchNoWorkspace } from "../../lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Strategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
}

interface DatasetItem {
  id: string;
  exchange: string;
  symbol: string;
  interval: string;
  fromTsMs: number;
  toTsMs: number;
  fetchedAt: string;
  datasetHash: string;
  candleCount: number;
  qualityJson: QualityJson;
  status: string;
}

interface QualityJson {
  gapsCount: number;
  maxGapMs: number;
  dupeAttempts: number;
  sanityIssuesCount: number;
  firstOpenTimeMs: number;
  lastOpenTimeMs: number;
  expectedCandles: number;
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

interface BacktestReport {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
  tradeLog?: TradeRecord[];
}

interface BacktestItem {
  id: string;
  strategyId: string;
  symbol: string;
  interval: string;
  fromTs: string;
  toTs: string;
  status: "PENDING" | "RUNNING" | "DONE" | "FAILED";
  reportJson: BacktestReport | null;
  errorMessage: string | null;
  createdAt: string;
  // Stage 19b reproducibility fields
  datasetId: string | null;
  datasetHash: string | null;
  feeBps: number;
  slippageBps: number;
  fillAt: string;
  engineVersion: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function pct(n: number) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function fmtRate(n: number) {
  return (n * 100).toFixed(1) + "%";
}

function fmtInterval(interval: string) {
  if (interval === "60") return "1h";
  if (interval === "240") return "4h";
  if (interval === "1440") return "1d";
  return interval + "m";
}

function fmtTs(ts: number) {
  return new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function shortHash(hash: string | null | undefined) {
  return hash ? hash.slice(0, 10) : null;
}

// ---------------------------------------------------------------------------
// Guest Demo types (Stage 20e)
// ---------------------------------------------------------------------------

interface DemoSummary {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
}

interface DemoResult {
  presetId: string;
  description: string;
  symbol: string;
  interval: string;
  summary: DemoSummary;
  trades: TradeRecord[];
}

const DEMO_PRESETS = [
  {
    id: "btc-breakout-demo",
    label: "BTC Breakout",
    subtitle: "BTCUSDT · 1h · 90 days",
    description: "Price-breakout strategy on BTC/USDT 1-hour candles over the last 90 days.",
  },
  {
    id: "eth-mean-reversion-demo",
    label: "ETH Momentum",
    subtitle: "ETHUSDT · 15m · 45 days",
    description: "Breakout momentum strategy on ETH/USDT 15-minute candles over the last 45 days.",
  },
];

type DemoStep = "idle" | "select" | "load" | "simulate" | "report";

// ---------------------------------------------------------------------------
// Guest Lab Demo component
// ---------------------------------------------------------------------------

function GuestLabDemo() {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [step, setStep] = useState<DemoStep>("idle");
  const [result, setResult] = useState<DemoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTrades, setShowTrades] = useState(false);

  async function runDemo(presetId: string) {
    setSelectedPreset(presetId);
    setResult(null);
    setError(null);
    setShowTrades(false);

    // Step 1: select
    setStep("select");
    await delay(600);

    // Step 2: load dataset
    setStep("load");
    await delay(800);

    // Step 3: simulate (fetch real data from server)
    setStep("simulate");

    const res = await apiFetchNoWorkspace<DemoResult>("/demo/backtest", {
      method: "POST",
      body: JSON.stringify({ presetId }),
    });

    if (!res.ok) {
      setError(`${res.problem.title}: ${res.problem.detail}`);
      setStep("idle");
      return;
    }

    await delay(400);

    // Step 4: show report
    setStep("report");
    setResult(res.data);
  }

  const preset = DEMO_PRESETS.find((p) => p.id === selectedPreset) ?? null;

  return (
    <div>
      <h1 style={{ fontSize: 26, marginBottom: 4 }}>Research Lab — Demo</h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: 28, fontSize: 14 }}>
        Explore our backtest engine with public market data — no account needed.
        <Link href="/login" style={{ color: "var(--accent, #0969da)", marginLeft: 8 }}>
          Sign in for full access →
        </Link>
      </p>

      {/* Preset cards */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 28 }}>
        {DEMO_PRESETS.map((p) => (
          <div
            key={p.id}
            style={{
              ...demoCard,
              border: selectedPreset === p.id
                ? "2px solid var(--accent, #0969da)"
                : "2px solid var(--border)",
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{p.label}</div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 10 }}>
              {p.subtitle}
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.5 }}>
              {p.description}
            </div>
            <button
              style={{
                ...demoBtnStyle,
                opacity: step !== "idle" && step !== "report" ? 0.5 : 1,
                cursor: step !== "idle" && step !== "report" ? "not-allowed" : "pointer",
              }}
              onClick={() => {
                if (step !== "idle" && step !== "report") return;
                void runDemo(p.id);
              }}
            >
              {selectedPreset === p.id && step !== "idle" && step !== "report"
                ? "Running..."
                : "Run demo backtest"}
            </button>
          </div>
        ))}
      </div>

      {/* Step progress */}
      {step !== "idle" && (
        <div style={{ ...sectionStyle, marginBottom: 24 }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
            {preset?.label ?? "Demo"} · Progress
          </div>
          <DemoProgress step={step} />
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ color: "#f85149", padding: "12px 16px", background: "rgba(248,81,73,0.1)", borderRadius: 6, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Report */}
      {step === "report" && result && (
        <div style={sectionStyle}>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{result.description}</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 20 }}>
            {result.summary.candles.toLocaleString()} candles processed
          </div>

          {/* Summary grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10, marginBottom: 20 }}>
            <DemoStat label="Trades" value={String(result.summary.trades)} />
            <DemoStat label="Win Rate" value={fmtRate(result.summary.winrate)} color={result.summary.winrate >= 0.5 ? "#3fb950" : "#f85149"} />
            <DemoStat label="Total PnL" value={pct(result.summary.totalPnlPct)} color={result.summary.totalPnlPct >= 0 ? "#3fb950" : "#f85149"} />
            <DemoStat label="Max Drawdown" value={`-${result.summary.maxDrawdownPct.toFixed(2)}%`} color="#e3b341" />
          </div>

          {/* Trade log toggle */}
          {result.trades.length > 0 && (
            <>
              <button
                style={{ ...demoBtnStyle, background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border)", marginBottom: 12 }}
                onClick={() => setShowTrades((v) => !v)}
              >
                {showTrades ? "Hide" : "Show"} trade log ({result.trades.length})
              </button>
              {showTrades && (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                    <thead>
                      <tr>
                        {["Entry", "Exit", "Entry Price", "Exit Price", "Outcome", "PnL %"].map((h) => (
                          <th key={h} style={thStyleDemo}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map((t, i) => (
                        <tr key={i}>
                          <td style={tdDemo}>{new Date(t.entryTime).toLocaleDateString()}</td>
                          <td style={tdDemo}>{new Date(t.exitTime).toLocaleDateString()}</td>
                          <td style={tdDemo}>{t.entryPrice.toFixed(2)}</td>
                          <td style={tdDemo}>{t.exitPrice.toFixed(2)}</td>
                          <td style={{ ...tdDemo, color: t.outcome === "WIN" ? "#3fb950" : t.outcome === "LOSS" ? "#f85149" : "var(--text-secondary)", fontWeight: 700 }}>
                            {t.outcome}
                          </td>
                          <td style={{ ...tdDemo, color: t.pnlPct >= 0 ? "#3fb950" : "#f85149" }}>
                            {pct(t.pnlPct)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Demo step progress sub-component
// ---------------------------------------------------------------------------

const DEMO_STEPS: { key: DemoStep; label: string }[] = [
  { key: "select", label: "Select preset" },
  { key: "load", label: "Load dataset" },
  { key: "simulate", label: "Run simulation" },
  { key: "report", label: "Render report" },
];

function DemoProgress({ step }: { step: DemoStep }) {
  const order: DemoStep[] = ["select", "load", "simulate", "report"];
  const current = order.indexOf(step);
  return (
    <div style={{ display: "flex", gap: 0 }}>
      {DEMO_STEPS.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={s.key} style={{ display: "flex", alignItems: "center", flex: 1 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
              <div style={{
                width: 28, height: 28,
                borderRadius: "50%",
                background: done ? "#3fb950" : active ? "var(--accent, #0969da)" : "var(--bg-secondary)",
                border: `2px solid ${done ? "#3fb950" : active ? "var(--accent, #0969da)" : "var(--border)"}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 13, fontWeight: 700,
                color: done || active ? "#fff" : "var(--text-secondary)",
                marginBottom: 6,
                transition: "background 0.3s",
              }}>
                {done ? "✓" : i + 1}
              </div>
              <div style={{ fontSize: 11, color: active ? "var(--text-primary)" : "var(--text-secondary)", textAlign: "center" }}>
                {s.label}
                {active && step !== "report" && (
                  <span style={{ display: "inline-block", marginLeft: 4 }}>...</span>
                )}
              </div>
            </div>
            {i < DEMO_STEPS.length - 1 && (
              <div style={{
                height: 2, flex: "0 0 24px",
                background: done ? "#3fb950" : "var(--border)",
                marginBottom: 22,
                transition: "background 0.3s",
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function DemoStat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ padding: "12px 14px", background: "var(--bg-secondary)", borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: color ?? "var(--text-primary)" }}>{value}</div>
    </div>
  );
}

function delay(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Authenticated Lab — Classic mode (StrategyList + DslEditor + AiChat + BacktestReport)
// ---------------------------------------------------------------------------

export function AuthLabClassicMode() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [strategyId, setStrategyId] = useState("");
  const [datasetId, setDatasetId] = useState("");

  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeBtId, setActiveBtId] = useState<string | null>(null);
  const [activeResult, setActiveResult] = useState<BacktestItem | null>(null);
  const [showTradeLog, setShowTradeLog] = useState(false);
  const [history, setHistory] = useState<BacktestItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Load strategies and datasets
  useEffect(() => {
    if (!getWorkspaceId()) return;
    apiFetch<Strategy[]>("/strategies").then((res) => {
      if (res.ok) setStrategies(res.data);
    });
    apiFetch<DatasetItem[]>("/lab/datasets").then((res) => {
      if (res.ok) setDatasets(res.data);
    });
  }, []);

  const handleStrategyChange = (id: string) => {
    setStrategyId(id);
  };

  const loadHistory = useCallback(async () => {
    if (!getWorkspaceId()) return;
    setHistoryLoading(true);
    const res = await apiFetch<BacktestItem[]>("/lab/backtests");
    setHistoryLoading(false);
    if (res.ok) setHistory(res.data);
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  // Poll active backtest until terminal
  useEffect(() => {
    if (!activeBtId) return;
    if (activeResult?.status === "DONE" || activeResult?.status === "FAILED") return;
    const timer = setInterval(async () => {
      const res = await apiFetch<BacktestItem>(`/lab/backtest/${activeBtId}`);
      if (res.ok) {
        setActiveResult(res.data);
        if (res.data.status === "DONE" || res.data.status === "FAILED") {
          setRunning(false);
          loadHistory();
        }
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [activeBtId, activeResult?.status, loadHistory]);

  async function startBacktest() {
    setError(null);
    if (!getWorkspaceId()) { setError("Set Workspace ID in Factory first"); return; }
    if (!strategyId.trim()) { setError("Select a strategy"); return; }
    if (!datasetId.trim()) { setError("Select a dataset"); return; }
    setRunning(true);
    setActiveResult(null);
    setActiveBtId(null);
    setShowTradeLog(false);

    const res = await apiFetch<BacktestItem>("/lab/backtest", {
      method: "POST",
      body: JSON.stringify({
        strategyId: strategyId.trim(),
        datasetId: datasetId.trim(),
        feeBps: 0,
        slippageBps: 0,
        fillAt: "CLOSE",
      }),
    });

    if (!res.ok) {
      setRunning(false);
      setError(`${res.problem.title}: ${res.problem.detail}`);
      return;
    }

    setActiveBtId(res.data.id);
    setActiveResult(res.data);
  }

  const report = activeResult?.reportJson ?? null;
  const tradeLog = report?.tradeLog ?? [];

  // Selected dataset info for preview
  const selectedDataset = datasets.find((d) => d.id === datasetId) ?? null;

  return (
    <div style={{ padding: "32px 24px", maxWidth: 860, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, marginBottom: 4 }}>Research Lab</h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: 28, fontSize: 14 }}>
        Historical backtest · dataset-first (Stage 19) · price-breakout strategy (lookback 20) · 2:1 R/R
      </p>

      {/* ── StrategyList + DslEditor form ── */}
      <section style={sectionStyle}>
        <h2 style={{ fontSize: 16, marginBottom: 16 }}>Run Backtest</h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
            Strategy
            {strategies.length > 0 ? (
              <select
                style={inputStyle}
                value={strategyId}
                onChange={(e) => handleStrategyChange(e.target.value)}
              >
                <option value="">— select a strategy —</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.symbol} · {s.timeframe})
                  </option>
                ))}
              </select>
            ) : (
              <input
                style={inputStyle}
                value={strategyId}
                onChange={(e) => setStrategyId(e.target.value)}
                placeholder="strategy UUID (no strategies loaded)"
              />
            )}
          </label>

          <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
            Dataset
            {datasets.length > 0 ? (
              <select
                style={inputStyle}
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
              >
                <option value="">— select a dataset —</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.symbol} · {d.interval} · {new Date(d.fromTsMs).toLocaleDateString()} – {new Date(d.toTsMs).toLocaleDateString()} · {d.candleCount} candles · {d.status}
                  </option>
                ))}
              </select>
            ) : (
              <input
                style={inputStyle}
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                placeholder="dataset UUID (no datasets loaded — POST /lab/datasets first)"
              />
            )}
          </label>

          {selectedDataset && (
            <div style={{ gridColumn: "1 / -1", fontSize: 12, color: "var(--text-secondary)", background: "rgba(255,255,255,0.03)", borderRadius: 6, padding: "8px 12px" }}>
              <strong>Dataset:</strong> {selectedDataset.exchange} · {selectedDataset.symbol} · {selectedDataset.interval} ·{" "}
              {selectedDataset.candleCount} candles · hash: <code>{shortHash(selectedDataset.datasetHash)}</code> · {selectedDataset.status}
            </div>
          )}
        </div>

        {error && (
          <div style={{ color: "#f87171", fontSize: 13, marginTop: 12 }}>{error}</div>
        )}

        <button
          style={{ ...btnStyle, marginTop: 16, opacity: running ? 0.6 : 1 }}
          disabled={running}
          onClick={startBacktest}
        >
          {running ? "Running…" : "Run Backtest"}
        </button>
      </section>

      {/* ── AiChat placeholder (BacktestReport active result) ── */}
      {activeResult && (
        <section style={sectionStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 style={{ fontSize: 16 }}>Result</h2>
            <StatusBadge status={activeResult.status} />
          </div>

          {activeResult.status === "FAILED" && (
            <div style={{ color: "#f87171", fontSize: 13 }}>
              Error: {activeResult.errorMessage}
            </div>
          )}

          {(activeResult.status === "PENDING" || activeResult.status === "RUNNING") && (
            <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>
              Loading candles from dataset and simulating… polling every 2 s
            </div>
          )}

          {activeResult.status === "DONE" && report && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                <MetricCard label="Trades" value={String(report.trades)} />
                <MetricCard label="Wins" value={String(report.wins)} />
                <MetricCard label="Winrate" value={fmtRate(report.winrate)} />
                <MetricCard
                  label="Total PnL"
                  value={pct(report.totalPnlPct)}
                  positive={report.totalPnlPct >= 0}
                />
                <MetricCard
                  label="Max Drawdown"
                  value={`-${report.maxDrawdownPct.toFixed(2)}%`}
                  positive={false}
                />
                <MetricCard label="Candles" value={String(report.candles)} />
              </div>

              {/* Trade Log toggle */}
              {tradeLog.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <button
                    style={{ ...btnStyle, fontSize: 12, padding: "5px 14px", background: "rgba(255,255,255,0.08)", color: "inherit" }}
                    onClick={() => setShowTradeLog((v) => !v)}
                  >
                    {showTradeLog ? "Hide" : "Show"} Trade Log ({tradeLog.length} trades)
                  </button>

                  {showTradeLog && (
                    <div style={{ marginTop: 12, overflowX: "auto" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                        <thead>
                          <tr style={{ color: "var(--text-secondary)", textAlign: "left" }}>
                            <th style={thStyle}>Entry</th>
                            <th style={thStyle}>Exit</th>
                            <th style={thStyle}>Entry $</th>
                            <th style={thStyle}>Exit $</th>
                            <th style={thStyle}>SL $</th>
                            <th style={thStyle}>TP $</th>
                            <th style={thStyle}>Outcome</th>
                            <th style={thStyle}>PnL %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tradeLog.map((t, i) => (
                            <tr key={i} style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                              <td style={tdStyle}>{fmtTs(t.entryTime)}</td>
                              <td style={tdStyle}>{fmtTs(t.exitTime)}</td>
                              <td style={tdStyle}>{t.entryPrice.toFixed(2)}</td>
                              <td style={tdStyle}>{t.exitPrice.toFixed(2)}</td>
                              <td style={tdStyle}>{t.slPrice.toFixed(2)}</td>
                              <td style={tdStyle}>{t.tpPrice.toFixed(2)}</td>
                              <td style={tdStyle}><OutcomeBadge outcome={t.outcome} /></td>
                              <td style={{
                                ...tdStyle,
                                color: t.pnlPct >= 0 ? "#4ade80" : "#f87171",
                                fontWeight: 600,
                              }}>
                                {pct(t.pnlPct)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* ── Data snapshot (Stage 19b) ── */}
          <DataSnapshot bt={activeResult} />

          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 12 }}>
            {activeResult.symbol} · {fmtInterval(activeResult.interval)} ·{" "}
            {new Date(activeResult.fromTs).toLocaleDateString()} –{" "}
            {new Date(activeResult.toTs).toLocaleDateString()}
          </div>
        </section>
      )}

      {/* ── Demo-forward note ── */}
      <section style={sectionStyle}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Demo-Forward Run</h2>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>
          To run your strategy live on Bybit Demo and record all events (signal, order_sent,
          order_update, position_update) in the journal, go to{" "}
          <Link href="/factory" style={{ color: "#60a5fa" }}>Factory</Link>
          , create a Bot from a strategy, and start a Run.
          The event log is available on the Bot detail page.
        </p>
      </section>

      {/* ── BacktestReport history ── */}
      <section style={sectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h2 style={{ fontSize: 16 }}>History</h2>
          <button style={{ ...btnStyle, fontSize: 12, padding: "4px 12px" }} onClick={loadHistory}>
            Refresh
          </button>
        </div>

        {historyLoading && (
          <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Loading…</div>
        )}

        {!historyLoading && history.length === 0 && (
          <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>No backtests yet.</div>
        )}

        {history.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ color: "var(--text-secondary)", textAlign: "left" }}>
                <th style={thStyle}>Symbol</th>
                <th style={thStyle}>Int</th>
                <th style={thStyle}>Period</th>
                <th style={thStyle}>Dataset</th>
                <th style={thStyle}>Fee/Slip</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Trades</th>
                <th style={thStyle}>Winrate</th>
                <th style={thStyle}>PnL</th>
              </tr>
            </thead>
            <tbody>
              {history.map((bt) => (
                <tr
                  key={bt.id}
                  style={{ cursor: "pointer", borderTop: "1px solid rgba(255,255,255,0.06)" }}
                  onClick={() => { setActiveResult(bt); setActiveBtId(bt.id); setShowTradeLog(false); }}
                >
                  <td style={tdStyle}>{bt.symbol}</td>
                  <td style={tdStyle}>{fmtInterval(bt.interval)}</td>
                  <td style={tdStyle}>
                    {new Date(bt.fromTs).toLocaleDateString()} –{" "}
                    {new Date(bt.toTs).toLocaleDateString()}
                  </td>
                  <td style={tdStyle}>
                    {bt.datasetHash
                      ? <code style={{ fontSize: 11 }}>{shortHash(bt.datasetHash)}</code>
                      : <span style={{ color: "var(--text-secondary)", fontSize: 11 }}>legacy</span>}
                  </td>
                  <td style={tdStyle}>
                    {bt.datasetId ? `${bt.feeBps}/${bt.slippageBps}` : "—"}
                  </td>
                  <td style={tdStyle}><StatusBadge status={bt.status} /></td>
                  <td style={tdStyle}>{bt.reportJson?.trades ?? "—"}</td>
                  <td style={tdStyle}>
                    {bt.reportJson ? fmtRate(bt.reportJson.winrate) : "—"}
                  </td>
                  <td style={tdStyle}>
                    {bt.reportJson ? (
                      <span style={{ color: bt.reportJson.totalPnlPct >= 0 ? "#4ade80" : "#f87171" }}>
                        {pct(bt.reportJson.totalPnlPct)}
                      </span>
                    ) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Guest mode export
// ---------------------------------------------------------------------------

export function GuestLabClassicMode() {
  return (
    <div style={{ padding: "32px 24px", maxWidth: 860, margin: "0 auto" }}>
      <GuestLabDemo />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Data Snapshot sub-component (Stage 19b spec §11)
// ---------------------------------------------------------------------------

function DataSnapshot({ bt }: { bt: BacktestItem }) {
  if (!bt.datasetId) {
    return (
      <div style={{ marginTop: 16, padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: 6, fontSize: 12, color: "var(--text-secondary)" }}>
        Legacy backtest (no dataset binding)
      </div>
    );
  }

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Data Snapshot
      </div>
      <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 6, padding: "12px 14px", fontSize: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 24px" }}>
        <SnapshotRow label="Dataset ID" value={bt.datasetId.slice(0, 18) + "…"} mono />
        <SnapshotRow label="Hash" value={bt.datasetHash ? shortHash(bt.datasetHash)! : "—"} mono />
        <SnapshotRow label="Fee" value={`${bt.feeBps} bps`} />
        <SnapshotRow label="Slippage" value={`${bt.slippageBps} bps`} />
        <SnapshotRow label="Fill at" value={bt.fillAt} />
        <SnapshotRow label="Engine" value={bt.engineVersion} mono />
      </div>
    </div>
  );
}

function SnapshotRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
      <span style={{ color: "var(--text-secondary)", minWidth: 80, flexShrink: 0 }}>{label}:</span>
      <span style={mono ? { fontFamily: "monospace", fontSize: 11 } : {}}>{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PENDING: "#fbbf24",
    RUNNING: "#60a5fa",
    DONE:    "#4ade80",
    FAILED:  "#f87171",
  };
  const color = colors[status] ?? "#888";
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 4,
      background: color + "22", color,
    }}>
      {status}
    </span>
  );
}

function OutcomeBadge({ outcome }: { outcome: "WIN" | "LOSS" | "NEUTRAL" }) {
  const map = {
    WIN:     { color: "#4ade80", label: "WIN" },
    LOSS:    { color: "#f87171", label: "LOSS" },
    NEUTRAL: { color: "#94a3b8", label: "NEUT" },
  };
  const { color, label } = map[outcome];
  return <span style={{ fontSize: 11, fontWeight: 600, color }}>{label}</span>;
}

function MetricCard({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  const color = positive === undefined ? undefined : positive ? "#4ade80" : "#f87171";
  return (
    <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 6, padding: "12px 16px" }}>
      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const sectionStyle: React.CSSProperties = {
  background: "var(--surface, #1a1a2e)",
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

const labelStyle: React.CSSProperties = {
  display: "flex", flexDirection: "column", gap: 6,
  fontSize: 13, color: "var(--text-secondary)",
};

const inputStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.07)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6, padding: "8px 10px",
  color: "inherit", fontSize: 13,
  outline: "none", width: "100%", boxSizing: "border-box",
};

const btnStyle: React.CSSProperties = {
  background: "#3b82f6", color: "#fff", border: "none",
  borderRadius: 6, padding: "10px 20px",
  fontSize: 14, fontWeight: 600, cursor: "pointer",
};

const thStyle: React.CSSProperties = { padding: "6px 8px", fontWeight: 500, fontSize: 12 };
const tdStyle: React.CSSProperties = { padding: "8px 8px" };

// ── Guest demo styles (Stage 20e) ─────────────────────────────────────────

const demoCard: React.CSSProperties = {
  flex: "1 1 260px",
  maxWidth: 360,
  background: "var(--surface, #1a1a2e)",
  borderRadius: 10,
  padding: 20,
  boxSizing: "border-box",
};

const demoBtnStyle: React.CSSProperties = {
  background: "#3b82f6",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  padding: "10px 20px",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
  width: "100%",
};

const thStyleDemo: React.CSSProperties = {
  padding: "6px 8px",
  fontWeight: 600,
  fontSize: 11,
  color: "var(--text-secondary)",
  textAlign: "left",
  borderBottom: "1px solid var(--border)",
};

const tdDemo: React.CSSProperties = {
  padding: "7px 8px",
  fontSize: 12,
  borderBottom: "1px solid var(--border)",
  fontFamily: "monospace",
};
