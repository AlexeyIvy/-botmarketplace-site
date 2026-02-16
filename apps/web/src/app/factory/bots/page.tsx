"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { apiFetch, getWorkspaceId, type ProblemDetails } from "../api";

interface Bot {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  strategyVersionId: string;
  updatedAt: string;
}

const TIMEFRAMES = ["M1", "M5", "M15", "H1"];

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [name, setName] = useState("");
  const [svId, setSvId] = useState("");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("H1");

  const load = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<Bot[]>("/bots");
    if (res.ok) {
      setBots(res.data);
      setError(null);
    } else {
      setError(res.problem);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    const res = await apiFetch<Bot>("/bots", {
      method: "POST",
      body: JSON.stringify({ name, strategyVersionId: svId, symbol, timeframe }),
    });
    if (res.ok) {
      setName("");
      setSvId("");
      setError(null);
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
    <div style={{ padding: "48px 24px", maxWidth: 800, margin: "0 auto" }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>Bots</h1>

      {error && <ErrorBox problem={error} />}

      <form onSubmit={create} style={card}>
        <h3 style={{ marginBottom: 12 }}>Create Bot</h3>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input style={input} placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input style={{ ...input, flex: 2 }} placeholder="Strategy Version ID" value={svId} onChange={(e) => setSvId(e.target.value)} required />
          <input style={{ ...input, width: 120 }} placeholder="Symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)} required />
          <select style={input} value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            {TIMEFRAMES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button style={btn} type="submit">Create</button>
        </div>
      </form>

      <table style={{ width: "100%", marginTop: 24, borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Name", "Symbol", "TF", "Status", "Updated"].map((h) => (
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
              <td style={td}>{new Date(b.updatedAt).toLocaleString()}</td>
            </tr>
          ))}
          {bots.length === 0 && (
            <tr>
              <td colSpan={5} style={{ ...td, color: "var(--text-secondary)" }}>No bots yet</td>
            </tr>
          )}
        </tbody>
      </table>
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
const input: React.CSSProperties = { padding: "8px 12px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 14 };
const btn: React.CSSProperties = { padding: "8px 16px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 };
const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 13 };
const td: React.CSSProperties = { padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 14 };
