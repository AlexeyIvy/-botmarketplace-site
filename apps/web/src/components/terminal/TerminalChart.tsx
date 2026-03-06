'use client';

import { useEffect, useRef, useState } from 'react';
import {
  createChart,
  createSeriesMarkers,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type CandlestickData,
  type HistogramData,
  type LineData,
  type SeriesMarker,
  type Time,
  CrosshairMode,
} from 'lightweight-charts';
import { apiFetchNoWorkspace } from '../../lib/api';
import {
  calcMA,
  calcEMA,
  calcRSI,
  calcBB,
  calcMACD,
  type ActiveIndicator,
} from './indicators';

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

export interface ChartMarker {
  /** Unix seconds */
  time: number;
  side: 'BUY' | 'SELL';
}

export interface TerminalChartProps {
  /** Symbol to display, e.g. "BTCUSDT". Re-fetches when changed. */
  symbol: string;
  /** Number of candles to fetch (1–1000). Default: 200. */
  limit?: number;
  /** Trade markers to overlay on the chart. */
  markers?: ChartMarker[];
  /**
   * Active indicators driven by the framework.
   * Each item has: { id, params } where id is one of "ma"|"ema"|"bb"|"rsi"|"macd".
   */
  activeIndicators?: ActiveIndicator[];
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

// ---------------------------------------------------------------------------
// Cached data ref shape
// ---------------------------------------------------------------------------

interface CachedCandles {
  times: Time[];
  closes: number[];
  raw: Candle[];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalChart({
  symbol,
  limit = 200,
  markers,
  activeIndicators = [],
}: TerminalChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  // Overlay series (pane 0)
  const maRef = useRef<ISeriesApi<'Line'> | null>(null);
  const emaRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbMidRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<'Line'> | null>(null);
  // Oscillator series (pane 1)
  const rsiRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdLineRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdSignalRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdHistRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  const markersPluginRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const lastCandlesRef = useRef<CachedCandles | null>(null);

  const [interval, setIntervalValue] = useState<Interval>('15');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Volume stays as a standalone toggle (not part of indicator framework)
  const [showVolume, setShowVolume] = useState(true);

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
      crosshair: { mode: CrosshairMode.Magnet },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
    });

