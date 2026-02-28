'use client';

import { useEffect, useRef, useState } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type LineData,
  type Time,
  CrosshairMode,
} from 'lightweight-charts';
import { apiFetchNoWorkspace } from '../../app/factory/api';
import { calcMA, calcEMA, calcRSI } from './indicators';

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

const CHART_HEIGHT = 400;
const RSI_PANE_HEIGHT = 120;

const MA_PERIOD = 20;
const EMA_PERIOD = 50;
const RSI_PERIOD = 14;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalChart({ symbol, limit = 200 }: TerminalChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const ma20Ref = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50Ref = useRef<ISeriesApi<'Line'> | null>(null);
  const rsi14Ref = useRef<ISeriesApi<'Line'> | null>(null);

  const [interval, setIntervalValue] = useState<Interval>('15');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Toggle state — volume on by default, indicators off
  const [showVolume, setShowVolume] = useState(true);
  const [showMA, setShowMA] = useState(false);
  const [showEMA, setShowEMA] = useState(false);
  const [showRSI, setShowRSI] = useState(false);

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

    // ── Pane 0: Candlestick + Volume + MA + EMA ──────────────────────────

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#3fb950',
      downColor: '#f85149',
      borderUpColor: '#3fb950',
      borderDownColor: '#f85149',
      wickUpColor: '#3fb950',
      wickDownColor: '#f85149',
    });

    // Volume histogram — lower 15% of main pane
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    // MA(20) — golden line on pane 0
    const ma20 = chart.addSeries(LineSeries, {
      color: '#f0c040',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // EMA(50) — sky-blue line on pane 0
    const ema50 = chart.addSeries(LineSeries, {
      color: '#4fc3f7',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // ── Pane 1: RSI ───────────────────────────────────────────────────────
    const rsi14 = chart.addSeries(LineSeries, {
      color: '#ce93d8',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      title: 'RSI(14)',
      visible: false,
    }, 1);

    // Overbought / oversold reference lines (dashed)
    rsi14.createPriceLine({ price: 70, color: 'rgba(248,81,73,0.5)', lineWidth: 1, lineStyle: 2, title: '' });
    rsi14.createPriceLine({ price: 30, color: 'rgba(63,185,80,0.5)', lineWidth: 1, lineStyle: 2, title: '' });

    // Shrink RSI pane
    const panes = chart.panes();
    if (panes.length > 1) {
      panes[1].setHeight(RSI_PANE_HEIGHT);
    }

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    ma20Ref.current = ma20;
    ema50Ref.current = ema50;
    rsi14Ref.current = rsi14;

    // ── ResizeObserver ────────────────────────────────────────────────────
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
      ma20Ref.current = null;
      ema50Ref.current = null;
      rsi14Ref.current = null;
    };
  }, []); // run once

  // ── Toggle effects ───────────────────────────────────────────────────────
  useEffect(() => {
    volumeSeriesRef.current?.applyOptions({ visible: showVolume });
  }, [showVolume]);

  useEffect(() => {
    ma20Ref.current?.applyOptions({ visible: showMA });
  }, [showMA]);

  useEffect(() => {
    ema50Ref.current?.applyOptions({ visible: showEMA });
  }, [showEMA]);

  useEffect(() => {
    rsi14Ref.current?.applyOptions({ visible: showRSI });
  }, [showRSI]);

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
      const times = raw.map((c) => Math.floor(c.openTime / 1000) as Time);
      const closes = raw.map((c) => c.close);

      // ── Candlestick data ──
      const candleData: CandlestickData<Time>[] = raw.map((c, i) => ({
        time: times[i],
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

      // ── Volume data ──
      const volumeData: HistogramData<Time>[] = raw.map((c, i) => ({
        time: times[i],
        value: c.volume,
        color: c.close >= c.open
          ? 'rgba(63, 185, 80, 0.35)'
          : 'rgba(248, 81, 73, 0.35)',
      }));

      // ── MA(20) data ──
      const maValues = calcMA(closes, MA_PERIOD);
      const maData: LineData<Time>[] = maValues
        .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
        .filter((x): x is LineData<Time> => x !== null);

      // ── EMA(50) data ──
      const emaValues = calcEMA(closes, EMA_PERIOD);
      const emaData: LineData<Time>[] = emaValues
        .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
        .filter((x): x is LineData<Time> => x !== null);

      // ── RSI(14) data ──
      const rsiValues = calcRSI(closes, RSI_PERIOD);
      const rsiData: LineData<Time>[] = rsiValues
        .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
        .filter((x): x is LineData<Time> => x !== null);

      candleSeriesRef.current?.setData(candleData);
      volumeSeriesRef.current?.setData(volumeData);
      ma20Ref.current?.setData(maData);
      ema50Ref.current?.setData(emaData);
      rsi14Ref.current?.setData(rsiData);
      chartRef.current?.timeScale().fitContent();
    });

    return () => {
      cancelled = true;
    };
  }, [symbol, interval, limit]);

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div>
      {/* ── Timeframe selector ── */}
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
        {loading && <span style={styles.loadingHint}>Loading...</span>}
      </div>

      {/* ── Indicator toggles ── */}
      <div style={styles.toggleRow}>
        <ToggleBtn label="Vol" active={showVolume} color="#26a69a" onClick={() => setShowVolume((v) => !v)} />
        <ToggleBtn label={`MA(${MA_PERIOD})`} active={showMA} color="#f0c040" onClick={() => setShowMA((v) => !v)} />
        <ToggleBtn label={`EMA(${EMA_PERIOD})`} active={showEMA} color="#4fc3f7" onClick={() => setShowEMA((v) => !v)} />
        <ToggleBtn label={`RSI(${RSI_PERIOD})`} active={showRSI} color="#ce93d8" onClick={() => setShowRSI((v) => !v)} />
      </div>

      {/* ── Error ── */}
      {error && <p style={styles.errorMsg}>{error}</p>}

      {/* ── Chart container — explicit height required ── */}
      <div ref={containerRef} style={styles.chartContainer} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// ToggleBtn sub-component
// ---------------------------------------------------------------------------

function ToggleBtn({
  label,
  active,
  color,
  onClick,
}: {
  label: string;
  active: boolean;
  color: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        ...styles.toggleBtn,
        background: active ? color : 'var(--bg-secondary)',
        color: active ? '#fff' : 'var(--text-secondary)',
        borderColor: active ? color : 'var(--border)',
      }}
    >
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = {
  tfRow: {
    display: 'flex',
    gap: 4,
    marginBottom: 6,
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

  toggleRow: {
    display: 'flex',
    gap: 6,
    marginBottom: 8,
    flexWrap: 'wrap',
    alignItems: 'center',
  } as React.CSSProperties,

  toggleBtn: {
    padding: '3px 10px',
    fontSize: 11,
    border: '1px solid var(--border)',
    borderRadius: 4,
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'background 0.15s, color 0.15s, border-color 0.15s',
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
