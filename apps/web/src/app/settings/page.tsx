"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, apiFetchNoWorkspace, clearAuth, getToken } from "../../lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Me {
  id: string;
  email: string;
}

interface ExchangeConn {
  id: string;
  workspaceId: string;
  exchange: string;
  name: string;
  status: string;
  createdAt: string;
}

interface TestResult {
  id: string;
  status: string;
  detail: string;
}

type Theme = "system" | "dark" | "light";

const EMPTY_FORM = { exchange: "BYBIT", name: "", apiKey: "", secret: "" };

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const router = useRouter();

  // account
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // appearance
  const [theme, setTheme] = useState<Theme>("system");

  // exchange connections
  const [connections, setConnections] = useState<ExchangeConn[]>([]);
  const [connLoading, setConnLoading] = useState(false);
  const [connError, setConnError] = useState<string | null>(null);
  const [addForm, setAddForm] = useState(EMPTY_FORM);
  const [addError, setAddError] = useState<string | null>(null);
  const [addSaving, setAddSaving] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    const stored = localStorage.getItem("theme") as Theme | null;
    if (stored === "system" || stored === "dark" || stored === "light") {
      setTheme(stored);
    }
    setConnLoading(true);
    Promise.all([
      apiFetchNoWorkspace<Me>("/auth/me"),
      apiFetch<ExchangeConn[]>("/exchanges"),
    ]).then(([meRes, connsRes]) => {
      setLoading(false);
      setConnLoading(false);

      if (meRes.ok) {
        setMe(meRes.data);
      } else if (meRes.problem.status === 401) {
        setSessionExpired(true);
        return;
      } else {
        setError(`${meRes.problem.title}: ${meRes.problem.detail}`);
      }

      if (connsRes.ok) {
        setConnections(connsRes.data);
      } else if (connsRes.problem.status === 401) {
        setSessionExpired(true);
      } else {
        setConnError(`${connsRes.problem.title}: ${connsRes.problem.detail}`);
      }
    });
  }, [router]);

  function handleLogout() {
    clearAuth();
    router.push("/login");
  }

  function applyTheme(t: Theme) {
    localStorage.setItem("theme", t);
    setTheme(t);
    if (t === "light") {
      document.documentElement.classList.add("theme-light");
    } else if (t === "dark") {
      document.documentElement.classList.remove("theme-light");
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (prefersDark) {
        document.documentElement.classList.remove("theme-light");
      } else {
        document.documentElement.classList.add("theme-light");
      }
    }
  }

  async function handleAdd() {
    setAddError(null);
    const { exchange, name, apiKey, secret } = addForm;
    if (!name.trim() || !apiKey.trim() || !secret.trim()) {
      setAddError("All fields are required.");
      return;
    }
    setAddSaving(true);
    const res = await apiFetch<ExchangeConn>("/exchanges", {
      method: "POST",
      body: JSON.stringify({
        exchange,
        name: name.trim(),
        apiKey: apiKey.trim(),
        secret: secret.trim(),
      }),
    });
    setAddSaving(false);
    if (res.ok) {
      setConnections((prev) => [res.data, ...prev]);
      setAddForm({ ...EMPTY_FORM });
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
      setTestResults((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } else if (res.problem.status === 401) {
      setSessionExpired(true);
    } else {
      setConnError(`Delete failed: ${res.problem.detail}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Early returns
  // ---------------------------------------------------------------------------

  if (loading && !sessionExpired) {
    return <div style={wrap}><p style={hint}>Loading...</p></div>;
  }

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
      <h1 style={{ fontSize: 26, marginBottom: 24, fontWeight: 700 }}>Settings</h1>

      {/* Account block */}
      <section style={card}>
        <h2 style={sectionTitle}>Account</h2>
        {error && <p style={{ color: "#f85149", fontSize: 13, marginBottom: 12 }}>{error}</p>}
        <div style={field}>
          <span style={fieldLabel}>Email</span>
          <span style={fieldValue}>{me?.email ?? "—"}</span>
        </div>
        <div style={{ marginTop: 20 }}>
          <button onClick={handleLogout} style={logoutBtn}>Log out</button>
        </div>
      </section>

      {/* Appearance block */}
      <section style={card}>
        <h2 style={sectionTitle}>Appearance</h2>
        <div style={field}>
          <span style={fieldLabel}>Theme</span>
          <select
            value={theme}
            onChange={(e) => applyTheme(e.target.value as Theme)}
            style={themeSelect}
          >
            <option value="system">System</option>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
      </section>

      {/* Exchange Connections block */}
      <section style={card}>
        <h2 style={sectionTitle}>Exchange Connections</h2>

        {connLoading && <p style={hint}>Loading connections…</p>}
        {connError && (
          <p style={{ color: "#f85149", fontSize: 13, marginBottom: 12 }}>{connError}</p>
        )}

        {!connLoading && connections.length === 0 && (
          <p style={hint}>No connections yet.</p>
        )}

        {connections.map((conn) => {
          const tr = testResults[conn.id];
          return (
            <div key={conn.id} style={connRow}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <strong style={{ color: "var(--text-primary)", fontSize: 14 }}>{conn.name}</strong>
                <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{conn.exchange}</span>
                <StatusBadge status={conn.status} />
                {tr && (
                  <span
                    style={{
                      fontSize: 12,
                      color: tr.status === "CONNECTED" ? "#3fb950" : "#f85149",
                    }}
                  >
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
        <div style={addFormWrap}>
          <h3 style={addFormTitle}>Add Connection</h3>
          {addError && (
            <p style={{ color: "#f85149", fontSize: 13, marginBottom: 10 }}>{addError}</p>
          )}
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
            <button onClick={handleAdd} disabled={addSaving} style={primaryBtn}>
              {addSaving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      </section>
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
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        color,
        border: `1px solid ${color}`,
        borderRadius: 4,
        padding: "1px 6px",
        letterSpacing: "0.03em",
      }}
    >
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const wrap: React.CSSProperties = {
  maxWidth: 600,
  margin: "0 auto",
  padding: "48px 24px",
};

const card: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: "20px 24px",
  marginBottom: 24,
};

const sectionTitle: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 600,
  marginBottom: 16,
  color: "var(--text-primary)",
};

const field: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  fontSize: 14,
};

const fieldLabel: React.CSSProperties = {
  color: "var(--text-secondary)",
  minWidth: 60,
};

const fieldValue: React.CSSProperties = {
  color: "var(--text-primary)",
  fontWeight: 500,
};

const logoutBtn: React.CSSProperties = {
  padding: "8px 20px",
  background: "transparent",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontSize: 13,
};

const themeSelect: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 13,
  padding: "6px 10px",
  cursor: "pointer",
};

const connRow: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
  padding: "10px 0",
  borderBottom: "1px solid var(--border)",
};

const smallBtn: React.CSSProperties = {
  padding: "4px 12px",
  background: "transparent",
  border: "1px solid var(--border)",
  borderRadius: 5,
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontSize: 12,
};

const addFormWrap: React.CSSProperties = {
  marginTop: 20,
  borderTop: "1px solid var(--border)",
  paddingTop: 16,
};

const addFormTitle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  marginBottom: 12,
  color: "var(--text-primary)",
};

const inputStyle: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 13,
  padding: "8px 10px",
  width: "100%",
};

const primaryBtn: React.CSSProperties = {
  padding: "8px 20px",
  background: "var(--accent)",
  border: "none",
  borderRadius: 6,
  color: "#fff",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  alignSelf: "flex-start",
};

const hint: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 13,
};

const expiredBanner: React.CSSProperties = {
  background: "#f85149",
  color: "#fff",
  padding: "14px 18px",
  borderRadius: 8,
  display: "flex",
  alignItems: "center",
  gap: 14,
  fontSize: 14,
};

const expiredBtn: React.CSSProperties = {
  background: "rgba(255,255,255,0.2)",
  border: "1px solid rgba(255,255,255,0.4)",
  borderRadius: 4,
  color: "#fff",
  cursor: "pointer",
  fontSize: 13,
  padding: "4px 12px",
};
