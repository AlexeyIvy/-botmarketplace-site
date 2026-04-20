"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken } from "../../../lib/api";

// ---------------------------------------------------------------------------
// Types — mirror the API shape from GET /api/v1/intents
// ---------------------------------------------------------------------------

type IntentState =
  | "PENDING" | "PLACED" | "PARTIALLY_FILLED" | "FILLED" | "CANCELLED" | "FAILED";

interface BotRef { id: string; name: string; symbol: string }
interface BotRunRef { id: string; symbol: string; state: string; bot: BotRef }

interface Intent {
  id: string;
  intentId: string;
  orderLinkId: string;
  type: string;
  side: string;
  qty: string;
  price: string | null;
  state: IntentState;
  retryCount: number;
  orderId: string | null;
  metaJson: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
  botRun: BotRunRef;
}

interface ListResponse {
  items: Intent[];
  total: number;
  limit: number;
  offset: number;
}

const STATES: IntentState[] = ["FAILED", "PENDING", "PLACED", "PARTIALLY_FILLED", "FILLED", "CANCELLED"];
const PAGE_SIZE = 25;

// ---------------------------------------------------------------------------

export default function DlqPage() {
  const router = useRouter();

  const [state, setState] = useState<IntentState | "">("FAILED");
  const [items, setItems] = useState<Intent[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [retrying, setRetrying] = useState<Record<string, boolean>>({});
  const [retryMsg, setRetryMsg] = useState<Record<string, string | null>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const qs = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(offset),
      ...(state ? { state } : {}),
    });
    const res = await apiFetch<ListResponse>(`/intents?${qs.toString()}`);
    setLoading(false);
    if (!res.ok) {
      setError(`${res.problem.title}: ${res.problem.detail}`);
      setItems([]);
      setTotal(0);
      return;
    }
    setItems(res.data.items);
    setTotal(res.data.total);
  }, [state, offset]);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    load();
  }, [load, router]);

  async function handleRetry(intent: Intent) {
    setRetrying((r) => ({ ...r, [intent.id]: true }));
    setRetryMsg((m) => ({ ...m, [intent.id]: null }));
    const res = await apiFetch<Intent>(`/intents/${intent.id}/retry`, { method: "POST" });
    setRetrying((r) => ({ ...r, [intent.id]: false }));
    if (!res.ok) {
      setRetryMsg((m) => ({ ...m, [intent.id]: `✗ ${res.problem.title}: ${res.problem.detail}` }));
      return;
    }
    setRetryMsg((m) => ({ ...m, [intent.id]: "✓ Retried — state reset to PENDING" }));
    // Refresh list in place so the retried row disappears from FAILED view
    setTimeout(load, 500);
  }

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div style={wrap}>
      <div style={header}>
        <h1 style={title}>Dead-letter queue</h1>
        <p style={subtitle}>
          Failed bot intents, workspace-scoped. Retry puts an intent back into PENDING
          so the worker re-processes it on the next tick.
        </p>
      </div>

      <div style={card}>
        <div style={filterRow}>
          <label style={fieldLabel}>State</label>
          <select
            style={selectStyle}
            value={state}
            onChange={(e) => { setOffset(0); setState(e.target.value as IntentState | ""); }}
          >
            <option value="">(any)</option>
            {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button style={smallBtn} onClick={() => load()} disabled={loading}>
            {loading ? "Loading…" : "Refresh"}
          </button>
          <span style={{ ...hint, marginLeft: "auto" }}>
            {total > 0 ? `${total} total, page ${page}/${pages}` : "0 total"}
          </span>
        </div>

        {error && <div style={errorBanner}>{error}</div>}
        {!error && items.length === 0 && !loading && (
          <div style={emptyMsg}>No intents match the current filter.</div>
        )}

        {items.length > 0 && (
          <table style={table}>
            <thead>
              <tr>
                <Th w={30} />
                <Th>intentId</Th>
                <Th>bot / symbol</Th>
                <Th>type</Th>
                <Th>side</Th>
                <Th>qty</Th>
                <Th>state</Th>
                <Th>retry</Th>
                <Th>created</Th>
                <Th w={120} align="right">actions</Th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <IntentRow
                  key={it.id}
                  intent={it}
                  expanded={expanded === it.id}
                  toggle={() => setExpanded(expanded === it.id ? null : it.id)}
                  retrying={!!retrying[it.id]}
                  retryMsg={retryMsg[it.id] ?? null}
                  onRetry={() => handleRetry(it)}
                />
              ))}
            </tbody>
          </table>
        )}

        {total > PAGE_SIZE && (
          <div style={paginationRow}>
            <button
              style={smallBtn}
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              ← Prev
            </button>
            <span style={hint}>page {page} / {pages}</span>
            <button
              style={smallBtn}
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Row — collapsible, with detail + action buttons
// ---------------------------------------------------------------------------

function IntentRow({
  intent, expanded, toggle, retrying, retryMsg, onRetry,
}: {
  intent: Intent;
  expanded: boolean;
  toggle: () => void;
  retrying: boolean;
  retryMsg: string | null;
  onRetry: () => void;
}) {
  const createdAgo = useMemo(() => formatAgo(intent.createdAt), [intent.createdAt]);
  const meta = intent.metaJson ?? {};
  const errorReason = String(meta.error ?? meta.classificationReason ?? meta.deadLetterReason ?? "—");
  const errorClass = String(meta.errorClass ?? "");

  return (
    <>
      <tr onClick={toggle} style={trClickable}>
        <td style={td}>{expanded ? "▾" : "▸"}</td>
        <td style={{ ...td, fontFamily: "var(--font-mono, monospace)", fontSize: 12 }}>{intent.intentId}</td>
        <td style={td}>
          <div style={{ fontWeight: 500 }}>{intent.botRun.bot.name}</div>
          <div style={hint}>{intent.botRun.bot.symbol}</div>
        </td>
        <td style={td}>{intent.type}</td>
        <td style={td}>{intent.side}</td>
        <td style={td}>{intent.qty}</td>
        <td style={td}><StateBadge state={intent.state} /></td>
        <td style={td}>{intent.retryCount}</td>
        <td style={{ ...td, ...hint }}>{createdAgo}</td>
        <td style={{ ...td, textAlign: "right" }}>
          {intent.state === "FAILED" && (
            <button
              style={retryBtn}
              onClick={(e) => { e.stopPropagation(); onRetry(); }}
              disabled={retrying}
            >
              {retrying ? "…" : "Retry"}
            </button>
          )}
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={10} style={detailCell}>
            <div style={detailGrid}>
              <DetailField label="id" value={intent.id} />
              <DetailField label="orderLinkId" value={intent.orderLinkId} />
              <DetailField label="orderId" value={intent.orderId ?? "—"} />
              <DetailField label="run" value={`${intent.botRun.id} (${intent.botRun.state})`} />
              <DetailField label="error" value={errorReason} />
              <DetailField label="errorClass" value={errorClass || "—"} />
              <DetailField label="price" value={intent.price ?? "—"} />
              <DetailField label="updatedAt" value={new Date(intent.updatedAt).toISOString()} />
            </div>
            <pre style={metaPre}>{JSON.stringify(meta, null, 2)}</pre>
            {retryMsg && <div style={retryStatus}>{retryMsg}</div>}
          </td>
        </tr>
      )}
    </>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={hint}>{label}</div>
      <div style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12, wordBreak: "break-all" }}>
        {value}
      </div>
    </div>
  );
}

