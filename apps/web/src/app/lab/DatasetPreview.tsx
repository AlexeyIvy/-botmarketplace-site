"use client";

/**
 * DatasetPreview — Phase 2B
 *
 * Renders a switchable Table / Chart preview of OHLCV candle data for a dataset.
 *
 * Table: virtualized with @tanstack/react-virtual (paginated load-more).
 * Chart: OHLCV candlestick via lightweight-charts (same lib as Terminal).
 *
 * States handled:
 *  - FAILED dataset  → clear no-preview message (no API call attempted)
 *  - PARTIAL dataset → warning banner from parent is preserved; preview loads normally
 *  - loading         → spinner text
 *  - error           → error box with retry
 *  - empty           → "No data" message
 *  - loaded          → table or chart, with load-more for table pagination
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { apiFetch } from "../../lib/api";
import type { IChartApi } from "lightweight-charts";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PreviewRow {
  /** openTimeMs as string (BigInt-safe) */
  t: string;
  o: string;
  h: string;
  l: string;
  c: string;
  v: string;
}

interface PreviewResponse {
  datasetId:  string;
  page:       number;
  pageSize:   number;
  totalCount: number;
  totalPages: number;
  rows:       PreviewRow[];
}

type ViewMode = "table" | "chart";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE_SIZE = 200;
const MAX_ROWS  = 10_000;

// ---------------------------------------------------------------------------
// DatasetPreview
// ---------------------------------------------------------------------------

