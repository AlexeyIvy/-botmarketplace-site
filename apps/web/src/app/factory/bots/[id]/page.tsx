"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch, getWorkspaceId, type ProblemDetails } from "../../api";

interface BotRun {
  id: string;
  state: string;
  startedAt: string | null;
  stoppedAt: string | null;
  errorCode: string | null;
  createdAt: string;
}

interface BotDetail {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  strategyVersion: {
    id: string;
    version: number;
    strategy: { id: string; name: string };
  };
  lastRun: BotRun | null;
}

interface BotEvent {
  id: string;
  ts: string;
  type: string;
  payloadJson: Record<string, unknown>;
}

export default function BotDetailPage() {
  const { id: botId } = useParams<{ id: string }>();
  const [bot, setBot] = useState<BotDetail | null>(null);
  const [events, setEvents] = useState<BotEvent[]>([]);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [polling, setPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadBot = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<BotDetail>(`/bots/${botId}`);
    if (res.ok) {
      setBot(res.data);
      setError(null);
      return res.data;
    } else {
      setError(res.problem);
      return null;
    }
  }, [botId]);

  const loadEvents = useCallback(async (runId: string) => {
    const res = await apiFetch<BotEvent[]>(`/runs/${runId}/events`);
    if (res.ok) setEvents(res.data);
  }, []);

  // Initial load
  useEffect(() => {
    loadBot().then((b) => {
      if (b?.lastRun) loadEvents(b.lastRun.id);
    });
  }, [loadBot, loadEvents]);

  // Polling
  useEffect(() => {
    if (polling && bot?.lastRun) {
      const runId = bot.lastRun.id;
      intervalRef.current = setInterval(async () => {
        const b = await loadBot();
        if (b?.lastRun) await loadEvents(b.lastRun.id);
        // Auto-stop polling if run is terminal
        if (b?.lastRun && ["STOPPED", "FAILED", "TIMED_OUT"].includes(b.lastRun.state)) {
          setPolling(false);
        }
      }, 2000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [polling, bot?.lastRun?.id, loadBot, loadEvents]);

  async function startRun() {
    setError(null);
    const res = await apiFetch<BotRun>(`/bots/${botId}/runs`, { method: "POST" });
    if (res.ok) {
      await loadBot().then((b) => {
        if (b?.lastRun) loadEvents(b.lastRun.id);
      });
      setPolling(true);
    } else {
      setError(res.problem);
    }
  }

  async function stopRun() {
    if (!bot?.lastRun) return;
    setError(null);
    const res = await apiFetch(`/bots/${botId}/runs/${bot.lastRun.id}/stop`, { method: "POST" });
    if (res.ok) {
      setPolling(false);
      await loadBot().then((b) => {
        if (b?.lastRun) loadEvents(b.lastRun.id);
      });
    } else {
      setError((res as { ok: false; problem: ProblemDetails }).problem);
    }
  }

  if (!getWorkspaceId()) {
    return (
      <div style={{ padding: "48px 24px" }}>
        <Link href="/factory">Set Workspace ID first</Link>
      </div>
    );
  }

  const lastRun = bot?.lastRun;
  const isActive = lastRun && !["STOPPED", "FAILED", "TIMED_OUT"].includes(lastRun.state);

  return (
    <div style={{ padding: "48px 24px", maxWidth: 800, margin: "0 auto" }}>
      <p style={{ marginBottom: 16 }}>
        <Link href="/factory/bots">← Bots</Link>
      </p>

      {error && <ErrorBox problem={error} />}

      {bot && (
        <>
          <h1 style={{ fontSize: 24, marginBottom: 8 }}>{bot.name}</h1>
          <p style={{ color: "var(--text-secondary)", marginBottom: 4 }}>
            {bot.symbol} · {bot.timeframe} · {bot.status}
          </p>
          <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 13 }}>
            Strategy: <strong>{bot.strategyVersion.strategy.name}</strong> v{bot.strategyVersion.version}
          </p>

          {/* Run controls */}
          <div style={{ ...card, display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <button style={btn} onClick={startRun} disabled={!!isActive}>
              Start Run
            </button>
            <button style={btnDanger} onClick={stopRun} disabled={!isActive}>
              Stop Run
            </button>
            <button style={btnSecondary} onClick={() => setPolling((p) => !p)}>
              {polling ? "Stop Polling" : "Start Polling"}
            </button>
            <button
              style={btnSecondary}
              onClick={() => {
                loadBot().then((b) => {
                  if (b?.lastRun) loadEvents(b.lastRun.id);
                });
              }}
            >
              Refresh
            </button>
            {lastRun && (
              <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                Last run: <strong>{lastRun.state}</strong>{" "}
                {lastRun.errorCode && `(${lastRun.errorCode})`}
              </span>
            )}
            {polling && <span style={{ fontSize: 12, color: "#3fb950" }}>● polling</span>}
          </div>

          {/* Events log */}
          <h3 style={{ marginTop: 24, marginBottom: 12 }}>Events</h3>
          {events.length > 0 ? (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["Time", "Type", "Payload"].map((h) => (
                    <th key={h} style={th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr key={ev.id}>
                    <td style={{ ...td, fontSize: 12, whiteSpace: "nowrap" }}>
                      {new Date(ev.ts).toLocaleTimeString()}
                    </td>
                    <td style={{ ...td, fontWeight: 600 }}>{ev.type}</td>
                    <td style={{ ...td, fontFamily: "monospace", fontSize: 12 }}>
                      {JSON.stringify(ev.payloadJson)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: "var(--text-secondary)" }}>
              {lastRun ? "No events yet" : "No runs yet — click Start Run"}
            </p>
          )}
        </>
      )}
    </div>
  );
}

function ErrorBox({ problem }: { problem: ProblemDetails }) {
  return (
    <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 6, padding: 12, marginBottom: 16 }}>
      <strong>{problem.title}</strong>: {problem.detail}
    </div>
  );
}

const card: React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 };
const btn: React.CSSProperties = { padding: "8px 16px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 };
const btnDanger: React.CSSProperties = { ...btn, background: "#da3633" };
const btnSecondary: React.CSSProperties = { ...btn, background: "var(--bg-secondary)", border: "1px solid var(--border)" };
const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 13 };
const td: React.CSSProperties = { padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 14 };
