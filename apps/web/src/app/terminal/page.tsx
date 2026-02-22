"use client";

import { useState } from "react";
import { apiFetchNoWorkspace } from "../factory/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Ticker {
  symbol: string;
  lastPrice: number;
  bidPrice: number;
  askPrice: number;
  prevPrice24h: number;
  price24hPcnt: number;
  highPrice24h: number;
  lowPrice24h: number;
  volume24h: number;
}

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

type LoadState = "idle" | "loading" | "success" | "error";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVALS = ["1", "5", "15", "30", "60", "240", "D"] as const;
const DEFAULT_SYMBOL = "BTCUSDT";
const DEFAULT_INTERVAL = "15";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalPage() {
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [interval, setInterval] = useState(DEFAULT_INTERVAL);
  const [limit, setLimit] = useState("50");

  const [tickerState, setTickerState] = useState<LoadState>("idle");
  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [tickerError, setTickerError] = useState<string | null>(null);

  const [candlesState, setCandlesState] = useState<LoadState>("idle");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [candlesError, setCandlesError] = useState<string | null>(null);

  // --- Actions ---

  async function loadTicker() {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    setTickerState("loading");
    setTickerError(null);
    setTicker(null);

    const res = await apiFetchNoWorkspace<Ticker>(
      `/terminal/ticker?symbol=${encodeURIComponent(sym)}`,
    );
    if (res.ok) {
      setTicker(res.data);
      setTickerState("success");
    } else {
      setTickerError(`${res.problem.title}: ${res.problem.detail}`);
      setTickerState("error");
    }
  }

  async function loadCandles() {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    setCandlesState("loading");
    setCandlesError(null);
    setCandles([]);

    const lim = Math.min(Math.max(1, Number(limit) || 50), 1000);
    const res = await apiFetchNoWorkspace<Candle[]>(
      `/terminal/candles?symbol=${encodeURIComponent(sym)}&interval=${interval}&limit=${lim}`,
    );
    if (res.ok) {
      setCandles(res.data);
      setCandlesState("success");
    } else {
      setCandlesError(`${res.problem.title}: ${res.problem.detail}`);
      setCandlesState("error");
    }
  }

  async function loadAll() {
    await Promise.all([loadTicker(), loadCandles()]);
  }

  // --- Helpers ---

  function pctColor(pct: number) {
    if (pct > 0) return "#3fb950";
    if (pct < 0) return "#f85149";
    return "var(--text-secondary)";
  }

  function fmt(n: number) {
    return n.toLocaleString(undefined, { maximumFractionDigits: 6 });
  }

  const loading = tickerState === "loading" || candlesState === "loading";

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={{ padding: "32px 24px", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, marginBottom: 24 }}>Terminal — Market Data</h1>

      {/* ── Controls ── */}
      <div style={{ ...card, marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <input
            style={{ ...input, width: 140 }}
            placeholder="Symbol (e.g. BTCUSDT)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && loadAll()}
          />
          <select
            style={{ ...input, width: 100 }}
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
          >
            {INTERVALS.map((iv) => (
              <option key={iv} value={iv}>
                {iv === "D" ? "1D" : `${iv}m`}
              </option>
            ))}
          </select>
          <input
            style={{ ...input, width: 80 }}
            type="number"
            min={1}
            max={1000}
            placeholder="Limit"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
          />
          <button style={btn} onClick={loadAll} disabled={loading}>
            {loading ? "Loading..." : "Load"}
          </button>
        </div>
      </div>

      {/* ── Ticker ── */}
      <div style={{ ...card, marginBottom: 20 }}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Ticker</h2>

        {tickerState === "idle" && (
          <p style={hint}>Select a symbol and click Load.</p>
        )}
        {tickerState === "loading" && <p style={hint}>Loading ticker...</p>}
        {tickerState === "error" && (
          <p style={{ color: "#f85149", fontSize: 13 }}>{tickerError}</p>
        )}
        {tickerState === "success" && ticker && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
            <TickerCell label="Last Price" value={fmt(ticker.lastPrice)} />
            <TickerCell label="Bid" value={fmt(ticker.bidPrice)} />
            <TickerCell label="Ask" value={fmt(ticker.askPrice)} />
            <TickerCell
              label="24h Change"
              value={`${(ticker.price24hPcnt * 100).toFixed(2)}%`}
              color={pctColor(ticker.price24hPcnt)}
            />
            <TickerCell label="24h High" value={fmt(ticker.highPrice24h)} />
            <TickerCell label="24h Low" value={fmt(ticker.lowPrice24h)} />
            <TickerCell label="24h Volume" value={fmt(ticker.volume24h)} />
            <TickerCell label="Prev Close" value={fmt(ticker.prevPrice24h)} />
          </div>
        )}
      </div>

      {/* ── Candles ── */}
      <div style={card}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>
          Candles{candlesState === "success" ? ` (${candles.length})` : ""}
        </h2>

        {candlesState === "idle" && <p style={hint}>Click Load to fetch candles.</p>}
        {candlesState === "loading" && <p style={hint}>Loading candles...</p>}
        {candlesState === "error" && (
          <p style={{ color: "#f85149", fontSize: 13 }}>{candlesError}</p>
        )}
        {candlesState === "success" && candles.length === 0 && (
          <p style={hint}>No candles returned.</p>
        )}
        {candlesState === "success" && candles.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>
                  {["Time", "Open", "High", "Low", "Close", "Volume"].map((h) => (
                    <th
                      key={h}
                      style={{
                        textAlign: "right",
                        padding: "4px 8px",
                        borderBottom: "1px solid var(--border)",
                        color: "var(--text-secondary)",
                        fontWeight: 600,
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...candles].reverse().map((c) => {
                  const bullish = c.close >= c.open;
                  return (
                    <tr key={c.openTime}>
                      <td style={td}>{new Date(c.openTime).toLocaleString()}</td>
                      <td style={td}>{fmt(c.open)}</td>
                      <td style={td}>{fmt(c.high)}</td>
                      <td style={td}>{fmt(c.low)}</td>
                      <td style={{ ...td, color: bullish ? "#3fb950" : "#f85149" }}>
                        {fmt(c.close)}
                      </td>
                      <td style={td}>{fmt(c.volume)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TickerCell({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div style={{ padding: "10px 12px", background: "var(--bg-secondary)", borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: color ?? "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const card: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: 16,
};

const input: React.CSSProperties = {
  padding: "8px 12px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 14,
};

const btn: React.CSSProperties = {
  padding: "8px 20px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
};

const hint: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 13,
};

const td: React.CSSProperties = {
  padding: "4px 8px",
  textAlign: "right",
  borderBottom: "1px solid var(--border)",
  fontFamily: "monospace",
};