export function DatasetPreview({
  datasetId,
  status,
}: {
  datasetId: string;
  status:    "READY" | "PARTIAL" | "FAILED";
}) {
  const [viewMode,     setViewMode]     = useState<ViewMode>("table");
  const [rows,         setRows]         = useState<PreviewRow[]>([]);
  const [totalCount,   setTotalCount]   = useState(0);
  const [totalPages,   setTotalPages]   = useState(0);
  const [currentPage,  setCurrentPage]  = useState(0);
  const [loading,      setLoading]      = useState(false);
  const [loadingMore,  setLoadingMore]  = useState(false);
  const [error,        setError]        = useState<string | null>(null);

  const loadPage = useCallback(async (page: number, initial: boolean) => {
    if (initial) {
      setLoading(true);
      setError(null);
      setRows([]);
    } else {
      setLoadingMore(true);
    }

    const res = await apiFetch<PreviewResponse>(
      `/lab/datasets/${datasetId}/preview?page=${page}&pageSize=${PAGE_SIZE}`,
    );

    if (initial) setLoading(false);
    else         setLoadingMore(false);

    if (res.ok) {
      setRows((prev) => initial ? res.data.rows : [...prev, ...res.data.rows]);
      setTotalCount(res.data.totalCount);
      setTotalPages(res.data.totalPages);
      setCurrentPage(page);
    } else {
      setError(res.problem?.detail ?? res.problem?.title ?? "Failed to load preview");
    }
  }, [datasetId]);

  // Load first page on mount — skip if dataset FAILED (no usable rows)
  useEffect(() => {
    if (status === "FAILED") return;
    loadPage(1, true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, status]);

  // ── FAILED state ───────────────────────────────────────────────────────────
  if (status === "FAILED") {
    return (
      <div style={errorBoxStyle}>
        Preview not available — this dataset failed to fetch.
        Check the quality details above or create a new dataset.
      </div>
    );
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return <div style={stateTextStyle}>Loading preview…</div>;
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div style={errorBoxStyle}>
        Preview error: {error}
        <button onClick={() => loadPage(1, true)} style={retryBtnStyle}>Retry</button>
      </div>
    );
  }

  // ── Empty ──────────────────────────────────────────────────────────────────
  if (rows.length === 0) {
    return <div style={stateTextStyle}>No candle data available for this dataset.</div>;
  }

  const canLoadMore = currentPage < totalPages && rows.length < MAX_ROWS;

  // ── Preview ────────────────────────────────────────────────────────────────
  return (
    <div style={{ marginTop: 20 }}>
      {/* Header */}
      <div style={previewHeaderStyle}>
        <span style={labelSmStyle}>Preview</span>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>
            {rows.length.toLocaleString()} / {totalCount.toLocaleString()} candles
          </span>
          <div style={toggleGroupStyle}>
            <button style={toggleBtnStyle(viewMode === "table")} onClick={() => setViewMode("table")}>
              Table
            </button>
            <button style={toggleBtnStyle(viewMode === "chart")} onClick={() => setViewMode("chart")}>
              Chart
            </button>
          </div>
        </div>
      </div>

      {viewMode === "table" ? (
        <PreviewTable
          rows={rows}
          canLoadMore={canLoadMore}
          loadingMore={loadingMore}
          onLoadMore={() => loadPage(currentPage + 1, false)}
        />
      ) : (
        <PreviewChart rows={rows} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// PreviewTable — virtualized OHLCV rows with load-more pagination
// ---------------------------------------------------------------------------

function PreviewTable({
  rows,
  canLoadMore,
  loadingMore,
  onLoadMore,
}: {
  rows:        PreviewRow[];
  canLoadMore: boolean;
  loadingMore: boolean;
  onLoadMore:  () => void;
}) {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count:           rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize:    () => 30,
    overscan:        15,
  });

  return (
    <div>
      {/* Column headers */}
      <div style={tableHeaderStyle}>
        {["Date / Time (UTC)", "Open", "High", "Low", "Close", "Volume"].map((col) => (
          <div key={col} style={thStyle}>{col}</div>
        ))}
      </div>

      {/* Virtualized scroll container */}
      <div
        ref={parentRef}
        style={{
          height:       360,
          overflow:     "auto",
          border:       "1px solid var(--border)",
          borderTop:    "none",
          borderRadius: "0 0 6px 6px",
        }}
      >
        <div style={{ height: rowVirtualizer.getTotalSize(), position: "relative" }}>
          {rowVirtualizer.getVirtualItems().map((vRow) => {
            const r    = rows[vRow.index]!;
            const ts   = new Date(Number(r.t)).toUTCString().replace(/ GMT$/, "").slice(5);
            const isUp = parseFloat(r.c) >= parseFloat(r.o);
            return (
              <div
                key={vRow.key}
                style={{
                  position:        "absolute",
                  top:             0,
                  left:            0,
                  width:           "100%",
                  height:          vRow.size,
                  transform:       `translateY(${vRow.start}px)`,
                  display:         "grid",
                  gridTemplateColumns: TABLE_COLS,
                  alignItems:      "center",
                  borderBottom:    "1px solid rgba(255,255,255,0.04)",
                  background:      vRow.index % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)",
                }}
              >
                <div style={tdStyle}>{ts}</div>
                <div style={tdStyle}>{fmt(r.o)}</div>
                <div style={{ ...tdStyle, color: "#3fb950" }}>{fmt(r.h)}</div>
                <div style={{ ...tdStyle, color: "#f85149" }}>{fmt(r.l)}</div>
                <div style={{ ...tdStyle, color: isUp ? "#3fb950" : "#f85149", fontWeight: 500 }}>
                  {fmt(r.c)}
                </div>
                <div style={{ ...tdStyle, color: "var(--text-secondary)" }}>{fmtVol(r.v)}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Load-more footer */}
      {canLoadMore && (
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={onLoadMore} disabled={loadingMore} style={loadMoreBtnStyle}>
            {loadingMore ? "Loading…" : "Load more"}
          </button>
          <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>
            {rows.length.toLocaleString()} rows loaded
          </span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// PreviewChart — OHLCV candlestick chart via lightweight-charts
// ---------------------------------------------------------------------------

function PreviewChart({ rows }: { rows: PreviewRow[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartApiRef  = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || rows.length === 0) return;

    let mounted = true;

    // Dynamic import avoids SSR issues (lightweight-charts is browser-only)
    import("lightweight-charts").then(({ createChart, CandlestickSeries }) => {
      if (!mounted || !containerRef.current) return;

      const chart = createChart(containerRef.current, {
        autoSize: true,
        layout: {
          background: { color: "#0d1117" },
          textColor:  "#8b949e",
        },
        grid: {
          vertLines: { color: "#21262d" },
          horzLines: { color: "#21262d" },
        },
        rightPriceScale: { borderColor: "#30363d" },
        timeScale:        { borderColor: "#30363d", timeVisible: true },
      });

      const series = chart.addSeries(CandlestickSeries, {
        upColor:        "#3fb950",
        downColor:      "#f85149",
        borderUpColor:  "#3fb950",
        borderDownColor:"#f85149",
        wickUpColor:    "#3fb950",
        wickDownColor:  "#f85149",
      });

      // Convert ms timestamps → unix seconds (lightweight-charts Time format)
      const data = rows
        .map((r) => ({
          time:  Math.floor(Number(r.t) / 1000) as import("lightweight-charts").Time,
          open:  parseFloat(r.o),
          high:  parseFloat(r.h),
          low:   parseFloat(r.l),
          close: parseFloat(r.c),
        }))
        .sort((a, b) => (a.time as number) - (b.time as number));

      series.setData(data);
      chart.timeScale().fitContent();
      chartApiRef.current = chart;
    });

    return () => {
      mounted = false;
      chartApiRef.current?.remove();
      chartApiRef.current = null;
    };
  }, [rows]);

  if (rows.length === 0) {
    return <div style={stateTextStyle}>No data to chart.</div>;
  }

  return (
    <div
      ref={containerRef}
      style={{
        height:     380,
        border:     "1px solid var(--border)",
        borderRadius: 6,
        overflow:   "hidden",
        background: "#0d1117",
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

function fmt(s: string): string {
  const n = parseFloat(s);
  if (!isFinite(n)) return s;
  // Trim to 6 significant digits, no trailing zeros
  return parseFloat(n.toPrecision(6)).toString();
}

function fmtVol(s: string): string {
  const n = parseFloat(s);
  if (!isFinite(n)) return s;
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000)     return (n / 1_000).toFixed(2) + "K";
  return n.toFixed(2);
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const TABLE_COLS = "2fr 1fr 1fr 1fr 1fr 1fr";

const tableHeaderStyle: React.CSSProperties = {
  display:             "grid",
  gridTemplateColumns: TABLE_COLS,
  border:              "1px solid var(--border)",
  borderBottom:        "none",
  borderRadius:        "6px 6px 0 0",
  background:          "rgba(255,255,255,0.04)",
};

const thStyle: React.CSSProperties = {
  padding:       "6px 8px",
  fontSize:      10,
  fontWeight:    600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color:         "var(--text-secondary)",
};

const tdStyle: React.CSSProperties = {
  padding:      "0 8px",
  fontSize:     11,
  fontFamily:   "monospace",
  color:        "var(--text-primary)",
  overflow:     "hidden",
  textOverflow: "ellipsis",
  whiteSpace:   "nowrap",
};

const previewHeaderStyle: React.CSSProperties = {
  display:        "flex",
  alignItems:     "center",
  justifyContent: "space-between",
  marginBottom:   10,
};

const labelSmStyle: React.CSSProperties = {
  fontSize:      11,
  fontWeight:    600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color:         "var(--text-secondary)",
};

const toggleGroupStyle: React.CSSProperties = {
  display:  "flex",
  border:   "1px solid rgba(255,255,255,0.12)",
  borderRadius: 5,
  overflow: "hidden",
};

function toggleBtnStyle(active: boolean): React.CSSProperties {
  return {
    padding:    "4px 12px",
    fontSize:   11,
    fontWeight: active ? 600 : 400,
    background: active ? "rgba(88,166,255,0.15)" : "transparent",
    color:      active ? "var(--accent, #58a6ff)" : "var(--text-secondary)",
    border:     "none",
    cursor:     "pointer",
    transition: "background 0.15s",
  };
}

const stateTextStyle: React.CSSProperties = {
  padding:  "16px 0",
  fontSize: 12,
  color:    "var(--text-secondary)",
};

const errorBoxStyle: React.CSSProperties = {
  background:   "rgba(248,81,73,0.12)",
  border:       "1px solid rgba(248,81,73,0.4)",
  borderRadius: 6,
  padding:      "10px 14px",
  fontSize:     12,
  color:        "#f85149",
  marginTop:    16,
};

const retryBtnStyle: React.CSSProperties = {
  marginLeft:   12,
  fontSize:     11,
  color:        "#f85149",
  background:   "none",
  border:       "1px solid rgba(248,81,73,0.4)",
  borderRadius: 4,
  padding:      "2px 8px",
  cursor:       "pointer",
};

const loadMoreBtnStyle: React.CSSProperties = {
  background:   "rgba(255,255,255,0.07)",
  color:        "var(--text-secondary)",
  border:       "1px solid rgba(255,255,255,0.12)",
  borderRadius: 5,
  padding:      "5px 12px",
  fontSize:     11,
  cursor:       "pointer",
};
