"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  getWorkspaceId,
  setWorkspaceId,
  apiFetch,
  apiFetchNoWorkspace,
} from "./api";

interface Workspace {
  id: string;
  name: string;
}

interface Strategy {
  id: string;
  name: string;
}

interface StrategyVersion {
  id: string;
  version: number;
}

interface Bot {
  id: string;
  name: string;
}

interface DemoSummary {
  workspaceId: string;
  strategyId: string;
  versionId: string;
  botId: string;
  runId?: string;
}

export default function FactoryPage() {
  const router = useRouter();
  const [wsId, setWsId] = useState("");
  const [saved, setSaved] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStatus, setDemoStatus] = useState<string | null>(null);
  const [demoSummary, setDemoSummary] = useState<DemoSummary | null>(null);
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

  async function createDemoSetup(autoStart: boolean) {
    setDemoRunning(true);
    setDemoSummary(null);
    setError(null);

    const suffix = Date.now() % 10000;

    try {
      // A) Create workspace
      setDemoStatus("Creating workspace...");
      const wsRes = await apiFetchNoWorkspace<Workspace>("/workspaces", {
        method: "POST",
        body: JSON.stringify({ name: `Demo Workspace ${suffix}` }),
      });
      if (!wsRes.ok) throw wsRes.problem;
      const workspaceId = wsRes.data.id;
      setWorkspaceId(workspaceId);
      setWsId(workspaceId);
      setSaved(workspaceId);

      // B) Create strategy
      setDemoStatus("Creating strategy...");
      let strategyName = "Demo Strategy";
      let stratRes = await apiFetch<Strategy>("/strategies", {
        method: "POST",
        body: JSON.stringify({ name: strategyName, symbol: "BTCUSDT", timeframe: "M5" }),
      });
      if (!stratRes.ok && stratRes.problem.status === 409) {
        strategyName = `Demo Strategy ${suffix}`;
        stratRes = await apiFetch<Strategy>("/strategies", {
          method: "POST",
          body: JSON.stringify({ name: strategyName, symbol: "BTCUSDT", timeframe: "M5" }),
        });
      }
      if (!stratRes.ok) throw stratRes.problem;
      const strategyId = stratRes.data.id;

      // C) Create strategy version
      setDemoStatus("Creating strategy version...");
      const verRes = await apiFetch<StrategyVersion>(`/strategies/${strategyId}/versions`, {
        method: "POST",
        body: JSON.stringify({ dslJson: { kind: "demo", entry: { type: "market" } } }),
      });
      if (!verRes.ok) throw verRes.problem;
      const versionId = verRes.data.id;

      // D) Create bot
      setDemoStatus("Creating bot...");
      let botName = "Demo Bot";
      let botRes = await apiFetch<Bot>("/bots", {
        method: "POST",
        body: JSON.stringify({
          name: botName,
          strategyVersionId: versionId,
          symbol: "BTCUSDT",
          timeframe: "M5",
        }),
      });
      if (!botRes.ok && botRes.problem.status === 409) {
        botName = `Demo Bot ${suffix}`;
        botRes = await apiFetch<Bot>("/bots", {
          method: "POST",
          body: JSON.stringify({
            name: botName,
            strategyVersionId: versionId,
            symbol: "BTCUSDT",
            timeframe: "M5",
          }),
        });
      }
      if (!botRes.ok) throw botRes.problem;
      const botId = botRes.data.id;

      // E) Optionally start a run
      let runId: string | undefined;
      if (autoStart) {
        setDemoStatus("Starting run...");
        const runRes = await apiFetch<{ id: string }>(`/bots/${botId}/runs`, {
          method: "POST",
        });
        if (runRes.ok) {
          runId = runRes.data.id;
        } else if (runRes.problem.status !== 409) {
          // 409 ActiveRunExists is fine — still redirect
          throw runRes.problem;
        }
      }

      // F) Success
      const summary: DemoSummary = { workspaceId, strategyId, versionId, botId, runId };
      setDemoSummary(summary);
      setDemoStatus("Done! Redirecting...");

      setTimeout(() => router.push(`/factory/bots/${botId}`), 600);
    } catch (err: unknown) {
      const prob = err as { title?: string; detail?: string };
      setError(`${prob.title ?? "Error"}: ${prob.detail ?? "Unknown error"}`);
      setDemoStatus(null);
    } finally {
      setDemoRunning(false);
    }
  }

  const busy = creating || demoRunning;

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
          <button style={btn} onClick={save} disabled={busy}>
            Save
          </button>
        </div>
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 12 }}>
          <button style={btnSecondary} onClick={createWorkspace} disabled={busy}>
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

      {/* Demo bootstrap */}
      <div style={{ ...card, marginTop: 16 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Quick Start</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginBottom: 12 }}>
          Creates a full demo stack: Workspace, Strategy, Version, and Bot in one click.
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={btnSecondary} onClick={() => createDemoSetup(false)} disabled={busy}>
            Create Demo Setup
          </button>
          <button style={btnAccent} onClick={() => createDemoSetup(true)} disabled={busy}>
            {demoRunning ? "Creating..." : "Create Demo + Start Run"}
          </button>
        </div>
        {demoStatus && (
          <p style={{ marginTop: 8, color: "var(--text-secondary)", fontSize: 13 }}>
            {demoStatus}
          </p>
        )}
        {demoSummary && (
          <div style={{ marginTop: 12, padding: 12, background: "var(--bg-secondary)", borderRadius: 6, fontSize: 12, fontFamily: "monospace" }}>
            <div>workspace: {demoSummary.workspaceId}</div>
            <div>strategy: {demoSummary.strategyId}</div>
            <div>version: {demoSummary.versionId}</div>
            <div>bot: {demoSummary.botId}</div>
            {demoSummary.runId && <div>run: {demoSummary.runId}</div>}
          </div>
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

const btnAccent: React.CSSProperties = {
  padding: "10px 20px",
  background: "#238636",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
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
