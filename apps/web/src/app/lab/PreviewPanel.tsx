"use client";

// ---------------------------------------------------------------------------
// /lab — DSL dry-run preview against the last 24h of real candles (§5.12)
//
// Sits in the context bar next to Compile & Save. On click, POSTs the most
// recently compiled DSL to /api/v1/lab/preview and renders a compact popover
// with trades / winrate / max drawdown / P&L + an inline equity sparkline.
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";

// ---------------------------------------------------------------------------
// Types — mirror the backend response shape
// ---------------------------------------------------------------------------

interface TradeRecord {
  entryTime: number;
  exitTime: number;
  entryPrice: number;
  exitPrice: number;
  pnlPct: number;
  outcome: "WIN" | "LOSS" | "NEUTRAL";
}

interface PreviewReport {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
  tradeLog: TradeRecord[];
}

interface PreviewMeta {
  symbol: string;
  exchange: string;
  interval: string;
  hours: number;
  candleCount: number;
  fromTsMs: number;
  toTsMs: number;
  dataAgeMs: number;
  engineVersion: string;
}

interface PreviewResponse {
  report: PreviewReport;
  meta: PreviewMeta;
}

type RunState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; data: PreviewResponse }
  | { kind: "error"; title: string; detail: string; errors?: Array<{ field: string; message: string }> };

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PreviewPanel({
  dslJson,
  symbol,
  disabled,
}: {
  dslJson: Record<string, unknown> | null;
  symbol: string;
  disabled: boolean;
}) {
  const [state, setState] = useState<RunState>({ kind: "idle" });
  const [open, setOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const btnDisabled = disabled || !dslJson || state.kind === "loading";

  const runPreview = useCallback(async () => {
    if (!dslJson) return;
    setState({ kind: "loading" });
    setOpen(true);
    const res = await apiFetch<PreviewResponse>("/lab/preview", {
      method: "POST",
      body: JSON.stringify({ dslJson, symbol, hours: 24 }),
    });
    if (res.ok) {
      setState({ kind: "done", data: res.data });
    } else {
      setState({
        kind: "error",
        title: res.problem.title,
        detail: res.problem.detail,
        errors: res.problem.errors,
      });
    }
  }, [dslJson, symbol]);

  // Close popover on click-outside / Escape
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("mousedown", handleClick);
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("mousedown", handleClick);
      window.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div style={{ position: "relative", flexShrink: 0 }} ref={popoverRef}>
      <button
        onClick={runPreview}
        disabled={btnDisabled}
        title={
          !dslJson
            ? "Compile the graph first"
            : "Run a dry-run preview against the last 24h of market data"
        }
        style={{
          padding: "5px 14px",
          fontSize: 12,
          fontWeight: 600,
          background: btnDisabled ? "rgba(255,255,255,0.06)" : "rgba(59,130,246,0.15)",
          border: `1px solid ${btnDisabled ? "rgba(255,255,255,0.12)" : "rgba(59,130,246,0.5)"}`,
          borderRadius: 5,
          color: btnDisabled ? "rgba(255,255,255,0.3)" : "#3B82F6",
          cursor: btnDisabled ? "not-allowed" : "pointer",
          transition: "background 0.15s",
          fontFamily: "inherit",
        }}
      >
        {state.kind === "loading" ? "Previewing…" : "Preview 24h"}
      </button>

      {open && (
        <div style={popoverStyle}>
          <PreviewBody state={state} onClose={() => setOpen(false)} onRetry={runPreview} />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Popover body — loading / error / done states
// ---------------------------------------------------------------------------

function PreviewBody({
  state,
  onClose,
  onRetry,
}: {
  state: RunState;
  onClose: () => void;
  onRetry: () => void;
}) {
  if (state.kind === "loading") {
    return (
      <>
        <PopoverHeader title="Preview · last 24h" onClose={onClose} />
        <div style={{ padding: 16, fontSize: 12, color: "rgba(255,255,255,0.55)" }}>
          Running dry-run against recent candles…
        </div>
      </>
    );
  }

  if (state.kind === "error") {
    const isValidation = state.errors && state.errors.length > 0;
    return (
      <>
        <PopoverHeader title={state.title} onClose={onClose} />
        <div style={{ padding: 16, fontSize: 12, color: "#f85149" }}>
          <div style={{ marginBottom: 8 }}>{state.detail}</div>
          {isValidation && (
            <ul style={{ margin: 0, padding: "0 0 0 16px", color: "rgba(255,255,255,0.7)" }}>
              {state.errors!.map((e, i) => (
                <li key={i}>
                  <code style={codeStyle}>{e.field}</code>: {e.message}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div style={popoverFooterStyle}>
          <button onClick={onRetry} style={footerBtnStyle}>Retry</button>
        </div>
      </>
    );
  }

  if (state.kind === "done") {
    const { report, meta } = state.data;
    const ageMinutes = Math.round(meta.dataAgeMs / 60_000);
    const pnlColor = report.totalPnlPct >= 0 ? "#3fb950" : "#f85149";
    return (
      <>
        <PopoverHeader
          title={`Preview · ${meta.symbol} · ${meta.hours}h`}
          onClose={onClose}
        />
        <div style={{ padding: "12px 16px" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 8,
              marginBottom: 12,
            }}
          >
            <MetricCard
              label="Total PnL"
              value={`${report.totalPnlPct >= 0 ? "+" : ""}${report.totalPnlPct.toFixed(2)}%`}
              color={pnlColor}
            />
            <MetricCard label="Trades" value={String(report.trades)} />
            <MetricCard
              label="Win Rate"
              value={`${(report.winrate * 100).toFixed(1)}%`}
            />
            <MetricCard
              label="Max DD"
              value={`-${report.maxDrawdownPct.toFixed(2)}%`}
              color={report.maxDrawdownPct > 5 ? "#f85149" : undefined}
            />
          </div>

          {report.tradeLog.length >= 2 ? (
            <EquitySparkline tradeLog={report.tradeLog} />
          ) : (
            <div
              style={{
                fontSize: 11,
                color: "rgba(255,255,255,0.4)",
                textAlign: "center",
                padding: "18px 0",
              }}
            >
              Not enough trades in the window to draw an equity curve.
            </div>
          )}

          <div style={metaLineStyle}>
            {report.candles} candles · {meta.interval} · data age{" "}
            {ageMinutes <= 0 ? "<1m" : `${ageMinutes}m`}
          </div>
        </div>
      </>
    );
  }

  return null;
}

// ---------------------------------------------------------------------------
// Presentational bits
// ---------------------------------------------------------------------------

function PopoverHeader({ title, onClose }: { title: string; onClose: () => void }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 14px",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
        {title}
      </span>
      <button
        onClick={onClose}
        aria-label="Close"
        style={{
          background: "none",
          border: "none",
          color: "rgba(255,255,255,0.4)",
          cursor: "pointer",
          fontSize: 14,
          padding: 0,
          fontFamily: "inherit",
        }}
      >
        ✕
      </button>
    </div>
  );
}

function MetricCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.07)",
        borderRadius: 6,
        padding: "8px 10px",
      }}
    >
      <div
        style={{
          fontSize: 9,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          color: "rgba(255,255,255,0.35)",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 15,
          fontWeight: 700,
          color: color ?? "rgba(255,255,255,0.88)",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        }}
      >
        {value}
      </div>
    </div>
  );
}

// Inline SVG sparkline — avoids pulling lightweight-charts into this bundle.
function EquitySparkline({ tradeLog }: { tradeLog: TradeRecord[] }) {
  const width = 300;
  const height = 60;
  const pad = 4;

  const points: Array<{ t: number; v: number }> = [
    { t: tradeLog[0].entryTime, v: 0 },
  ];
  let cum = 0;
  for (const trade of tradeLog) {
    cum += trade.pnlPct;
    points.push({ t: trade.exitTime, v: cum });
  }

  const minV = Math.min(...points.map((p) => p.v));
  const maxV = Math.max(...points.map((p) => p.v));
  const rangeV = maxV - minV || 1;
  const minT = points[0].t;
  const rangeT = points[points.length - 1].t - minT || 1;

  const coords = points.map((p) => {
    const x = pad + ((p.t - minT) / rangeT) * (width - 2 * pad);
    const y = height - pad - ((p.v - minV) / rangeV) * (height - 2 * pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const pathD = `M ${coords.join(" L ")}`;
  const zeroY =
    height - pad - ((0 - minV) / rangeV) * (height - 2 * pad);
  const lineColor = cum >= 0 ? "#3fb950" : "#f85149";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      style={{
        display: "block",
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 6,
      }}
      aria-label="Cumulative equity curve"
    >
      {minV < 0 && maxV > 0 && (
        <line
          x1={pad}
          x2={width - pad}
          y1={zeroY}
          y2={zeroY}
          stroke="rgba(255,255,255,0.15)"
          strokeDasharray="2 3"
        />
      )}
      <path d={pathD} fill="none" stroke={lineColor} strokeWidth={1.5} />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Shared style tokens
// ---------------------------------------------------------------------------

const popoverStyle: React.CSSProperties = {
  position: "absolute",
  top: "calc(100% + 6px)",
  right: 0,
  width: 340,
  zIndex: 120,
  background: "rgba(14,18,24,0.98)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  boxShadow: "0 10px 30px rgba(0,0,0,0.55)",
  fontFamily: "inherit",
};

const popoverFooterStyle: React.CSSProperties = {
  padding: "8px 14px",
  borderTop: "1px solid rgba(255,255,255,0.07)",
  display: "flex",
  justifyContent: "flex-end",
};

const footerBtnStyle: React.CSSProperties = {
  padding: "4px 12px",
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 4,
  color: "rgba(255,255,255,0.8)",
  cursor: "pointer",
  fontSize: 11,
  fontFamily: "inherit",
};

const codeStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.08)",
  padding: "1px 4px",
  borderRadius: 3,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
  fontSize: 11,
};

const metaLineStyle: React.CSSProperties = {
  marginTop: 10,
  fontSize: 10,
  color: "rgba(255,255,255,0.35)",
  textAlign: "center",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
};
