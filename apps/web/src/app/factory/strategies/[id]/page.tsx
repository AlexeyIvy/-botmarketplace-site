"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch, getWorkspaceId, type ProblemDetails } from "../../api";

interface StrategyVersion {
  id: string;
  version: number;
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

export default function StrategyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [strategy, setStrategy] = useState<StrategyDetail | null>(null);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [dsl, setDsl] = useState('{"kind":"stub"}');
  const [validateMsg, setValidateMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<StrategyDetail>(`/strategies/${id}`);
    if (res.ok) {
      setStrategy(res.data);
      setError(null);
    } else {
      setError(res.problem);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function validate() {
    setValidateMsg(null);
    setError(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(dsl);
    } catch {
      setValidateMsg("Invalid JSON");
      return;
    }
    const res = await apiFetch("/strategies/validate", {
      method: "POST",
      body: JSON.stringify({ dslJson: parsed }),
    });
    if (res.ok) {
      setValidateMsg("Valid!");
    } else {
      setError(res.problem);
    }
  }

  async function createVersion() {
    setError(null);
    setValidateMsg(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(dsl);
    } catch {
      setValidateMsg("Invalid JSON");
      return;
    }
    const res = await apiFetch(`/strategies/${id}/versions`, {
      method: "POST",
      body: JSON.stringify({ dslJson: parsed }),
    });
    if (res.ok) {
      load();
    } else {
      setError(res.problem);
    }
  }

  if (!getWorkspaceId()) {
    return (
      <div style={{ padding: "48px 24px" }}>
        <Link href="/factory">Set Workspace ID first</Link>
      </div>
    );
  }

  return (
    <div style={{ padding: "48px 24px", maxWidth: 700, margin: "0 auto" }}>
      <p style={{ marginBottom: 16 }}>
        <Link href="/factory/strategies">← Strategies</Link>
      </p>

      {error && <ErrorBox problem={error} />}

      {strategy && (
        <>
          <h1 style={{ fontSize: 24, marginBottom: 8 }}>{strategy.name}</h1>
          <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>
            {strategy.symbol} · {strategy.timeframe} · {strategy.status}
          </p>

          <div style={card}>
            <h3 style={{ marginBottom: 8 }}>New Version</h3>
            <textarea
              style={{ ...inputStyle, width: "100%", minHeight: 80, fontFamily: "monospace" }}
              value={dsl}
              onChange={(e) => setDsl(e.target.value)}
            />
            {validateMsg && (
              <p style={{ fontSize: 13, marginTop: 4, color: validateMsg === "Valid!" ? "#3fb950" : "#f85149" }}>
                {validateMsg}
              </p>
            )}
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button style={btnSecondary} onClick={validate}>Validate</button>
              <button style={btn} onClick={createVersion}>Create Version</button>
            </div>
          </div>

          <h3 style={{ marginTop: 24, marginBottom: 12 }}>Versions</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["#", "ID", "Created"].map((h) => (
                  <th key={h} style={th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {strategy.versions.map((v) => (
                <tr key={v.id}>
                  <td style={td}>v{v.version}</td>
                  <td style={{ ...td, fontFamily: "monospace", fontSize: 12 }}>{v.id}</td>
                  <td style={td}>{new Date(v.createdAt).toLocaleString()}</td>
                </tr>
              ))}
              {strategy.versions.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ ...td, color: "var(--text-secondary)" }}>No versions yet</td>
                </tr>
              )}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

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

const card: React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 };
const inputStyle: React.CSSProperties = { padding: "8px 12px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 14 };
const btn: React.CSSProperties = { padding: "8px 16px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 };
const btnSecondary: React.CSSProperties = { ...btn, background: "var(--bg-secondary)", border: "1px solid var(--border)" };
const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 13 };
const td: React.CSSProperties = { padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 14 };
