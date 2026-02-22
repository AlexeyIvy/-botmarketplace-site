"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch, getWorkspaceId, type ProblemDetails } from "../../api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DslBody {
  id?: string;
  name?: string;
  dslVersion?: number;
  enabled?: boolean;
  market?: { exchange: string; env: string; category: string; symbol: string };
  entry?: { side?: string; signal?: string };
  risk?: { maxPositionSizeUsd?: number; riskPerTradePct?: number; cooldownSeconds?: number };
  execution?: { orderType?: string; clientOrderIdPrefix?: string };
  guards?: { maxOpenPositions?: number; maxOrdersPerMinute?: number; pauseOnError?: boolean };
}

interface StrategyVersion {
  id: string;
  version: number;
  dslJson: DslBody;
  createdAt: string;
}

interface StrategyDetail {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  versions: StrategyVersion[];
}

// Default form values for a new DSL body built from the strategy metadata
function defaultForm(strategy: StrategyDetail): DslBody {
  return {
    id: `${strategy.id}-v1`,
    name: strategy.name,
    dslVersion: 1,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: strategy.symbol },
    entry: { side: "Buy", signal: "manual" },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 1, cooldownSeconds: 60 },
    execution: { orderType: "Market", clientOrderIdPrefix: "bot" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

// One-line summary shown in version history
function dslSummary(dsl: DslBody): string {
  const orderType = dsl.execution?.orderType ?? "?";
  const side = dsl.entry?.side ?? "?";
  const risk = dsl.risk?.riskPerTradePct != null ? `${dsl.risk.riskPerTradePct}% risk` : "";
  const maxPos = dsl.risk?.maxPositionSizeUsd != null ? `$${dsl.risk.maxPositionSizeUsd} max` : "";
  const enabled = dsl.enabled === false ? "disabled" : "enabled";
  return [orderType, side, risk, maxPos, enabled].filter(Boolean).join(" · ");
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function StrategyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [strategy, setStrategy] = useState<StrategyDetail | null>(null);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [validateMsg, setValidateMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Structured form state
  const [form, setForm] = useState<DslBody>({});

  // Advanced: toggle raw JSON view
  const [showRaw, setShowRaw] = useState(false);
  const [rawJson, setRawJson] = useState("");

  const load = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<StrategyDetail>(`/strategies/${id}`);
    if (res.ok) {
      setStrategy(res.data);
      setError(null);
      const dfl = defaultForm(res.data);
      setForm(dfl);
      setRawJson(JSON.stringify(dfl, null, 2));
    } else {
      setError(res.problem);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  function toggleRaw() {
    if (!showRaw) setRawJson(JSON.stringify(buildDsl(), null, 2));
    setShowRaw((v) => !v);
  }

  function buildDsl(): DslBody {
    if (showRaw) {
      try { return JSON.parse(rawJson) as DslBody; } catch { return form; }
    }
    return form;
  }

  function setNested<K extends keyof DslBody>(section: K, field: string, value: unknown) {
    setForm((prev) => ({
      ...prev,
      [section]: { ...(prev[section] as Record<string, unknown>), [field]: value },
    }));
    setValidateMsg(null);
    setError(null);
  }

  async function validate() {
    setBusy(true);
    setValidateMsg(null);
    setError(null);
    const res = await apiFetch<{ ok: boolean; message: string }>("/strategies/validate", {
      method: "POST",
      body: JSON.stringify({ dslJson: buildDsl() }),
    });
    setBusy(false);
    if (res.ok) setValidateMsg(res.data.message ?? "DSL is valid");
    else setError(res.problem);
  }

  async function createVersion() {
    setBusy(true);
    setError(null);
    setValidateMsg(null);
    const res = await apiFetch(`/strategies/${id}/versions`, {
      method: "POST",
      body: JSON.stringify({ dslJson: buildDsl() }),
    });
    setBusy(false);
    if (res.ok) { await load(); setValidateMsg("Version saved!"); }
    else setError(res.problem);
  }

  if (!getWorkspaceId()) {
    return (
      <div style={{ padding: "48px 24px" }}>
        <Link href="/factory">Set Workspace ID first</Link>
      </div>
    );
  }

  return (
    <div style={{ padding: "48px 24px", maxWidth: 720, margin: "0 auto" }}>
      <p style={{ marginBottom: 16 }}>
        <Link href="/factory/strategies">← Strategies</Link>
      </p>

      {error && <ErrorBox problem={error} />}

      {strategy && (
        <>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>{strategy.name}</h1>
          <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 14 }}>
            {strategy.symbol} · {strategy.timeframe} · {strategy.status}
          </p>

          {/* ── DSL Editor card ────────────────────────────────────────── */}
          <div style={card}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 16 }}>New Version (DSL v1)</h3>
              <button style={btnLink} onClick={toggleRaw}>
                {showRaw ? "← Structured form" : "Raw JSON ↗"}
              </button>
            </div>

            {showRaw ? (
              <textarea
                style={{ ...inputStyle, width: "100%", minHeight: 260, fontFamily: "monospace", fontSize: 12, boxSizing: "border-box", display: "block" }}
                value={rawJson}
                onChange={(e) => { setRawJson(e.target.value); setValidateMsg(null); setError(null); }}
              />
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>

                <Section label="Entry">
                  <Row label="Side">
                    <Select value={form.entry?.side ?? "Buy"} options={["Buy", "Sell"]} onChange={(v) => setNested("entry", "side", v)} />
                  </Row>
                  <Row label="Signal source">
                    <Select value={form.entry?.signal ?? "manual"} options={["manual", "webhook"]} onChange={(v) => setNested("entry", "signal", v)} />
                  </Row>
                </Section>

                <Section label="Risk">
                  <Row label="Max position (USD)">
                    <NumberInput value={form.risk?.maxPositionSizeUsd ?? 100} min={1} step={10} onChange={(v) => setNested("risk", "maxPositionSizeUsd", v)} />
                  </Row>
                  <Row label="Risk per trade (%)">
                    <NumberInput value={form.risk?.riskPerTradePct ?? 1} min={0.1} max={100} step={0.1} onChange={(v) => setNested("risk", "riskPerTradePct", v)} />
                  </Row>
                  <Row label="Cooldown (seconds)">
                    <NumberInput value={form.risk?.cooldownSeconds ?? 60} min={0} step={10} integer onChange={(v) => setNested("risk", "cooldownSeconds", v)} />
                  </Row>
                </Section>

                <Section label="Execution">
                  <Row label="Order type">
                    <Select value={form.execution?.orderType ?? "Market"} options={["Market", "Limit"]} onChange={(v) => setNested("execution", "orderType", v)} />
                  </Row>
                  <Row label="Client ID prefix">
                    <input
                      style={{ ...inputStyle, width: 160 }}
                      value={form.execution?.clientOrderIdPrefix ?? "bot"}
                      onChange={(e) => setNested("execution", "clientOrderIdPrefix", e.target.value)}
                      placeholder="e.g. mybot"
                    />
                  </Row>
                </Section>

                <Section label="Guards">
                  <Row label="Max orders/minute">
                    <NumberInput value={form.guards?.maxOrdersPerMinute ?? 10} min={1} max={120} step={1} integer onChange={(v) => setNested("guards", "maxOrdersPerMinute", v)} />
                  </Row>
                  <Row label="Pause on error">
                    <input
                      type="checkbox"
                      checked={form.guards?.pauseOnError ?? true}
                      onChange={(e) => setNested("guards", "pauseOnError", e.target.checked)}
                      style={{ width: 16, height: 16, cursor: "pointer" }}
                    />
                  </Row>
                  <Row label="Max open positions">
                    <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>1 (fixed, MVP)</span>
                  </Row>
                </Section>
              </div>
            )}

            {validateMsg && (
              <p style={{ fontSize: 13, marginTop: 12, color: (validateMsg.includes("valid") || validateMsg === "Version saved!") ? "#3fb950" : "#f85149" }}>
                {validateMsg}
              </p>
            )}

            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button style={btnSecondary} onClick={validate} disabled={busy}>
                {busy ? "…" : "Validate"}
              </button>
              <button style={btn} onClick={createVersion} disabled={busy}>
                {busy ? "Saving…" : "Save Version"}
              </button>
            </div>
          </div>

          {/* ── Version History ───────────────────────────────────────── */}
          <h3 style={{ marginTop: 28, marginBottom: 12, fontSize: 16 }}>
            Version History ({strategy.versions.length})
          </h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Ver", "Summary", "Created", "ID"].map((h) => (
                  <th key={h} style={th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {strategy.versions.map((v) => (
                <tr key={v.id}>
                  <td style={{ ...td, fontWeight: 600 }}>v{v.version}</td>
                  <td style={{ ...td, color: "var(--text-secondary)", fontSize: 13 }}>
                    {dslSummary(v.dslJson)}
                  </td>
                  <td style={{ ...td, fontSize: 13 }}>{new Date(v.createdAt).toLocaleString()}</td>
                  <td style={{ ...td, fontFamily: "monospace", fontSize: 11, color: "var(--text-secondary)" }}>
                    {v.id.slice(0, 8)}…
                  </td>
                </tr>
              ))}
              {strategy.versions.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ ...td, color: "var(--text-secondary)" }}>
                    No versions yet — fill the form above and click Save Version
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small UI helpers
// ---------------------------------------------------------------------------

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: 1, color: "var(--text-secondary)", marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ display: "flex", flexDirection: "column" as const, gap: 8 }}>{children}</div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <label style={{ width: 180, fontSize: 13, color: "var(--text-secondary)", flexShrink: 0 }}>{label}</label>
      {children}
    </div>
  );
}

