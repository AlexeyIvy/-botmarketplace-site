"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetchNoWorkspace, apiFetch, getToken } from "../../lib/api";
import TerminalChart, { type ChartMarker } from "../../components/terminal/TerminalChart";

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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WATCHLIST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"] as const;
const DEFAULT_SYMBOL = "BTCUSDT";
const DEFAULT_INTERVAL = "15";

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

  // Load exchange connections on mount
  useEffect(() => {
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
    if (!getToken()) {
      router.push("/login");
      return;
    }
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

  if (hasToken === false) {
    return (
      <div style={loginCtaWrap}>
        <div style={loginCtaBox}>
          <h1 style={{ fontSize: 26, marginBottom: 12 }}>Terminal</h1>
          <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 15 }}>
            Sign in to load market data, view charts, and place orders.
          </p>
          <button style={loginCtaBtn} onClick={() => router.push("/login")}>
            Login to load market data
          </button>
        </div>
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

        <input
          style={{ ...input, width: 120 }}
          placeholder="Symbol"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && loadAll()}
        />

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

      {/* ── Main row: Watchlist | Chart | Order Panel ── */}
      <div style={mainRow}>

        {/* ── Left: Watchlist ── */}
        {showWatchlist && (
          <div style={watchlistPanel}>
            <div style={panelTitle}>Watchlist</div>
            {WATCHLIST_SYMBOLS.map((sym) => (
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
                {sym}
              </button>
            ))}
          </div>
        )}

        {/* ── Center: Chart ── */}
        <div style={chartCenter}>
          <TerminalChart
            symbol={symbol || DEFAULT_SYMBOL}
            limit={Math.min(Math.max(1, Number(limit) || 200), 1000)}
            markers={markers}
          />
        </div>

        {/* ── Right: Order Panel ── */}
        {showOrderPanel && (
          <div style={orderPanelCol}>
            <div style={panelTitle}>Place Order</div>

            {connections.length === 0 ? (
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
              {allOrders.length === 0 ? (
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

const loginCtaWrap: React.CSSProperties = {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  minHeight: "60vh",
  padding: "32px 24px",
};

const loginCtaBox: React.CSSProperties = {
  textAlign: "center",
  maxWidth: 400,
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
