'use client';

import { useEffect, useRef, useState } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type Time,
  CrosshairMode,
} from 'lightweight-charts';
import { apiFetchNoWorkspace } from '../../app/factory/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Candle {
  openTime: number; // milliseconds (API)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TerminalChartProps {
  /** Symbol to display, e.g. "BTCUSDT". Re-fetches when changed. */
  symbol: string;
  /** Number of candles to fetch (1–1000). Default: 200. */
  limit?: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVALS = ['1', '5', '15', '30', '60', '240', 'D'] as const;
type Interval = (typeof INTERVALS)[number];

function fmtInterval(iv: string) {
  return iv === 'D' ? '1D' : `${iv}m`;
}

const CHART_HEIGHT = 440;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalChart({ symbol, limit = 200 }: TerminalChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  const [interval, setIntervalValue] = useState<Interval>('15');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Create chart once on mount ──────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: CHART_HEIGHT,
      layout: {
        background: { color: 'transparent' },
        textColor: '#888',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.06)' },
        horzLines: { color: 'rgba(255,255,255,0.06)' },
      },
      crosshair: {
        mode: CrosshairMode.Magnet,
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.1)',
      },
    });

    // Candlestick series (v5 API: addSeries with series definition)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#3fb950',
      downColor: '#f85149',
      borderUpColor: '#3fb950',
      borderDownColor: '#f85149',
      wickUpColor: '#3fb950',
      wickDownColor: '#f85149',
    });

    // Volume histogram — overlay on separate price scale to stay small at bottom
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // ── ResizeObserver — CRITICAL for responsive layout ──────────────────
    const observer = new ResizeObserver(() => {
      if (el && chartRef.current) {
        chartRef.current.resize(el.clientWidth, el.clientHeight);
      }
    });
    observer.observe(el);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []); // run once

  // ── Load data when symbol or interval changes ───────────────────────────
  useEffect(() => {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    const lim = Math.min(Math.max(1, limit), 1000);

    apiFetchNoWorkspace<Candle[]>(
      `/terminal/candles?symbol=${encodeURIComponent(sym)}&interval=${interval}&limit=${lim}`,
    ).then((res) => {
      if (cancelled) return;
      setLoading(false);

      if (!res.ok) {
        setError(`${res.problem.title}: ${res.problem.detail}`);
        return;
      }

      const raw = res.data;
      if (!raw.length) return;

      // CRITICAL: API openTime is milliseconds → lightweight-charts needs seconds
      const candleData: CandlestickData<Time>[] = raw.map((c) => ({
        time: Math.floor(c.openTime / 1000) as Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

      const volumeData: HistogramData<Time>[] = raw.map((c) => ({
        time: Math.floor(c.openTime / 1000) as Time,
        value: c.volume,
        color: c.close >= c.open
          ? 'rgba(63, 185, 80, 0.35)'
          : 'rgba(248, 81, 73, 0.35)',
      }));

      candleSeriesRef.current?.setData(candleData);
      volumeSeriesRef.current?.setData(volumeData);
      chartRef.current?.timeScale().fitContent();
    });

    return () => {
      cancelled = true;
    };
  }, [symbol, interval, limit]);

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div>
      {/* Timeframe selector */}
      <div style={styles.tfRow}>
        {INTERVALS.map((iv) => (
          <button
            key={iv}
            onClick={() => setIntervalValue(iv)}
            style={{
              ...styles.tfBtn,
              background: iv === interval ? 'var(--accent, #0969da)' : 'var(--bg-secondary)',
              color: iv === interval ? '#fff' : 'var(--text-secondary)',
              fontWeight: iv === interval ? 700 : 400,
            }}
          >
            {fmtInterval(iv)}
          </button>
        ))}
        {loading && (
          <span style={styles.loadingHint}>Loading...</span>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p style={styles.errorMsg}>{error}</p>
      )}

      {/* Chart container — explicit height required (zero-height = blank chart) */}
      <div
        ref={containerRef}
        style={styles.chartContainer}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = {
  tfRow: {
    display: 'flex',
    gap: 4,
    marginBottom: 8,
    flexWrap: 'wrap',
    alignItems: 'center',
  } as React.CSSProperties,

  tfBtn: {
    padding: '4px 10px',
    fontSize: 12,
    border: '1px solid var(--border)',
    borderRadius: 4,
    cursor: 'pointer',
    transition: 'background 0.15s, color 0.15s',
  } as React.CSSProperties,

  loadingHint: {
    fontSize: 12,
    color: 'var(--text-secondary)',
    marginLeft: 8,
  } as React.CSSProperties,

  errorMsg: {
    color: '#f85149',
    fontSize: 13,
    marginBottom: 8,
    marginTop: 0,
  } as React.CSSProperties,

  chartContainer: {
    width: '100%',
    height: CHART_HEIGHT,
    borderRadius: 6,
    overflow: 'hidden',
  } as React.CSSProperties,
} as const;
