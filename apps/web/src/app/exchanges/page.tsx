"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken } from "../factory/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExchangeConn {
  id: string;
  workspaceId: string;
  exchange: string;
  name: string;
  status: string;
  createdAt: string;
  /** docs/55-T5: true when a dedicated spot key is configured. */
  hasSpotKey?: boolean;
  /** docs/55-T5: free-form label for the spot key. */
  spotKeyLabel?: string | null;
}

interface TestResult {
  id: string;
  status: string;
  detail: string;
}

const EMPTY_FORM = {
  exchange: "BYBIT",
  name: "",
  apiKey: "",
  secret: "",
  // docs/55-T5: optional dedicated spot scope creds. Empty strings = "not
  // configured" — only sent to the API when both spotApiKey AND spotSecret
  // are filled (the backend enforces the both-or-neither rule).
  spotApiKey: "",
  spotSecret: "",
  spotKeyLabel: "",
};

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ExchangesPage() {
  const router = useRouter();

  const [connections, setConnections] = useState<ExchangeConn[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [addForm, setAddForm] = useState(EMPTY_FORM);
  const [addError, setAddError] = useState<string | null>(null);
  const [addSaving, setAddSaving] = useState(false);
  const [spotKeyExpanded, setSpotKeyExpanded] = useState(false);

  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});

  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    apiFetch<ExchangeConn[]>("/exchanges").then((res) => {
      setLoading(false);
      if (res.ok) {
        setConnections(res.data);
      } else if (res.problem.status === 401) {
        setSessionExpired(true);
      } else {
        setListError(`${res.problem.title}: ${res.problem.detail}`);
      }
    });
  }, [router]);

  async function handleAdd() {
    setAddError(null);
    const { exchange, name, apiKey, secret, spotApiKey, spotSecret, spotKeyLabel } = addForm;
    if (!name.trim() || !apiKey.trim() || !secret.trim()) {
      setAddError("Name, API key and secret are required.");
      return;
    }
    // Both-or-neither rule for the spot pair. Mirrors the backend
    // validator at apps/api/src/routes/exchanges.ts; surfacing it client-side
    // means the operator gets immediate feedback instead of a round-trip
    // 400.
    const trimmedSpotKey = spotApiKey.trim();
    const trimmedSpotSecret = spotSecret.trim();
    if (Boolean(trimmedSpotKey) !== Boolean(trimmedSpotSecret)) {
      setAddError(
        "Spot API key and spot secret must be supplied together (or both left blank for single-key fallback).",
      );
      return;
    }

    const body: Record<string, unknown> = {
      exchange,
      name: name.trim(),
      apiKey: apiKey.trim(),
      secret: secret.trim(),
    };
    if (trimmedSpotKey && trimmedSpotSecret) {
      body.spotApiKey = trimmedSpotKey;
      body.spotSecret = trimmedSpotSecret;
      const trimmedLabel = spotKeyLabel.trim();
      if (trimmedLabel) body.spotKeyLabel = trimmedLabel;
    }

    setAddSaving(true);
    const res = await apiFetch<ExchangeConn>("/exchanges", {
      method: "POST",
      body: JSON.stringify(body),
    });
    setAddSaving(false);
    if (res.ok) {
      setConnections((prev) => [res.data, ...prev]);
      setAddForm({ ...EMPTY_FORM });
      setSpotKeyExpanded(false);
    } else if (res.problem.status === 401) {
      setSessionExpired(true);
    } else {
      const errs = res.problem.errors?.map((e) => e.message).join(", ");
      setAddError(errs ?? `${res.problem.title}: ${res.problem.detail}`);
    }
  }

  async function handleTest(id: string) {
    setTesting((prev) => ({ ...prev, [id]: true }));
    const res = await apiFetch<TestResult>(`/exchanges/${id}/test`, { method: "POST" });
    setTesting((prev) => ({ ...prev, [id]: false }));
    if (res.ok) {
      setTestResults((prev) => ({ ...prev, [id]: res.data }));
      setConnections((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: res.data.status } : c))
      );
    } else if (res.problem.status === 401) {
      setSessionExpired(true);
    } else {
      setTestResults((prev) => ({
        ...prev,
        [id]: { id, status: "FAILED", detail: res.problem.detail },
      }));
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`Delete exchange connection "${name}"?`)) return;
    const res = await apiFetch<void>(`/exchanges/${id}`, { method: "DELETE" });
    if (res.ok) {
      setConnections((prev) => prev.filter((c) => c.id !== id));
      setTestResults((prev) => { const n = { ...prev }; delete n[id]; return n; });
    } else if (res.problem.status === 401) {
      setSessionExpired(true);
    } else {
      setListError(`Delete failed: ${res.problem.detail}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Early returns
  // ---------------------------------------------------------------------------

  if (sessionExpired) {
    return (
      <div style={wrap}>
        <div style={expiredBanner}>
          <span>Session expired. Please log in again.</span>
          <button onClick={() => router.push("/login")} style={expiredBtn}>Log in</button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={wrap}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Exchange Connections</h1>

      {loading && <p style={hint}>Loading…</p>}
      {listError && <p style={{ color: "#f85149", fontSize: 13, marginBottom: 12 }}>{listError}</p>}

      {!loading && connections.length === 0 && (
        <p style={hint}>No connections yet. Add one below.</p>
      )}

      {connections.map((conn) => {
        const tr = testResults[conn.id];
        return (
          <div key={conn.id} style={connRow}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", flex: 1 }}>
              <strong style={{ color: "var(--text-primary)", fontSize: 14 }}>{conn.name}</strong>
              <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{conn.exchange}</span>
              <StatusBadge status={conn.status} />
              {conn.hasSpotKey && (
                <span
                  style={spotPillStyle}
                  title={
                    conn.spotKeyLabel
                      ? `Dedicated spot key: ${conn.spotKeyLabel}`
                      : "Dedicated spot key configured"
                  }
                >
                  + Spot
                </span>
              )}
              {tr && (
                <span style={{ fontSize: 12, color: tr.status === "CONNECTED" ? "#3fb950" : "#f85149" }}>
                  {tr.detail}
                </span>
              )}
            </div>
            <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
              <button
                onClick={() => handleTest(conn.id)}
                disabled={!!testing[conn.id]}
                style={smallBtn}
              >
                {testing[conn.id] ? "Testing…" : "Test"}
              </button>
              <button
                onClick={() => handleDelete(conn.id, conn.name)}
                style={{ ...smallBtn, color: "#f85149", borderColor: "#f85149" }}
              >
                Delete
              </button>
            </div>
          </div>
        );
      })}

      {/* Add form */}
      <div style={addCard}>
        <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, color: "var(--text-primary)" }}>
          Add Connection
        </h2>
        {addError && <p style={{ color: "#f85149", fontSize: 13, marginBottom: 10 }}>{addError}</p>}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <select
            value={addForm.exchange}
            onChange={(e) => setAddForm((f) => ({ ...f, exchange: e.target.value }))}
            style={inputStyle}
          >
            <option value="BYBIT">Bybit</option>
          </select>
          <input
            placeholder="Name"
            value={addForm.name}
            onChange={(e) => setAddForm((f) => ({ ...f, name: e.target.value }))}
            style={inputStyle}
          />
          <input
            placeholder="API Key"
            value={addForm.apiKey}
            onChange={(e) => setAddForm((f) => ({ ...f, apiKey: e.target.value }))}
            style={inputStyle}
            autoComplete="off"
          />
          <input
            type="password"
            placeholder="Secret"
            value={addForm.secret}
            onChange={(e) => setAddForm((f) => ({ ...f, secret: e.target.value }))}
            style={inputStyle}
            autoComplete="new-password"
          />

          {/* docs/55-T5: optional dedicated spot scope creds. Hidden by
              default — single-key Bybit accounts work fine without them
              (the executor falls back to the linear pair). Operators who
              want a separate scope for funding-arb expand this section. */}
          <button
            type="button"
            onClick={() => setSpotKeyExpanded((v) => !v)}
            style={spotToggleStyle}
          >
            {spotKeyExpanded ? "▾" : "▸"} Spot key (optional, for funding arbitrage)
          </button>
          {spotKeyExpanded && (
            <div style={spotSectionStyle}>
              <input
                placeholder="Spot API Key"
                value={addForm.spotApiKey}
                onChange={(e) => setAddForm((f) => ({ ...f, spotApiKey: e.target.value }))}
                style={inputStyle}
                autoComplete="off"
              />
              <input
                type="password"
                placeholder="Spot Secret"
                value={addForm.spotSecret}
                onChange={(e) => setAddForm((f) => ({ ...f, spotSecret: e.target.value }))}
                style={inputStyle}
                autoComplete="new-password"
              />
              <input
                placeholder="Label (e.g. 'Funding-arb spot')"
                value={addForm.spotKeyLabel}
                onChange={(e) => setAddForm((f) => ({ ...f, spotKeyLabel: e.target.value }))}
                style={inputStyle}
              />
              <p style={spotHintStyle}>
                Required only for funding arbitrage strategy. Leave blank to
                reuse the linear key for spot calls (single-key Bybit).
              </p>
            </div>
          )}

          <button onClick={handleAdd} disabled={addSaving} style={primaryBtn}>
            {addSaving ? "Saving…" : "Add Connection"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "CONNECTED" ? "#3fb950" :
    status === "FAILED"    ? "#f85149" :
                             "#8b949e";
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, color,
      border: `1px solid ${color}`, borderRadius: 4,
      padding: "1px 6px", letterSpacing: "0.03em",
    }}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const wrap: React.CSSProperties = { maxWidth: 600, margin: "0 auto", padding: "48px 24px" };

const hint: React.CSSProperties = { color: "var(--text-secondary)", fontSize: 13, marginBottom: 12 };

const connRow: React.CSSProperties = {
  display: "flex", alignItems: "center", justifyContent: "space-between",
  gap: 12, padding: "12px 0", borderBottom: "1px solid var(--border)",
};

const addCard: React.CSSProperties = {
  marginTop: 28, padding: "20px 24px",
  background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8,
};

const smallBtn: React.CSSProperties = {
  padding: "4px 12px", background: "transparent",
  border: "1px solid var(--border)", borderRadius: 5,
  color: "var(--text-secondary)", cursor: "pointer", fontSize: 12,
};

const inputStyle: React.CSSProperties = {
  background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6,
  color: "var(--text-primary)", fontSize: 13, padding: "8px 10px", width: "100%",
};

const primaryBtn: React.CSSProperties = {
  padding: "8px 20px", background: "var(--accent)", border: "none", borderRadius: 6,
  color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600, alignSelf: "flex-start",
};

const expiredBanner: React.CSSProperties = {
  background: "#f85149", color: "#fff", padding: "14px 18px", borderRadius: 8,
  display: "flex", alignItems: "center", gap: 14, fontSize: 14,
};

const expiredBtn: React.CSSProperties = {
  background: "rgba(255,255,255,0.2)", border: "1px solid rgba(255,255,255,0.4)",
  borderRadius: 4, color: "#fff", cursor: "pointer", fontSize: 13, padding: "4px 12px",
};

// docs/55-T5: spot-key UI primitives. Same amber as the BETA badge so the
// "this is the funding-arb feature" visual cue carries across pages.
const spotPillStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  padding: "1px 6px",
  borderRadius: 4,
  color: "#F59E0B",
  background: "rgba(245, 158, 11, 0.12)",
  border: "1px solid rgba(245, 158, 11, 0.45)",
  cursor: "help",
};

const spotToggleStyle: React.CSSProperties = {
  textAlign: "left",
  background: "transparent",
  border: "none",
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontSize: 12,
  padding: "4px 0",
  fontFamily: "inherit",
};

const spotSectionStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  paddingLeft: 12,
  borderLeft: "2px solid rgba(245, 158, 11, 0.35)",
  marginLeft: 2,
};

const spotHintStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 11,
  color: "var(--text-secondary)",
  lineHeight: 1.4,
};
