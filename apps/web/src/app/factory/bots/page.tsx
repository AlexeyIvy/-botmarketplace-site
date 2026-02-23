"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { apiFetch, getWorkspaceId, type ProblemDetails } from "../api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StrategyVersion {
  id: string;
  version: number;
  dslJson: { market?: { symbol?: string }; entry?: { side?: string }; execution?: { orderType?: string } };
}

interface StrategyWithVersions {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  versions: StrategyVersion[];
}

interface ExchangeConnection {
  id: string;
  name: string;
  exchange: string;
  status: string;
}

interface Bot {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  strategyVersionId: string;
  exchangeConnectionId: string | null;
  updatedAt: string;
}

const TIMEFRAMES = ["M1", "M5", "M15", "H1"];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [error, setError] = useState<ProblemDetails | null>(null);

  // form state
  const [name, setName] = useState("");
  const [timeframe, setTimeframe] = useState("M15");

  // strategy / version selection
  const [strategies, setStrategies] = useState<StrategyWithVersions[]>([]);
  const [selectedStratId, setSelectedStratId] = useState("");
  const [selectedVerId, setSelectedVerId] = useState("");

  // exchange connection selection (optional)
  const [exchanges, setExchanges] = useState<ExchangeConnection[]>([]);
  const [selectedExchangeId, setSelectedExchangeId] = useState("");

  // derived symbol from selected version DSL
  const [symbol, setSymbol] = useState("BTCUSDT");

  // loading state
  const [loadingVersions, setLoadingVersions] = useState(false);

  // ---------------------------------------------------------------------------
  // Loaders
  // ---------------------------------------------------------------------------

  const loadBots = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<Bot[]>("/bots");
    if (res.ok) {
      setBots(res.data);
      setError(null);
    } else {
      setError(res.problem);
    }
  }, []);

  const loadExchanges = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<ExchangeConnection[]>("/exchanges");
    if (res.ok) setExchanges(res.data);
  }, []);

  const loadStrategies = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<{ id: string; name: string; symbol: string; timeframe: string; status: string }[]>("/strategies");
    if (res.ok) {
      setStrategies(res.data.map((s) => ({ ...s, versions: [] })));
    }
  }, []);

  useEffect(() => {
    loadBots();
    loadExchanges();
    loadStrategies();
  }, [loadBots, loadExchanges, loadStrategies]);

  // ---------------------------------------------------------------------------
  // Strategy selection → load its versions
  // ---------------------------------------------------------------------------

  async function onStrategyChange(stratId: string) {
    setSelectedStratId(stratId);
    setSelectedVerId("");
    setSymbol("BTCUSDT");
    if (!stratId) return;

    setLoadingVersions(true);
    const res = await apiFetch<StrategyWithVersions>(`/strategies/${stratId}`);
    setLoadingVersions(false);
    if (res.ok) {
      const sv = res.data;
      setStrategies((prev) =>
        prev.map((s) => (s.id === stratId ? { ...s, versions: sv.versions } : s))
      );
      // auto-select the latest version (first in desc order)
      const latest = sv.versions[0];
      if (latest) {
        setSelectedVerId(latest.id);
        const sym = latest.dslJson?.market?.symbol;
        if (sym) setSymbol(sym);
      }
    }
  }

  function onVersionChange(verId: string) {
    setSelectedVerId(verId);
    const strat = strategies.find((s) => s.id === selectedStratId);
    const ver = strat?.versions.find((v) => v.id === verId);
    const sym = ver?.dslJson?.market?.symbol;
    if (sym) setSymbol(sym);
  }

  // ---------------------------------------------------------------------------
  // Create bot
  // ---------------------------------------------------------------------------

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const body: Record<string, unknown> = {
      name,
      strategyVersionId: selectedVerId,
      symbol,
      timeframe,
    };
    if (selectedExchangeId) body.exchangeConnectionId = selectedExchangeId;

    const res = await apiFetch<Bot>("/bots", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (res.ok) {
      setName("");
      setSelectedStratId("");
      setSelectedVerId("");
      setSelectedExchangeId("");
      setSymbol("BTCUSDT");
      setError(null);
      loadBots();
    } else {
      setError(res.problem);
    }
  }

  // ---------------------------------------------------------------------------
  // Guards
  // ---------------------------------------------------------------------------

  if (!getWorkspaceId()) {
    return (
      <div style={{ padding: "48px 24px" }}>
        <Link href="/factory">Set Workspace ID first</Link>
      </div>
    );
  }

  const selectedStrat = strategies.find((s) => s.id === selectedStratId);
  const versions = selectedStrat?.versions ?? [];
  const selectedVer = versions.find((v) => v.id === selectedVerId);
  const dslSummary = selectedVer
    ? `${selectedVer.dslJson?.entry?.side ?? ""} · ${selectedVer.dslJson?.execution?.orderType ?? ""}`
    : null;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={{ padding: "48px 24px", maxWidth: 860, margin: "0 auto" }}>
      <p style={{ marginBottom: 16 }}>
        <Link href="/factory">← Factory</Link>
      </p>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>Bots</h1>

      {error && <ErrorBox problem={error} />}

      {/* ── Create bot form ─────────────────────────────────── */}
      <form onSubmit={create} style={card}>
        <h3 style={{ marginBottom: 14 }}>Create Bot</h3>

        {/* Row 1: Name + Timeframe */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          <input
            style={{ ...input, flex: 2 }}
            placeholder="Bot name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <select style={input} value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            {TIMEFRAMES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {/* Row 2: Strategy selector */}
        <div style={{ marginBottom: 10 }}>
          <label style={labelStyle}>Strategy</label>
          <select
            style={{ ...input, width: "100%" }}
            value={selectedStratId}
            onChange={(e) => onStrategyChange(e.target.value)}
            required
          >
            <option value="">— select strategy —</option>
            {strategies.map((s) => (
              <option key={s.id} value={s.id}>{s.name} ({s.symbol})</option>
            ))}
          </select>
        </div>

        {/* Row 3: Version selector (shown after strategy selected) */}
        {selectedStratId && (
          <div style={{ marginBottom: 10 }}>
            <label style={labelStyle}>
              Strategy Version{" "}
              {loadingVersions && <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>loading…</span>}
            </label>
            <select
              style={{ ...input, width: "100%" }}
              value={selectedVerId}
              onChange={(e) => onVersionChange(e.target.value)}
              required
            >
              <option value="">— select version —</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  v{v.version} · {v.dslJson?.market?.symbol ?? ""} · {v.dslJson?.entry?.side ?? ""} · {v.dslJson?.execution?.orderType ?? ""}
                </option>
              ))}
            </select>
            {dslSummary && selectedVer && (
              <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
                Symbol: <strong>{selectedVer.dslJson?.market?.symbol}</strong> · {dslSummary}
              </p>
            )}
          </div>
        )}

        {/* Row 4: Exchange Connection (optional) */}
        <div style={{ marginBottom: 10 }}>
          <label style={labelStyle}>
            Exchange Connection <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>(optional)</span>
          </label>
          <select
            style={{ ...input, width: "100%" }}
            value={selectedExchangeId}
            onChange={(e) => setSelectedExchangeId(e.target.value)}
          >
            <option value="">— none —</option>
            {exchanges.map((ex) => (
              <option key={ex.id} value={ex.id}>{ex.name} ({ex.exchange} · {ex.status})</option>
            ))}
          </select>
        </div>

        {/* Row 5: Symbol (auto-filled from DSL, editable) + Submit */}
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Symbol</label>
            <input
              style={{ ...input, width: "100%" }}
              placeholder="BTCUSDT"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              required
            />
          </div>
          <button style={btn} type="submit">
            Create Bot
          </button>
        </div>
      </form>

      {/* ── Bots list ──────────────────────────────────────── */}
      <table style={{ width: "100%", marginTop: 24, borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Name", "Symbol", "TF", "Status", "Exchange", "Updated"].map((h) => (
              <th key={h} style={th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bots.map((b) => (
            <tr key={b.id}>
              <td style={td}>
                <Link href={`/factory/bots/${b.id}`}>{b.name}</Link>
              </td>
              <td style={td}>{b.symbol}</td>
              <td style={td}>{b.timeframe}</td>
              <td style={td}>{b.status}</td>
              <td style={td}>{b.exchangeConnectionId ? "✓" : "—"}</td>
              <td style={td}>{new Date(b.updatedAt).toLocaleString()}</td>
            </tr>
          ))}
          {bots.length === 0 && (
            <tr>
              <td colSpan={6} style={{ ...td, color: "var(--text-secondary)" }}>No bots yet</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components + styles
// ---------------------------------------------------------------------------

function ErrorBox({ problem }: { problem: ProblemDetails }) {
  return (
    <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 6, padding: 12, marginBottom: 16 }}>
      <strong>{problem.title}</strong>: {problem.detail}
      {problem.errors?.map((e, i) => (
        <div key={i} style={{ fontSize: 13, marginTop: 4 }}>{e.field}: {e.message}</div>
      ))}
    </div>
  );
}

const card: React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, marginBottom: 8 };
const input: React.CSSProperties = { padding: "8px 12px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 14 };
const btn: React.CSSProperties = { padding: "8px 16px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 };
const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 13 };
const td: React.CSSProperties = { padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 14 };
const labelStyle: React.CSSProperties = { display: "block", fontSize: 12, color: "var(--text-secondary)", marginBottom: 4 };
