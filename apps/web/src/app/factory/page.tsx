"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getWorkspaceId, setWorkspaceId, apiFetchNoWorkspace } from "./api";

interface Workspace {
  id: string;
  name: string;
}

export default function FactoryPage() {
  const [wsId, setWsId] = useState("");
  const [saved, setSaved] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = getWorkspaceId();
    if (stored) {
      setWsId(stored);
      setSaved(stored);
    }
  }, []);

  function save() {
    const trimmed = wsId.trim();
    if (!trimmed) return;
    setWorkspaceId(trimmed);
    setSaved(trimmed);
    setError(null);
  }

  async function createWorkspace() {
    setCreating(true);
    setError(null);
    const res = await apiFetchNoWorkspace<Workspace>("/workspaces", {
      method: "POST",
      body: JSON.stringify({}),
    });
    setCreating(false);
    if (res.ok) {
      setWsId(res.data.id);
      setWorkspaceId(res.data.id);
      setSaved(res.data.id);
    } else {
      setError(`${res.problem.title}: ${res.problem.detail}`);
    }
  }

  return (
    <div style={{ padding: "48px 24px", maxWidth: 600, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, marginBottom: 24 }}>Bot Factory</h1>

      <div style={card}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Workspace</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            style={input}
            placeholder="Workspace UUID"
            value={wsId}
            onChange={(e) => setWsId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && save()}
          />
          <button style={btn} onClick={save}>
            Save
          </button>
        </div>
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 12 }}>
          <button style={btnSecondary} onClick={createWorkspace} disabled={creating}>
            {creating ? "Creating..." : "Create Workspace"}
          </button>
          {saved && (
            <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
              Active: <code>{saved}</code>
            </span>
          )}
        </div>
        {error && (
          <p style={{ marginTop: 8, color: "#f85149", fontSize: 13 }}>{error}</p>
        )}
      </div>

      {saved ? (
        <div style={{ display: "flex", gap: 16, marginTop: 24 }}>
          <Link href="/factory/strategies" style={linkCard}>
            Strategies
          </Link>
          <Link href="/factory/bots" style={linkCard}>
            Bots
          </Link>
        </div>
      ) : (
        <p style={{ marginTop: 24, color: "var(--text-secondary)" }}>
          Set a Workspace ID or create a new one to continue.
        </p>
      )}
    </div>
  );
}

const card: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: 16,
};

const input: React.CSSProperties = {
  flex: 1,
  padding: "8px 12px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 14,
};

const btn: React.CSSProperties = {
  padding: "8px 16px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 14,
};

const btnSecondary: React.CSSProperties = {
  padding: "8px 16px",
  background: "var(--bg-secondary)",
  color: "var(--text-primary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 14,
};

const linkCard: React.CSSProperties = {
  flex: 1,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 24,
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 18,
  fontWeight: 600,
};
