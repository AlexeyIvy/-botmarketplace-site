"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiFetchNoWorkspace, apiFetch, getToken } from "../../lib/api";
import TerminalChart, { type ChartMarker } from "../../components/terminal/TerminalChart";
import {
  INDICATOR_REGISTRY,
  type ActiveIndicator,
} from "../../components/terminal/indicators";

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

interface ExchangeConnection {
  id: string;
  name: string;
  exchange: string;
  status: string;
}

interface TerminalOrder {
  id: string;
  symbol: string;
  side: string;
  type: string;
  qty: string;
  price: string | null;
  status: string;
  exchangeOrderId: string | null;
  error: string | null;
  createdAt: string;
}

type LoadState = "idle" | "loading" | "success" | "error";
type OrderState = "idle" | "loading" | "success" | "error";
type BottomTab = "ticker" | "orders" | "candles";

interface SymbolInfo {
  symbol: string;
  base: string;
  quote: string;
  status: string;
}

interface WatchlistQuote {
  symbol: string;
  lastPrice: string;
  price24hPcnt: string;
  prevLastPrice?: string; // for up/down hint
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SUPPORTED_EXCHANGES = ["bybit"] as const;
const SUPPORTED_MARKETS = ["linear", "spot"] as const;
type SupportedExchange = (typeof SUPPORTED_EXCHANGES)[number];
type SupportedMarket = (typeof SUPPORTED_MARKETS)[number];

const DEFAULT_EXCHANGE: SupportedExchange = "bybit";
const DEFAULT_MARKET: SupportedMarket = "linear";
const DEFAULT_SYMBOL = "BTCUSDT";
const DEFAULT_INTERVAL = "15";

const DEFAULT_WATCHLIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"];
const MAX_WATCHLIST = 30;
const POLL_INTERVAL_MS = 2000;

// ---------------------------------------------------------------------------
// Preferences helpers (Stage 20c extended for 20d)
// ---------------------------------------------------------------------------

const PREFS_LS_KEY = "terminalPrefsV1";
const PREFS_IMPORTED_KEY = "terminalPrefsImported";

interface MarketPrefs {
  watchlist: string[];
  activeSymbol?: string;
  interval?: string;
  indicators?: ActiveIndicator[];
  layout?: { showWatchlist?: boolean; showOrderPanel?: boolean };
}

interface TerminalJson {
  version: 1;
  selectedExchange?: string;
  selectedMarket?: string;
  terminal: Record<string, MarketPrefs>;
}

function marketKey(exchange: string, market: string) {
  return `${exchange}:${market}`;
}

const DEFAULT_PREFS: TerminalJson = {
  version: 1,
  selectedExchange: DEFAULT_EXCHANGE,
  selectedMarket: DEFAULT_MARKET,
  terminal: {
    [marketKey(DEFAULT_EXCHANGE, DEFAULT_MARKET)]: {
      watchlist: [...DEFAULT_WATCHLIST],
      activeSymbol: DEFAULT_SYMBOL,
      interval: DEFAULT_INTERVAL,
      indicators: [],
      layout: { showWatchlist: true, showOrderPanel: true },
    },
  },
};

function loadGuestPrefs(): TerminalJson | null {
  try {
    const raw = localStorage.getItem(PREFS_LS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as TerminalJson;
    if (parsed?.version === 1 && parsed?.terminal) return parsed;
  } catch {
    // ignore
  }
  return null;
}

function saveGuestPrefs(prefs: TerminalJson) {
  try {
    localStorage.setItem(PREFS_LS_KEY, JSON.stringify(prefs));
  } catch {
    // ignore
  }
}

function isDefaultOrEmpty(terminalJson: unknown): boolean {
  if (!terminalJson || typeof terminalJson !== "object") return true;
  const tj = terminalJson as TerminalJson;
  if (!tj.terminal) return true;
  return Object.keys(tj.terminal).length === 0;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalPage() {
  const router = useRouter();

  // --- Auth state ---
  const [hasToken, setHasToken] = useState<boolean | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    setHasToken(!!getToken());
  }, []);

  // --- Exchange + Market selection ---
  const [selectedExchange, setSelectedExchange] = useState<SupportedExchange>(DEFAULT_EXCHANGE);
  const [selectedMarket, setSelectedMarket] = useState<SupportedMarket>(DEFAULT_MARKET);

  // --- Symbols directory ---
  const [allSymbols, setAllSymbols] = useState<SymbolInfo[]>([]);
  const [symbolsLoading, setSymbolsLoading] = useState(false);
  const [symbolSearch, setSymbolSearch] = useState("");
  const [showPicker, setShowPicker] = useState(false);

  // --- Market Data state ---
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [interval, setInterval] = useState(DEFAULT_INTERVAL);
  const [limit, setLimit] = useState("50");

  const [tickerState, setTickerState] = useState<LoadState>("idle");
  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [tickerError, setTickerError] = useState<string | null>(null);

  const [candlesState, setCandlesState] = useState<LoadState>("idle");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [candlesError, setCandlesError] = useState<string | null>(null);

  // --- Order state ---
  const [connections, setConnections] = useState<ExchangeConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState("");
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [orderQty, setOrderQty] = useState("");
  const [orderPrice, setOrderPrice] = useState("");
  const [orderState, setOrderState] = useState<OrderState>("idle");
  const [lastOrder, setLastOrder] = useState<TerminalOrder | null>(null);
  const [orderError, setOrderError] = useState<string | null>(null);

  // --- Orders history (for markers + tab) ---
  const [allOrders, setAllOrders] = useState<TerminalOrder[]>([]);
  const [markers, setMarkers] = useState<ChartMarker[]>([]);

  // --- Watchlist + polling ---
  const [watchlist, setWatchlist] = useState<string[]>([...DEFAULT_WATCHLIST]);
  const [watchlistQuotes, setWatchlistQuotes] = useState<Record<string, WatchlistQuote>>({});
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // --- Indicator state (Stage 20e) ---
  const [activeIndicators, setActiveIndicators] = useState<ActiveIndicator[]>([]);
  const [indicatorModal, setIndicatorModal] = useState<ActiveIndicator | null>(null);
  const [showIndicatorAdd, setShowIndicatorAdd] = useState(false);

  // --- Layout state ---
  const [showWatchlist, setShowWatchlist] = useState(true);
  const [showOrderPanel, setShowOrderPanel] = useState(true);
  const [bottomTab, setBottomTab] = useState<BottomTab>("ticker");

  // Mobile: collapse panels by default on small screens
  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setShowWatchlist(false);
      setShowOrderPanel(false);
    }
  }, []);

  // --- Preferences sync (Stage 20c extended) ---
  const prefsSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prefsLoaded = useRef(false);

  const currentMktKey = marketKey(selectedExchange, selectedMarket);

  /** Build current prefs snapshot */
  const buildPrefs = useCallback((): TerminalJson => ({
    version: 1,
    selectedExchange,
    selectedMarket,
    terminal: {
      [currentMktKey]: {
        watchlist: [...watchlist],
        activeSymbol: symbol,
        interval,
        indicators: activeIndicators,
        layout: { showWatchlist, showOrderPanel },
      },
    },
  }), [selectedExchange, selectedMarket, currentMktKey, watchlist, symbol, interval, activeIndicators, showWatchlist, showOrderPanel]);

  /** Apply a loaded TerminalJson to local state */
  function applyPrefs(tj: TerminalJson) {
    if (tj.selectedExchange && SUPPORTED_EXCHANGES.includes(tj.selectedExchange as SupportedExchange)) {
      setSelectedExchange(tj.selectedExchange as SupportedExchange);
    }
    if (tj.selectedMarket && SUPPORTED_MARKETS.includes(tj.selectedMarket as SupportedMarket)) {
      setSelectedMarket(tj.selectedMarket as SupportedMarket);
    }
    // Load prefs for the saved market key
    const mktKey = marketKey(
      tj.selectedExchange ?? DEFAULT_EXCHANGE,
      tj.selectedMarket ?? DEFAULT_MARKET,
    );
    const mkt = tj.terminal?.[mktKey] ?? tj.terminal?.[marketKey(DEFAULT_EXCHANGE, DEFAULT_MARKET)];
    if (!mkt) return;
    if (mkt.activeSymbol) setSymbol(mkt.activeSymbol);
    if (mkt.interval) setInterval(mkt.interval);
    if (Array.isArray(mkt.watchlist) && mkt.watchlist.length > 0) {
      setWatchlist(mkt.watchlist.slice(0, MAX_WATCHLIST));
    }
    if (mkt.layout) {
      if (typeof mkt.layout.showWatchlist === "boolean") setShowWatchlist(mkt.layout.showWatchlist);
      if (typeof mkt.layout.showOrderPanel === "boolean") setShowOrderPanel(mkt.layout.showOrderPanel);
    }
    // Restore saved indicators — validate against registry
    if (Array.isArray(mkt.indicators)) {
      const validIds = new Set(INDICATOR_REGISTRY.map((d) => d.id));
      const restored = (mkt.indicators as ActiveIndicator[]).filter(
        (ind) => ind && typeof ind.id === "string" && validIds.has(ind.id),
      );
      if (restored.length > 0) setActiveIndicators(restored);
    }
  }

  /** Debounced save — guest or authed */
  const schedulePrefsWrite = useCallback((prefs: TerminalJson) => {
    if (prefsSaveTimer.current) clearTimeout(prefsSaveTimer.current);
    prefsSaveTimer.current = setTimeout(() => {
      if (getToken()) {
        apiFetchNoWorkspace("/user/preferences", {
          method: "PUT",
          body: JSON.stringify({ terminalJson: prefs }),
        }).catch(() => undefined);
      } else {
        saveGuestPrefs(prefs);
      }
    }, 1500);
  }, []);

  // Load preferences on mount
  useEffect(() => {
    if (prefsLoaded.current) return;
    prefsLoaded.current = true;

    if (getToken()) {
      // Auth mode: fetch from server
      apiFetchNoWorkspace<{ terminalJson: TerminalJson }>("/user/preferences").then((res) => {
        if (!res.ok) return;
        const serverEmpty = isDefaultOrEmpty(res.data.terminalJson);

        if (serverEmpty) {
          // Try to auto-import guest prefs once
          const guestImported = localStorage.getItem(PREFS_IMPORTED_KEY);
          const guest = guestImported ? null : loadGuestPrefs();
          if (guest && !guestImported) {
            apiFetchNoWorkspace("/user/preferences", {
              method: "PUT",
              body: JSON.stringify({ terminalJson: guest }),
            }).then(() => {
              localStorage.setItem(PREFS_IMPORTED_KEY, "1");
              applyPrefs(guest);
            }).catch(() => undefined);
          } else {
            applyPrefs(DEFAULT_PREFS);
          }
        } else {
          applyPrefs(res.data.terminalJson);
        }
      }).catch(() => undefined);
    } else {
      // Guest mode: load from localStorage
      const guest = loadGuestPrefs();
      if (guest) applyPrefs(guest);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save preferences when key state changes
  useEffect(() => {
    if (!prefsLoaded.current) return;
    schedulePrefsWrite(buildPrefs());
  }, [symbol, interval, showWatchlist, showOrderPanel, watchlist, activeIndicators, selectedExchange, selectedMarket, buildPrefs, schedulePrefsWrite]);

  // --- Load symbols directory when exchange/market changes ---
  useEffect(() => {
    setAllSymbols([]);
    setSymbolsLoading(true);
    apiFetchNoWorkspace<{ symbols: SymbolInfo[] }>(
      `/terminal/symbols?exchange=${selectedExchange}&market=${selectedMarket}`,
    ).then((res) => {
      if (res.ok) setAllSymbols(res.data.symbols ?? []);
    }).catch(() => undefined).finally(() => setSymbolsLoading(false));
  }, [selectedExchange, selectedMarket]);

  // --- Watchlist polling ---
  const pollWatchlistQuotes = useCallback(async () => {
    if (watchlist.length === 0) return;
    const syms = watchlist.slice(0, MAX_WATCHLIST).join(",");
    const res = await apiFetchNoWorkspace<{ tickers: Array<{ symbol: string; lastPrice: string; price24hPcnt: string }> }>(
      `/terminal/tickers?exchange=${selectedExchange}&market=${selectedMarket}&symbols=${encodeURIComponent(syms)}`,
    );
    if (!res.ok) return;
    setWatchlistQuotes((prev) => {
      const next: Record<string, WatchlistQuote> = { ...prev };
      for (const t of res.data.tickers ?? []) {
        next[t.symbol] = {
          symbol: t.symbol,
          lastPrice: t.lastPrice,
          price24hPcnt: t.price24hPcnt,
          prevLastPrice: prev[t.symbol]?.lastPrice,
        };
      }
      return next;
    });
  }, [watchlist, selectedExchange, selectedMarket]);

  // Start/restart polling when watchlist or exchange/market changes
  useEffect(() => {
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    let active = true;
    function schedulePoll() {
      void pollWatchlistQuotes().finally(() => {
        if (active) {
          pollTimerRef.current = setTimeout(schedulePoll, POLL_INTERVAL_MS);
        }
      });
    }
    schedulePoll();
    return () => {
      active = false;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [pollWatchlistQuotes]);

  // Load exchange connections on mount (auth only)
  useEffect(() => {
    if (!getToken()) return;
    apiFetch<ExchangeConnection[]>("/exchanges").then((res) => {
      if (res.ok) {
        setConnections(res.data);
        if (res.data.length > 0) setSelectedConnection(res.data[0].id);
      } else if (res.problem.status === 401) {
        setSessionExpired(true);
      }
    });
  }, []);

  // Load orders for markers (workspace-scoped via apiFetch)
  useEffect(() => {
    if (!hasToken) return;
    apiFetch<TerminalOrder[]>("/terminal/orders").then((res) => {
      if (!res.ok) return;
      setAllOrders(res.data);
    });
  }, [hasToken]);

  // Rebuild markers whenever orders or symbol changes
  useEffect(() => {
    const sym = symbol.trim().toUpperCase();
    const m: ChartMarker[] = allOrders
      .filter((o) => o.symbol === sym && (o.side === "BUY" || o.side === "SELL"))
      .map((o) => ({
        time: Math.floor(new Date(o.createdAt).getTime() / 1000),
        side: o.side as "BUY" | "SELL",
      }));
    setMarkers(m);
  }, [allOrders, symbol]);

  // --- Market Data actions ---

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
      if (res.problem.status === 401) setSessionExpired(true);
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
      if (res.problem.status === 401) setSessionExpired(true);
      setCandlesError(`${res.problem.title}: ${res.problem.detail}`);
      setCandlesState("error");
    }
  }

  async function loadAll() {
    await Promise.all([loadTicker(), loadCandles()]);
  }

  // --- Order actions ---

  async function submitOrder() {
    if (!selectedConnection) {
      setOrderError("Select an exchange connection first");
      setOrderState("error");
      return;
    }
    const sym = symbol.trim().toUpperCase() || DEFAULT_SYMBOL;
    const qty = Number(orderQty);
    if (!Number.isFinite(qty) || qty <= 0) {
      setOrderError("Quantity must be a positive number");
      setOrderState("error");
      return;
    }
    if (orderType === "LIMIT") {
      const pr = Number(orderPrice);
      if (!Number.isFinite(pr) || pr <= 0) {
        setOrderError("Price must be a positive number for LIMIT orders");
        setOrderState("error");
        return;
      }
    }

    setOrderState("loading");
    setOrderError(null);
    setLastOrder(null);

    const body: Record<string, unknown> = {
      exchangeConnectionId: selectedConnection,
      symbol: sym,
      side: orderSide,
      type: orderType,
      qty,
    };
    if (orderType === "LIMIT") body.price = Number(orderPrice);

    const res = await apiFetch<TerminalOrder>("/terminal/orders", {
      method: "POST",
      body: JSON.stringify(body),
    });

    if (res.ok) {
      setLastOrder(res.data);
      setOrderState("success");
      // Refresh markers after placing an order
      apiFetch<TerminalOrder[]>("/terminal/orders").then((r) => {
        if (r.ok) setAllOrders(r.data);
      });
    } else {
      if (res.problem.status === 401) setSessionExpired(true);
      setOrderError(`${res.problem.title}: ${res.problem.detail}`);
      setOrderState("error");
    }
  }

  async function refreshOrderStatus() {
    if (!lastOrder) return;
    const res = await apiFetch<TerminalOrder>(`/terminal/orders/${lastOrder.id}`);
    if (res.ok) setLastOrder(res.data);
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
  // Auth gate
  // ---------------------------------------------------------------------------

  if (hasToken === null) {
    return (
      <div style={{ padding: "32px 24px" }}>
        <p style={hint}>Loading...</p>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render — MT4-like layout
  // ---------------------------------------------------------------------------

  return (
    <div style={outerWrap}>

      {/* ── Session expired banner ── */}
      {sessionExpired && (
        <div style={{ background: "#f85149", color: "#fff", padding: "10px 16px", fontSize: 13, display: "flex", alignItems: "center", gap: 12 }}>
          <span>Session expired. Please log in again.</span>
          <button
            onClick={() => router.push("/login")}
            style={{ background: "rgba(255,255,255,0.2)", border: "1px solid rgba(255,255,255,0.4)", borderRadius: 4, color: "#fff", cursor: "pointer", fontSize: 12, padding: "3px 10px" }}
          >
            Log in
          </button>
        </div>
      )}

      {/* ── Top bar: controls + panel toggles ── */}
      <div style={topBar}>
        <button
          style={togglePanelBtn}
          onClick={() => setShowWatchlist((v) => !v)}
          title="Toggle Watchlist"
        >
          {showWatchlist ? "◀ Watch" : "Watch ▶"}
        </button>

        {/* Exchange selector */}
        <select
          style={{ ...input, width: 80 }}
          value={selectedExchange}
          onChange={(e) => setSelectedExchange(e.target.value as SupportedExchange)}
        >
          {SUPPORTED_EXCHANGES.map((ex) => (
            <option key={ex} value={ex}>{ex}</option>
          ))}
        </select>

        {/* Market selector */}
        <select
          style={{ ...input, width: 80 }}
          value={selectedMarket}
          onChange={(e) => setSelectedMarket(e.target.value as SupportedMarket)}
        >
          {SUPPORTED_MARKETS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>

        <input
          style={{ ...input, width: 120 }}
          placeholder="Symbol"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && loadAll()}
        />

        {/* Symbols picker toggle */}
        <button
          style={togglePanelBtn}
          onClick={() => setShowPicker((v) => !v)}
          title="Browse symbols"
        >
          {symbolsLoading ? "..." : `+ Symbols`}
        </button>

        <select
          style={{ ...input, width: 80 }}
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
        >
          {(["1", "5", "15", "30", "60", "240", "D"] as const).map((iv) => (
            <option key={iv} value={iv}>
              {iv === "D" ? "1D" : `${iv}m`}
            </option>
          ))}
        </select>

        <input
          style={{ ...input, width: 70 }}
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

        <button
          style={togglePanelBtn}
          onClick={() => setShowOrderPanel((v) => !v)}
          title="Toggle Order Panel"
        >
          {showOrderPanel ? "Orders ▶" : "◀ Orders"}
        </button>
      </div>

      {/* ── Symbols picker dropdown ── */}
      {showPicker && (
        <div style={pickerDropdown}>
          <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
            <input
              style={{ ...input, flex: 1 }}
              placeholder="Search symbols..."
              value={symbolSearch}
              onChange={(e) => setSymbolSearch(e.target.value.toUpperCase())}
              autoFocus
            />
            <button style={togglePanelBtn} onClick={() => setShowPicker(false)}>✕</button>
          </div>
          <div style={{ maxHeight: 240, overflowY: "auto" }}>
            {allSymbols
              .filter((s) => !symbolSearch || s.symbol.includes(symbolSearch))
              .slice(0, 100)
              .map((s) => {
                const inList = watchlist.includes(s.symbol);
                return (
                  <div key={s.symbol} style={pickerRow}>
                    <span style={{ fontFamily: "monospace", fontSize: 13 }}>{s.symbol}</span>
                    <span style={{ color: "var(--text-secondary)", fontSize: 11 }}>{s.base}/{s.quote}</span>
                    <button
                      style={{
                        ...togglePanelBtn,
                        padding: "2px 8px",
                        fontSize: 11,
                        marginLeft: "auto",
                        color: inList ? "#f85149" : "#3fb950",
                      }}
                      onClick={() => {
                        if (inList) {
                          setWatchlist((prev) => prev.filter((x) => x !== s.symbol));
                        } else if (watchlist.length < MAX_WATCHLIST) {
                          setWatchlist((prev) => [...prev, s.symbol]);
                        }
                      }}
                    >
                      {inList ? "Remove" : "Add"}
                    </button>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* ── Main row: Watchlist | Chart | Order Panel ── */}
      <div style={mainRow}>

        {/* ── Left: Watchlist ── */}
        {showWatchlist && (
          <div style={watchlistPanel}>
            <div style={panelTitle}>Watchlist</div>
            {watchlist.map((sym) => {
              const q = watchlistQuotes[sym];
              const pct = q ? parseFloat(q.price24hPcnt) : 0;
              const priceUp = q && q.prevLastPrice ? parseFloat(q.lastPrice) > parseFloat(q.prevLastPrice) : null;
              return (
                <button
                  key={sym}
                  style={{
                    ...watchlistItem,
                    background: sym === symbol ? "var(--accent, #0969da)" : "transparent",
                    color: sym === symbol ? "#fff" : "var(--text-primary)",
                    fontWeight: sym === symbol ? 700 : 400,
                  }}
                  onClick={() => setSymbol(sym)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span>{sym}</span>
                    {q && (
                      <span style={{
                        fontSize: 11,
                        color: priceUp === true ? "#3fb950" : priceUp === false ? "#f85149" : "inherit",
                      }}>
                        {priceUp === true ? "▲" : priceUp === false ? "▼" : ""}{q.lastPrice}
                      </span>
                    )}
                  </div>
                  {q && (
                    <div style={{ fontSize: 10, color: pct > 0 ? "#3fb950" : pct < 0 ? "#f85149" : "var(--text-secondary)", textAlign: "right" }}>
                      {pct > 0 ? "+" : ""}{(pct * 100).toFixed(2)}%
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* ── Center: Chart ── */}
        <div style={chartCenter}>
          {/* ── Indicator toolbar ── */}
          <div style={indicatorBar}>
            {/* Active indicator chips */}
            {activeIndicators.map((ind) => {
              const def = INDICATOR_REGISTRY.find((d) => d.id === ind.id);
              return (
                <button
                  key={ind.id}
                  style={indicatorChip}
                  onClick={() => setIndicatorModal({ ...ind })}
                  title="Click to edit"
                >
                  {def?.label ?? ind.id}
                  <span
                    style={indicatorChipX}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveIndicators((prev) => prev.filter((i) => i.id !== ind.id));
                    }}
                  >
                    ×
                  </span>
                </button>
              );
            })}

            {/* Add indicator dropdown */}
            <div style={{ position: "relative" }}>
              <button
                style={addIndicatorBtn}
                onClick={() => setShowIndicatorAdd((v) => !v)}
              >
                + Indicator
              </button>
              {showIndicatorAdd && (
                <div style={indicatorDropdown}>
                  {INDICATOR_REGISTRY.filter(
                    (def) => !activeIndicators.some((a) => a.id === def.id),
                  ).map((def) => (
                    <button
                      key={def.id}
                      style={indicatorDropdownItem}
                      onClick={() => {
                        setActiveIndicators((prev) => [
                          ...prev,
                          { id: def.id, params: { ...def.defaultParams } },
                        ]);
                        setShowIndicatorAdd(false);
                      }}
                    >
                      {def.label}
                    </button>
                  ))}
                  {INDICATOR_REGISTRY.every((d) => activeIndicators.some((a) => a.id === d.id)) && (
                    <div style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-secondary)" }}>
                      All indicators active
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <TerminalChart
            symbol={symbol || DEFAULT_SYMBOL}
            limit={Math.min(Math.max(1, Number(limit) || 200), 1000)}
            markers={markers}
            activeIndicators={activeIndicators}
          />
        </div>

        {/* ── Indicator settings modal ── */}
        {indicatorModal && (() => {
          const def = INDICATOR_REGISTRY.find((d) => d.id === indicatorModal.id);
          if (!def) return null;
          return (
            <div style={modalOverlay} onClick={() => setIndicatorModal(null)}>
              <div style={modalBox} onClick={(e) => e.stopPropagation()}>
                <div style={modalTitle}>{def.label} Settings</div>
                {def.paramDefs.map((pd) => (
                  <label key={pd.key} style={modalField}>
                    <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{pd.label}</span>
                    <input
                      type="number"
                      min={pd.min}
                      max={pd.max}
                      step={pd.step ?? 1}
                      value={indicatorModal.params[pd.key] ?? ""}
                      onChange={(e) => {
                        const v = parseFloat(e.target.value);
                        if (!Number.isFinite(v)) return;
                        setIndicatorModal((prev) =>
                          prev ? { ...prev, params: { ...prev.params, [pd.key]: v } } : prev,
                        );
                      }}
                      style={{ ...input, width: "100%", marginTop: 4 }}
                    />
                  </label>
                ))}
                <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                  <button
                    style={btn}
                    onClick={() => {
                      setActiveIndicators((prev) =>
                        prev.map((i) => (i.id === indicatorModal.id ? { ...indicatorModal } : i)),
                      );
                      setIndicatorModal(null);
                    }}
                  >
                    Apply
                  </button>
                  <button
                    style={{ ...btn, background: "#f85149" }}
                    onClick={() => {
                      setActiveIndicators((prev) => prev.filter((i) => i.id !== indicatorModal.id));
                      setIndicatorModal(null);
                    }}
                  >
                    Remove
                  </button>
                  <button
                    style={{ ...btn, background: "var(--bg-secondary)", color: "var(--text-secondary)" }}
                    onClick={() => setIndicatorModal(null)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          );
        })()}

        {/* ── Right: Order Panel ── */}
        {showOrderPanel && (
          <div style={orderPanelCol}>
            <div style={panelTitle}>Place Order</div>

            {!hasToken ? (
              <div style={{ padding: "16px 12px", display: "flex", flexDirection: "column", gap: 10 }}>
                <p style={{ ...hint, fontSize: 13, lineHeight: 1.5 }}>
                  Login to trade / connect exchange
                </p>
                <button style={loginCtaBtn} onClick={() => router.push("/login")}>
                  Sign in
                </button>
              </div>
            ) : connections.length === 0 ? (
              <p style={{ ...hint, padding: "10px 12px" }}>
                No exchange connections. Create one first.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10, padding: "10px 12px" }}>
                {/* Connection */}
                <div>
                  <div style={fieldLabel}>Connection</div>
                  <select
                    style={{ ...input, width: "100%" }}
                    value={selectedConnection}
                    onChange={(e) => setSelectedConnection(e.target.value)}
                  >
                    {connections.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.exchange})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Side */}
                <div>
                  <div style={fieldLabel}>Side</div>
                  <div style={{ display: "flex", gap: 4 }}>
                    <button
                      style={{
                        ...sideBtn,
                        flex: 1,
                        background: orderSide === "BUY" ? "#3fb950" : "var(--bg-secondary)",
                        color: orderSide === "BUY" ? "#fff" : "var(--text-primary)",
                      }}
                      onClick={() => setOrderSide("BUY")}
                    >
                      BUY
                    </button>
                    <button
                      style={{
                        ...sideBtn,
                        flex: 1,
                        background: orderSide === "SELL" ? "#f85149" : "var(--bg-secondary)",
                        color: orderSide === "SELL" ? "#fff" : "var(--text-primary)",
                      }}
                      onClick={() => setOrderSide("SELL")}
                    >
                      SELL
                    </button>
                  </div>
                </div>

                {/* Type */}
                <div>
                  <div style={fieldLabel}>Type</div>
                  <select
                    style={{ ...input, width: "100%" }}
                    value={orderType}
                    onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")}
                  >
                    <option value="MARKET">Market</option>
                    <option value="LIMIT">Limit</option>
                  </select>
                </div>

                {/* Qty */}
                <div>
                  <div style={fieldLabel}>Qty</div>
                  <input
                    style={{ ...input, width: "100%" }}
                    type="number"
                    min={0}
                    step="any"
                    placeholder="e.g. 0.001"
                    value={orderQty}
                    onChange={(e) => setOrderQty(e.target.value)}
                  />
                </div>

                {/* Price (LIMIT only) */}
                {orderType === "LIMIT" && (
                  <div>
                    <div style={fieldLabel}>Price</div>
                    <input
                      style={{ ...input, width: "100%" }}
                      type="number"
                      min={0}
                      step="any"
                      placeholder="e.g. 60000"
                      value={orderPrice}
                      onChange={(e) => setOrderPrice(e.target.value)}
                    />
                  </div>
                )}

                {/* Submit */}
                <button
                  style={{
                    ...btn,
                    width: "100%",
                    background: orderSide === "BUY" ? "#3fb950" : "#f85149",
                  }}
                  onClick={submitOrder}
                  disabled={orderState === "loading"}
                >
                  {orderState === "loading"
                    ? "Placing..."
                    : `${orderSide} ${orderType}`}
                </button>

                {/* Result */}
                {orderState === "error" && (
                  <p style={{ color: "#f85149", fontSize: 12, margin: 0 }}>{orderError}</p>
                )}
                {orderState === "success" && lastOrder && (
                  <OrderStatusRow order={lastOrder} onRefresh={refreshOrderStatus} />
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Bottom tabs: Ticker | Orders | Candles ── */}
      <div style={bottomSection}>
        <div style={tabBar}>
          {(["ticker", "orders", "candles"] as BottomTab[]).map((tab) => (
            <button
              key={tab}
              style={{
                ...tabBtn,
                borderBottom: bottomTab === tab ? "2px solid var(--accent, #0969da)" : "2px solid transparent",
                color: bottomTab === tab ? "var(--text-primary)" : "var(--text-secondary)",
                fontWeight: bottomTab === tab ? 600 : 400,
              }}
              onClick={() => setBottomTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === "orders" && allOrders.length > 0 ? ` (${allOrders.length})` : ""}
              {tab === "candles" && candlesState === "success" ? ` (${candles.length})` : ""}
            </button>
          ))}
        </div>

        <div style={tabContent}>
          {/* Ticker tab */}
          {bottomTab === "ticker" && (
            <>
              {tickerState === "idle" && (
                <p style={hint}>Select a symbol and click Load.</p>
              )}
              {tickerState === "loading" && <p style={hint}>Loading ticker...</p>}
              {tickerState === "error" && (
                <p style={{ color: "#f85149", fontSize: 13 }}>{tickerError}</p>
              )}
              {tickerState === "success" && ticker && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 10 }}>
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
            </>
          )}

          {/* Orders tab */}
          {bottomTab === "orders" && (
            <>
              {!hasToken ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "flex-start" }}>
                  <p style={hint}>Login to view order history.</p>
                  <button style={{ ...loginCtaBtn, fontSize: 13, padding: "8px 20px" }} onClick={() => router.push("/login")}>
                    Sign in to trade
                  </button>
                </div>
              ) : allOrders.length === 0 ? (
                <p style={hint}>No orders yet.</p>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                    <thead>
                      <tr>
                        {["Time", "Symbol", "Side", "Type", "Qty", "Price", "Status"].map((h) => (
                          <th key={h} style={thStyle}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[...allOrders].reverse().map((o) => {
                        const sideColor = o.side === "BUY" ? "#3fb950" : "#f85149";
                        return (
                          <tr key={o.id}>
                            <td style={td}>{new Date(o.createdAt).toLocaleString()}</td>
                            <td style={td}>{o.symbol}</td>
                            <td style={{ ...td, color: sideColor, fontWeight: 700 }}>{o.side}</td>
                            <td style={td}>{o.type}</td>
                            <td style={td}>{o.qty}</td>
                            <td style={td}>{o.price ?? "—"}</td>
                            <td style={td}>{o.status}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {/* Candles tab */}
          {bottomTab === "candles" && (
            <>
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
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                    <thead>
                      <tr>
                        {["Time", "Open", "High", "Low", "Close", "Volume"].map((h) => (
                          <th key={h} style={thStyle}>{h}</th>
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
            </>
          )}
        </div>
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
      <div style={{ fontSize: 15, fontWeight: 600, color: color ?? "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

function OrderStatusRow({
  order,
  onRefresh,
}: {
  order: TerminalOrder;
  onRefresh: () => void;
}) {
  const statusColors: Record<string, string> = {
    FILLED: "#3fb950",
    FAILED: "#f85149",
    REJECTED: "#f85149",
    SUBMITTED: "#e3b341",
    PARTIALLY_FILLED: "#e3b341",
    CANCELLED: "var(--text-secondary)",
    PENDING: "var(--text-secondary)",
  };
  const color = statusColors[order.status] ?? "var(--text-secondary)";

  return (
    <div
      style={{
        background: "var(--bg-secondary)",
        borderRadius: 6,
        padding: "8px 10px",
        fontSize: 12,
        display: "flex",
        flexWrap: "wrap",
        gap: 8,
        alignItems: "center",
      }}
    >
      <span style={{ fontWeight: 700, color }}>{order.status}</span>
      <span style={{ fontFamily: "monospace" }}>
        {order.side} {order.type} {order.qty} {order.symbol}
        {order.price ? ` @ ${order.price}` : ""}
      </span>
      {order.error && (
        <span style={{ color: "#f85149" }}>{order.error}</span>
      )}
      {(order.status === "SUBMITTED" || order.status === "PARTIALLY_FILLED") && (
        <button style={{ ...btn, padding: "3px 8px", fontSize: 11 }} onClick={onRefresh}>
          Refresh
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const outerWrap: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  height: "100%",
  minHeight: "100vh",
  padding: "0",
  boxSizing: "border-box",
};

const topBar: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 12px",
  borderBottom: "1px solid var(--border)",
  flexWrap: "wrap",
  background: "var(--bg-card)",
};

const togglePanelBtn: React.CSSProperties = {
  padding: "6px 10px",
  fontSize: 12,
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 5,
  cursor: "pointer",
  color: "var(--text-secondary)",
  whiteSpace: "nowrap",
};

const mainRow: React.CSSProperties = {
  display: "flex",
  flex: 1,
  gap: 0,
  minHeight: 0,
  overflow: "hidden",
};

const watchlistPanel: React.CSSProperties = {
  width: 160,
  minWidth: 140,
  borderRight: "1px solid var(--border)",
  background: "var(--bg-card)",
  display: "flex",
  flexDirection: "column",
  flexShrink: 0,
};

const panelTitle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  padding: "10px 12px 6px",
  borderBottom: "1px solid var(--border)",
};

const watchlistItem: React.CSSProperties = {
  display: "block",
  width: "100%",
  textAlign: "left",
  padding: "9px 12px",
  fontSize: 13,
  border: "none",
  borderBottom: "1px solid var(--border)",
  cursor: "pointer",
  fontFamily: "monospace",
  borderRadius: 0,
};

const chartCenter: React.CSSProperties = {
  flex: 1,
  minWidth: 0,
  padding: "12px",
  background: "var(--bg-primary, var(--bg-card))",
  overflow: "hidden",
};

const orderPanelCol: React.CSSProperties = {
  width: 240,
  minWidth: 200,
  borderLeft: "1px solid var(--border)",
  background: "var(--bg-card)",
  padding: "0 0 12px 0",
  flexShrink: 0,
  overflowY: "auto",
};

const bottomSection: React.CSSProperties = {
  borderTop: "1px solid var(--border)",
  background: "var(--bg-card)",
  maxHeight: 280,
  display: "flex",
  flexDirection: "column",
};

const tabBar: React.CSSProperties = {
  display: "flex",
  borderBottom: "1px solid var(--border)",
  padding: "0 8px",
};

const tabBtn: React.CSSProperties = {
  padding: "8px 14px",
  fontSize: 12,
  background: "none",
  border: "none",
  borderBottom: "2px solid transparent",
  cursor: "pointer",
  fontWeight: 400,
  whiteSpace: "nowrap",
};

const tabContent: React.CSSProperties = {
  padding: "12px",
  overflowY: "auto",
  flex: 1,
};

const input: React.CSSProperties = {
  padding: "6px 10px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 5,
  color: "var(--text-primary)",
  fontSize: 13,
};

const btn: React.CSSProperties = {
  padding: "7px 16px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 5,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
};

const sideBtn: React.CSSProperties = {
  padding: "8px 0",
  border: "1px solid var(--border)",
  borderRadius: 5,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
};

const hint: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 13,
  margin: 0,
};

const fieldLabel: React.CSSProperties = {
  fontSize: 11,
  color: "var(--text-secondary)",
  marginBottom: 4,
};

const thStyle: React.CSSProperties = {
  textAlign: "right",
  padding: "4px 8px",
  borderBottom: "1px solid var(--border)",
  color: "var(--text-secondary)",
  fontWeight: 600,
  fontSize: 11,
  whiteSpace: "nowrap",
};

const td: React.CSSProperties = {
  padding: "4px 8px",
  textAlign: "right",
  borderBottom: "1px solid var(--border)",
  fontFamily: "monospace",
};

const loginCtaBtn: React.CSSProperties = {
  padding: "12px 32px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 16,
  fontWeight: 600,
};

const pickerDropdown: React.CSSProperties = {
  position: "relative",
  background: "var(--bg-card)",
  borderBottom: "1px solid var(--border)",
  padding: "10px 12px",
  zIndex: 10,
};

const pickerRow: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "5px 4px",
  borderBottom: "1px solid var(--border)",
};

// ── Indicator styles (Stage 20e) ──────────────────────────────────────────

const indicatorBar: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 6,
  marginBottom: 8,
  alignItems: "center",
};

const indicatorChip: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  padding: "3px 10px",
  fontSize: 12,
  background: "rgba(96,165,250,0.15)",
  border: "1px solid rgba(96,165,250,0.4)",
  borderRadius: 4,
  cursor: "pointer",
  color: "#60a5fa",
  fontWeight: 600,
};

const indicatorChipX: React.CSSProperties = {
  marginLeft: 2,
  fontSize: 14,
  lineHeight: 1,
  opacity: 0.7,
  cursor: "pointer",
};

const addIndicatorBtn: React.CSSProperties = {
  padding: "3px 10px",
  fontSize: 12,
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 4,
  cursor: "pointer",
  color: "var(--text-secondary)",
};

const indicatorDropdown: React.CSSProperties = {
  position: "absolute",
  top: "calc(100% + 4px)",
  left: 0,
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
  zIndex: 50,
  minWidth: 160,
  overflow: "hidden",
};

const indicatorDropdownItem: React.CSSProperties = {
  display: "block",
  width: "100%",
  textAlign: "left",
  padding: "9px 14px",
  fontSize: 13,
  background: "none",
  border: "none",
  borderBottom: "1px solid var(--border)",
  cursor: "pointer",
  color: "var(--text-primary)",
};

const modalOverlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.55)",
  zIndex: 200,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const modalBox: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 10,
  padding: "24px",
  minWidth: 280,
  maxWidth: 360,
  width: "90%",
  boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
};

const modalTitle: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 700,
  marginBottom: 16,
};

const modalField: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 2,
  marginBottom: 12,
};
