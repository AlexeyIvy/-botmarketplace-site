"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getWorkspaceId, apiFetch } from "../../lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Strategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
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
}

const INTERVALS = [
  { value: "1",  label: "1m" },
  { value: "5",  label: "5m" },
  { value: "15", label: "15m" },
  { value: "60", label: "1h" },
];

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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LabPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [strategyId, setStrategyId] = useState("");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [candleInterval, setCandleInterval] = useState("15");
  const [fromDate, setFromDate] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() - 1);
    return d.toISOString().slice(0, 10);
  });
  const [toDate, setToDate] = useState(() => new Date().toISOString().slice(0, 10));

  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeBtId, setActiveBtId] = useState<string | null>(null);
  const [activeResult, setActiveResult] = useState<BacktestItem | null>(null);
  const [showTradeLog, setShowTradeLog] = useState(false);
  const [history, setHistory] = useState<BacktestItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Load strategies for dropdown
  useEffect(() => {
    if (!getWorkspaceId()) return;
    apiFetch<Strategy[]>("/strategies").then((res) => {
      if (res.ok) setStrategies(res.data);
    });
  }, []);

  // When strategy selection changes, auto-fill symbol from strategy
  const handleStrategyChange = (id: string) => {
    setStrategyId(id);
    const strat = strategies.find((s) => s.id === id);
    if (strat) setSymbol(strat.symbol);
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
    setRunning(true);
    setActiveResult(null);
    setActiveBtId(null);
    setShowTradeLog(false);

    const res = await apiFetch<BacktestItem>("/lab/backtest", {
      method: "POST",
      body: JSON.stringify({
        strategyId: strategyId.trim(),
        symbol: symbol.trim() || undefined,
        interval: candleInterval,
        fromTs: new Date(fromDate).toISOString(),
        toTs:   new Date(toDate).toISOString(),
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

  return (
    <div style={{ padding: "32px 24px", maxWidth: 860, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, marginBottom: 4 }}>Research Lab</h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: 28, fontSize: 14 }}>
        Historical backtest · price-breakout strategy (lookback 20) · 2:1 R/R
      </p>

      {/* ── Form ── */}
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

          <label style={labelStyle}>
            Symbol
            <input
              style={inputStyle}
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="BTCUSDT"
            />
          </label>
          <label style={labelStyle}>
            Interval
            <select
              style={inputStyle}
              value={candleInterval}
              onChange={(e) => setCandleInterval(e.target.value)}
            >
              {INTERVALS.map((iv) => (
                <option key={iv.value} value={iv.value}>{iv.label}</option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            From
            <input
              style={inputStyle}
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
          </label>
          <label style={labelStyle}>
            To
            <input
              style={inputStyle}
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
            />
          </label>
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

      {/* ── Active result ── */}
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
              Fetching candles and simulating… polling every 2 s
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

      {/* ── History ── */}
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
