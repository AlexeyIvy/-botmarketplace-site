"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getWorkspaceId, apiFetch } from "../factory/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BacktestReport {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LabPage() {
  const [wsId, setWsId] = useState("");
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
  const [history, setHistory] = useState<BacktestItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    const stored = getWorkspaceId();
    if (stored) setWsId(stored);
  }, []);

  const loadHistory = useCallback(async () => {
    if (!getWorkspaceId()) return;
    setHistoryLoading(true);
    const res = await apiFetch<BacktestItem[]>("/lab/backtests");
    setHistoryLoading(false);
    if (res.ok) setHistory(res.data);
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

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
    if (!wsId.trim()) { setError("Set Workspace ID in Factory first"); return; }
    if (!strategyId.trim()) { setError("Strategy ID is required"); return; }
    setRunning(true);
    setActiveResult(null);
    setActiveBtId(null);

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

  return (
    <div style={{ padding: "32px 24px", maxWidth: 760, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, marginBottom: 4 }}>Research Lab</h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: 28, fontSize: 14 }}>
        Historical backtest · price-breakout strategy (lookback 20) · 2:1 R/R
      </p>

      {/* ── Form ── */}
      <section style={sectionStyle}>
        <h2 style={{ fontSize: 16, marginBottom: 16 }}>Run Backtest</h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label style={labelStyle}>
            Workspace ID
            <input
              style={inputStyle}
              value={wsId}
              onChange={(e) => setWsId(e.target.value)}
              placeholder="from Factory"
            />
          </label>
          <label style={labelStyle}>
            Strategy ID
            <input
              style={inputStyle}
              value={strategyId}
              onChange={(e) => setStrategyId(e.target.value)}
              placeholder="uuid"
            />
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
          )}

          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 12 }}>
            {activeResult.symbol} · {activeResult.interval}m ·{" "}
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
                  onClick={() => { setActiveResult(bt); setActiveBtId(bt.id); }}
                >
                  <td style={tdStyle}>{bt.symbol}</td>
                  <td style={tdStyle}>{bt.interval}m</td>
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

const sectionStyle: { [key: string]: string | number | undefined } = {
  background: "var(--surface, #1a1a2e)",
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

const labelStyle: { [key: string]: string | number | undefined } = {
  display: "flex", flexDirection: "column", gap: 6,
  fontSize: 13, color: "var(--text-secondary)",
};

const inputStyle: { [key: string]: string | number | undefined } = {
  background: "rgba(255,255,255,0.07)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6, padding: "8px 10px",
  color: "inherit", fontSize: 13,
  outline: "none", width: "100%", boxSizing: "border-box",
};

const btnStyle: { [key: string]: string | number | undefined } = {
  background: "#3b82f6", color: "#fff", border: "none",
  borderRadius: 6, padding: "10px 20px",
  fontSize: 14, fontWeight: 600, cursor: "pointer",
};

const thStyle: { [key: string]: string | number | undefined } = { padding: "6px 8px", fontWeight: 500, fontSize: 12 };
const tdStyle: { [key: string]: string | number | undefined } = { padding: "8px 8px" };