    // ── Pane 0: Candlestick ───────────────────────────────────────────────
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
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });

    // MA — golden (pane 0, hidden initially)
    const maSeries = chart.addSeries(LineSeries, {
      color: '#f0c040',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // EMA — sky blue (pane 0, hidden initially)
    const emaSeries = chart.addSeries(LineSeries, {
      color: '#4fc3f7',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // BB upper — magenta dashed (pane 0, hidden)
    const bbUpperSeries = chart.addSeries(LineSeries, {
      color: 'rgba(206,147,216,0.7)',
      lineWidth: 1,
      lineStyle: 1, // dashed
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // BB mid — magenta solid (pane 0, hidden)
    const bbMidSeries = chart.addSeries(LineSeries, {
      color: '#ce93d8',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // BB lower — magenta dashed (pane 0, hidden)
    const bbLowerSeries = chart.addSeries(LineSeries, {
      color: 'rgba(206,147,216,0.7)',
      lineWidth: 1,
      lineStyle: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: false,
    }, 0);

    // ── Pane 1: Oscillators (RSI + MACD) ─────────────────────────────────
    const rsiSeries = chart.addSeries(LineSeries, {
      color: '#ce93d8',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      title: 'RSI',
      visible: false,
    }, 1);
    rsiSeries.createPriceLine({ price: 70, color: 'rgba(248,81,73,0.5)', lineWidth: 1, lineStyle: 2, title: '' });
    rsiSeries.createPriceLine({ price: 30, color: 'rgba(63,185,80,0.5)', lineWidth: 1, lineStyle: 2, title: '' });

    const macdLineSeries = chart.addSeries(LineSeries, {
      color: '#60a5fa',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      title: 'MACD',
      visible: false,
    }, 1);

    const macdSignalSeries = chart.addSeries(LineSeries, {
      color: '#f0c040',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      title: 'Signal',
      visible: false,
    }, 1);

    const macdHistSeries = chart.addSeries(HistogramSeries, {
      color: '#3fb950',
      priceLineVisible: false,
      lastValueVisible: false,
      title: 'Hist',
      visible: false,
    }, 1);

    // Shrink oscillator pane
    const panes = chart.panes();
    if (panes.length > 1) panes[1].setHeight(RSI_PANE_HEIGHT);

    // ── Trade markers plugin ──────────────────────────────────────────────
    const markersPlugin = createSeriesMarkers(candleSeries);

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    maRef.current = maSeries;
    emaRef.current = emaSeries;
    bbUpperRef.current = bbUpperSeries;
    bbMidRef.current = bbMidSeries;
    bbLowerRef.current = bbLowerSeries;
    rsiRef.current = rsiSeries;
    macdLineRef.current = macdLineSeries;
    macdSignalRef.current = macdSignalSeries;
    macdHistRef.current = macdHistSeries;
    markersPluginRef.current = markersPlugin;

    // ── ResizeObserver ────────────────────────────────────────────────────
    const observer = new ResizeObserver(() => {
      if (el && chartRef.current) {
        chartRef.current.resize(el.clientWidth, el.clientHeight);
      }
    });
    observer.observe(el);

    return () => {
      observer.disconnect();
      markersPlugin.detach();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      maRef.current = null;
      emaRef.current = null;
      bbUpperRef.current = null;
      bbMidRef.current = null;
      bbLowerRef.current = null;
      rsiRef.current = null;
      macdLineRef.current = null;
      macdSignalRef.current = null;
      macdHistRef.current = null;
      markersPluginRef.current = null;
    };
  }, []); // run once

  // ── Volume toggle ────────────────────────────────────────────────────────
  useEffect(() => {
    volumeSeriesRef.current?.applyOptions({ visible: showVolume });
  }, [showVolume]);

  // ── Apply indicators to cached data (when activeIndicators prop changes) ─
  useEffect(() => {
    if (lastCandlesRef.current) {
      applyIndicators(lastCandlesRef.current, activeIndicators);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndicators]);

  // ── Markers effect ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!markersPluginRef.current) return;
    const seriesMarkers: SeriesMarker<Time>[] = (markers ?? []).map((m) => ({
      time: m.time as Time,
      position: m.side === 'BUY' ? 'belowBar' : 'aboveBar',
      shape: m.side === 'BUY' ? 'arrowUp' : 'arrowDown',
      color: m.side === 'BUY' ? '#3fb950' : '#f85149',
      size: 1,
    }));
    markersPluginRef.current.setMarkers(seriesMarkers);
  }, [markers]);

  // ── Compute and apply all indicator series from cached candle data ───────
  function applyIndicators(cached: CachedCandles, indicators: ActiveIndicator[]) {
    const { times, closes } = cached;

    const active = new Set(indicators.map((i) => i.id));
    const paramsFor = (id: string): ActiveIndicator['params'] =>
      indicators.find((i) => i.id === id)?.params ?? {};

    // ── MA ──
    const maActive = active.has('ma');
    if (maActive) {
      const p = paramsFor('ma');
      const period = Math.max(2, p.period ?? 20);
      const vals = calcMA(closes, period);
      const data: LineData<Time>[] = vals
        .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
        .filter((x): x is LineData<Time> => x !== null);
      maRef.current?.setData(data);
      maRef.current?.applyOptions({ title: `MA(${period})` });
    }
    maRef.current?.applyOptions({ visible: maActive });

    // ── EMA ──
    const emaActive = active.has('ema');
    if (emaActive) {
      const p = paramsFor('ema');
      const period = Math.max(2, p.period ?? 50);
      const vals = calcEMA(closes, period);
      const data: LineData<Time>[] = vals
        .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
        .filter((x): x is LineData<Time> => x !== null);
      emaRef.current?.setData(data);
      emaRef.current?.applyOptions({ title: `EMA(${period})` });
    }
    emaRef.current?.applyOptions({ visible: emaActive });

    // ── Bollinger Bands ──
    const bbActive = active.has('bb');
    if (bbActive) {
      const p = paramsFor('bb');
      const period = Math.max(2, p.period ?? 20);
      const std = Math.max(0.1, p.stdDev ?? 2);
      const bb = calcBB(closes, period, std);
      const toLineData = (arr: (number | null)[]): LineData<Time>[] =>
        arr
          .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
          .filter((x): x is LineData<Time> => x !== null);
      bbUpperRef.current?.setData(toLineData(bb.upper));
      bbMidRef.current?.setData(toLineData(bb.mid));
      bbLowerRef.current?.setData(toLineData(bb.lower));
      bbMidRef.current?.applyOptions({ title: `BB(${period},${std})` });
    }
    bbUpperRef.current?.applyOptions({ visible: bbActive });
    bbMidRef.current?.applyOptions({ visible: bbActive });
    bbLowerRef.current?.applyOptions({ visible: bbActive });

    // ── RSI ──
    const rsiActive = active.has('rsi');
    if (rsiActive) {
      const p = paramsFor('rsi');
      const period = Math.max(2, p.period ?? 14);
      const vals = calcRSI(closes, period);
      const data: LineData<Time>[] = vals
        .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
        .filter((x): x is LineData<Time> => x !== null);
      rsiRef.current?.setData(data);
      rsiRef.current?.applyOptions({ title: `RSI(${period})` });
    }
    rsiRef.current?.applyOptions({ visible: rsiActive });

    // ── MACD ──
    const macdActive = active.has('macd');
    if (macdActive) {
      const p = paramsFor('macd');
      const fast = Math.max(2, p.fastPeriod ?? 12);
      const slow = Math.max(fast + 1, p.slowPeriod ?? 26);
      const sig = Math.max(2, p.signalPeriod ?? 9);
      const macd = calcMACD(closes, fast, slow, sig);
      const toLineData = (arr: (number | null)[]): LineData<Time>[] =>
        arr
          .map((v, i) => (v !== null ? { time: times[i], value: v } : null))
          .filter((x): x is LineData<Time> => x !== null);
      macdLineRef.current?.setData(toLineData(macd.macd));
      macdSignalRef.current?.setData(toLineData(macd.signal));
      // Histogram with red/green coloring
      const histData: HistogramData<Time>[] = macd.hist
        .map((v, i) =>
          v !== null
            ? ({ time: times[i], value: v, color: v >= 0 ? '#3fb950' : '#f85149' } as HistogramData<Time>)
            : null,
        )
        .filter((x): x is HistogramData<Time> => x !== null);
      macdHistRef.current?.setData(histData);
      macdLineRef.current?.applyOptions({ title: `MACD(${fast},${slow},${sig})` });
    }
    macdLineRef.current?.applyOptions({ visible: macdActive });
    macdSignalRef.current?.applyOptions({ visible: macdActive });
    macdHistRef.current?.applyOptions({ visible: macdActive });
  }

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

      const times = raw.map((c) => Math.floor(c.openTime / 1000) as Time);
      const closes = raw.map((c) => c.close);

      // Candlestick
      const candleData: CandlestickData<Time>[] = raw.map((c, i) => ({
        time: times[i],
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

      // Volume
      const volumeData: HistogramData<Time>[] = raw.map((c, i) => ({
        time: times[i],
        value: c.volume,
        color: c.close >= c.open ? 'rgba(63,185,80,0.35)' : 'rgba(248,81,73,0.35)',
      }));

      candleSeriesRef.current?.setData(candleData);
      volumeSeriesRef.current?.setData(volumeData);

      // Cache and apply indicators
      const cached: CachedCandles = { times, closes, raw };
      lastCandlesRef.current = cached;
      applyIndicators(cached, activeIndicators);

      chartRef.current?.timeScale().fitContent();
    });

    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

        {/* Volume toggle */}
        <button
          onClick={() => setShowVolume((v) => !v)}
          style={{
            ...styles.toggleBtn,
            background: showVolume ? '#26a69a' : 'var(--bg-secondary)',
            color: showVolume ? '#fff' : 'var(--text-secondary)',
            borderColor: showVolume ? '#26a69a' : 'var(--border)',
            marginLeft: 8,
          }}
        >
          Vol
        </button>

        {loading && <span style={styles.loadingHint}>Loading...</span>}
      </div>

      {/* ── Error ── */}
      {error && <p style={styles.errorMsg}>{error}</p>}

      {/* ── Chart container — explicit height required ── */}
      <div ref={containerRef} style={styles.chartContainer} />
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

  toggleBtn: {
    padding: '3px 10px',
    fontSize: 11,
    border: '1px solid var(--border)',
    borderRadius: 4,
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'background 0.15s, color 0.15s, border-color 0.15s',
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