function StateBadge({ state }: { state: IntentState }) {
  const bg = STATE_COLORS[state] ?? "#6e7681";
  return (
    <span style={{
      display: "inline-block", padding: "2px 8px", borderRadius: 4,
      background: bg, color: "#fff", fontSize: 11, fontWeight: 600, letterSpacing: 0.2,
    }}>
      {state}
    </span>
  );
}

function Th({ children, w, align }: { children?: React.ReactNode; w?: number; align?: "left" | "right" }) {
  return (
    <th style={{
      textAlign: align ?? "left",
      padding: "8px 10px",
      color: "var(--text-secondary)",
      fontWeight: 500,
      fontSize: 12,
      borderBottom: "1px solid var(--border)",
      width: w,
    }}>
      {children}
    </th>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatAgo(iso: string): string {
  const delta = Date.now() - new Date(iso).getTime();
  const s = Math.floor(delta / 1000);
  if (s < 60)     return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60)     return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24)     return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

// ---------------------------------------------------------------------------
// Styles — match the token vocabulary used on /settings
// ---------------------------------------------------------------------------

const STATE_COLORS: Record<IntentState, string> = {
  PENDING:           "#6e7681",
  PLACED:            "#1f6feb",
  PARTIALLY_FILLED:  "#bb8009",
  FILLED:            "#3fb950",
  CANCELLED:         "#8250df",
  FAILED:            "#f85149",
};

const wrap:          React.CSSProperties = { maxWidth: 1200, margin: "0 auto", padding: "32px 24px" };
const header:        React.CSSProperties = { marginBottom: 20 };
const title:         React.CSSProperties = { fontSize: 22, fontWeight: 600, margin: 0, color: "var(--text-primary)" };
const subtitle:      React.CSSProperties = { color: "var(--text-secondary)", fontSize: 13, marginTop: 6 };
const card:          React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: "16px 20px" };
const filterRow:     React.CSSProperties = { display: "flex", alignItems: "center", gap: 12, paddingBottom: 12, borderBottom: "1px solid var(--border)", marginBottom: 8 };
const fieldLabel:    React.CSSProperties = { color: "var(--text-secondary)", fontSize: 13 };
const selectStyle:   React.CSSProperties = { background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 13, padding: "6px 10px" };
const smallBtn:      React.CSSProperties = { padding: "4px 12px", background: "transparent", border: "1px solid var(--border)", borderRadius: 5, color: "var(--text-secondary)", cursor: "pointer", fontSize: 12 };
const retryBtn:      React.CSSProperties = { padding: "4px 12px", background: "var(--accent)", border: "none", borderRadius: 5, color: "#fff", cursor: "pointer", fontSize: 12, fontWeight: 600 };
const hint:          React.CSSProperties = { color: "var(--text-secondary)", fontSize: 12 };
const emptyMsg:      React.CSSProperties = { padding: "32px 0", textAlign: "center", color: "var(--text-secondary)", fontSize: 13 };
const errorBanner:   React.CSSProperties = { background: "#f85149", color: "#fff", padding: "10px 14px", borderRadius: 6, fontSize: 13, margin: "8px 0" };
const table:         React.CSSProperties = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const trClickable:   React.CSSProperties = { cursor: "pointer", borderBottom: "1px solid var(--border)" };
const td:            React.CSSProperties = { padding: "8px 10px", color: "var(--text-primary)", verticalAlign: "middle" };
const detailCell:    React.CSSProperties = { padding: "12px 16px", background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" };
const detailGrid:    React.CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginBottom: 12 };
const metaPre:       React.CSSProperties = { background: "var(--bg-card)", padding: 10, borderRadius: 6, border: "1px solid var(--border)", fontSize: 11, overflowX: "auto", color: "var(--text-primary)", margin: 0 };
const retryStatus:   React.CSSProperties = { marginTop: 10, fontSize: 12, color: "var(--text-secondary)" };
const paginationRow: React.CSSProperties = { display: "flex", alignItems: "center", justifyContent: "center", gap: 14, padding: "12px 0 4px" };