function Select({ value, options, onChange }: { value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <select style={inputStyle} value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function NumberInput({ value, min, max, step, integer, onChange }: {
  value: number; min?: number; max?: number; step?: number; integer?: boolean; onChange: (v: number) => void;
}) {
  return (
    <input
      type="number"
      style={{ ...inputStyle, width: 120 }}
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={(e) => {
        const v = integer ? parseInt(e.target.value, 10) : parseFloat(e.target.value);
        if (!isNaN(v)) onChange(v);
      }}
    />
  );
}

function ErrorBox({ problem }: { problem: ProblemDetails }) {
  return (
    <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 6, padding: 12, marginBottom: 16 }}>
      <strong>{problem.title}</strong>
      {problem.detail && <span>: {problem.detail}</span>}
      {problem.errors && problem.errors.length > 0 && (
        <ul style={{ margin: "8px 0 0 0", paddingLeft: 16 }}>
          {problem.errors.map((e, i) => (
            <li key={i} style={{ fontSize: 13, marginTop: 2 }}>
              <code style={{ color: "#f85149" }}>{e.field}</code>: {e.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const card: React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: 20 };
const inputStyle: React.CSSProperties = { padding: "6px 10px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 14 };
const btn: React.CSSProperties = { padding: "8px 16px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 };
const btnSecondary: React.CSSProperties = { ...btn, background: "transparent", border: "1px solid var(--border)", color: "var(--text-primary)" };
const btnLink: React.CSSProperties = { background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "var(--text-secondary)", padding: 0 };
const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 12 };
const td: React.CSSProperties = { padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 14, verticalAlign: "middle" };
