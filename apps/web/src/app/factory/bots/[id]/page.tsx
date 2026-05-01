"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch, getWorkspaceId, type ProblemDetails } from "../../api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BotRun {
  id: string;
  state: string;
  symbol: string;
  startedAt: string | null;
  stoppedAt: string | null;
  errorCode: string | null;
  durationMinutes: number | null;
  createdAt: string;
}

interface BotDetail {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  exchangeConnectionId: string | null;
  templateSlug: string | null;
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

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function BotDetailPage() {
  const { id: botId } = useParams<{ id: string }>();
  const [bot, setBot] = useState<BotDetail | null>(null);
  const [events, setEvents] = useState<BotEvent[]>([]);
  const [runs, setRuns] = useState<BotRun[]>([]);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [polling, setPolling] = useState(false);
  const [durationMinutes, setDurationMinutes] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---------------------------------------------------------------------------
  // Loaders
  // ---------------------------------------------------------------------------

  const loadBot = useCallback(async () => {
    if (!getWorkspaceId()) return null;
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

  const loadRuns = useCallback(async () => {
    if (!getWorkspaceId()) return;
    const res = await apiFetch<BotRun[]>(`/bots/${botId}/runs?limit=10`);
    if (res.ok) setRuns(res.data);
  }, [botId]);

  // Initial load
  useEffect(() => {
    loadBot().then((b) => {
      if (b?.lastRun) loadEvents(b.lastRun.id);
    });
    loadRuns();
  }, [loadBot, loadEvents, loadRuns]);

  // Polling loop — refreshes bot state and events every 2s while active
  useEffect(() => {
    if (polling && bot?.lastRun) {
      intervalRef.current = setInterval(async () => {
        const b = await loadBot();
        if (b?.lastRun) await loadEvents(b.lastRun.id);
        await loadRuns();
        if (b?.lastRun && ["STOPPED", "FAILED", "TIMED_OUT"].includes(b.lastRun.state)) {
          setPolling(false);
        }
      }, 2000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [polling, bot?.lastRun?.id, loadBot, loadEvents, loadRuns]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function startRun() {
    setError(null);
    const body: Record<string, unknown> = {};
    const dur = parseInt(durationMinutes, 10);
    if (!isNaN(dur) && dur >= 1) body.durationMinutes = dur;

    const res = await apiFetch<BotRun>(`/bots/${botId}/runs`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (res.ok) {
      await loadBot().then((b) => {
        if (b?.lastRun) loadEvents(b.lastRun.id);
      });
      await loadRuns();
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
      await loadRuns();
    } else {
      setError((res as { ok: false; problem: ProblemDetails }).problem);
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

  const lastRun = bot?.lastRun;
  const isActive = lastRun && !["STOPPED", "FAILED", "TIMED_OUT"].includes(lastRun.state);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={{ padding: "48px 24px", maxWidth: 860, margin: "0 auto" }}>
      <p style={{ marginBottom: 16 }}>
        <Link href="/factory/bots">← Bots</Link>
      </p>

      {error && <ErrorBox problem={error} />}

      {bot && (
        <>
          {/* ── Bot header ─────────────────────────────────── */}
          <h1 style={{ fontSize: 24, marginBottom: 6 }}>{bot.name}</h1>
          <p style={{ color: "var(--text-secondary)", marginBottom: 4 }}>
            {bot.symbol} · {bot.timeframe} · {bot.status}
          </p>
          {bot.templateSlug && (
            <p style={{ marginBottom: 4 }}>
              <span style={presetBadge}>From preset: {bot.templateSlug}</span>
            </p>
          )}
          <p style={{ color: "var(--text-secondary)", marginBottom: 4, fontSize: 13 }}>
            Strategy:{" "}
            <Link href={`/factory/strategies/${bot.strategyVersion.strategy.id}`}>
              <strong>{bot.strategyVersion.strategy.name}</strong>
            </Link>{" "}
            v{bot.strategyVersion.version}
          </p>
          {bot.exchangeConnectionId && (
            <p style={{ color: "var(--text-secondary)", marginBottom: 4, fontSize: 13 }}>
              Exchange Connection:{" "}
              <code style={{ fontSize: 12 }}>{bot.exchangeConnectionId}</code>
            </p>
          )}

          {/* ── Run controls ───────────────────────────────── */}
          <div style={{ ...card, marginTop: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
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
                  loadBot().then((b) => { if (b?.lastRun) loadEvents(b.lastRun.id); });
                  loadRuns();
                }}
              >
                Refresh
              </button>
              {lastRun && (
                <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                  Last run:{" "}
                  <strong style={{ color: stateColor(lastRun.state) }}>{lastRun.state}</strong>
                  {lastRun.errorCode && ` (${lastRun.errorCode})`}
                  {lastRun.durationMinutes != null && ` · limit ${lastRun.durationMinutes}min`}
                </span>
              )}
              {polling && <span style={{ fontSize: 12, color: "#3fb950" }}>● polling</span>}
            </div>

            {/* durationMinutes input for next run */}
            <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 8 }}>
              <label style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                Run limit (min):
              </label>
              <input
                style={{ ...input, width: 80 }}
                type="number"
                min="1"
                max="1440"
                placeholder="∞"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
                disabled={!!isActive}
              />
              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                leave blank for server default (4 h)
              </span>
            </div>
          </div>

          {/* ── Events log ─────────────────────────────────── */}
          <h3 style={{ marginTop: 28, marginBottom: 10 }}>Events (last run)</h3>
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
                    <td style={{ ...td, fontFamily: "monospace", fontSize: 11, wordBreak: "break-all" }}>
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

          {/* ── Run history ────────────────────────────────── */}
          <h3 style={{ marginTop: 28, marginBottom: 10 }}>
            Run History{" "}
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
              (click row to load events)
            </span>
          </h3>
          {runs.length > 0 ? (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["State", "Started", "Stopped", "Limit", "Error"].map((h) => (
                    <th key={h} style={th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr
                    key={r.id}
                    style={{ cursor: "pointer" }}
                    onClick={() => loadEvents(r.id)}
                    title="Click to load events for this run"
                  >
                    <td style={td}>
                      <span style={{ fontWeight: 600, color: stateColor(r.state) }}>{r.state}</span>
                    </td>
                    <td style={{ ...td, fontSize: 12 }}>
                      {r.startedAt ? new Date(r.startedAt).toLocaleTimeString() : "—"}
                    </td>
                    <td style={{ ...td, fontSize: 12 }}>
                      {r.stoppedAt ? new Date(r.stoppedAt).toLocaleTimeString() : "—"}
                    </td>
                    <td style={td}>
                      {r.durationMinutes != null ? `${r.durationMinutes}min` : "—"}
                    </td>
                    <td style={{ ...td, fontSize: 12, color: "#f85149" }}>
                      {r.errorCode ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: "var(--text-secondary)" }}>No run history yet</p>
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers + sub-components
// ---------------------------------------------------------------------------

function stateColor(state: string): string {
  if (["STOPPED", "TIMED_OUT"].includes(state)) return "var(--text-secondary)";
  if (state === "FAILED") return "#f85149";
  if (state === "RUNNING") return "#3fb950";
  return "var(--text-primary)";
}

function ErrorBox({ problem }: { problem: ProblemDetails }) {
  return (
    <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 6, padding: 12, marginBottom: 16 }}>
      <strong>{problem.title}</strong>: {problem.detail}
    </div>
  );
}

const card: React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 };
const input: React.CSSProperties = { padding: "6px 10px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 14 };
const btn: React.CSSProperties = { padding: "8px 16px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 };
const btnDanger: React.CSSProperties = { ...btn, background: "#da3633" };
const btnSecondary: React.CSSProperties = { ...btn, background: "var(--bg-secondary)", border: "1px solid var(--border)", color: "var(--text-primary)" };
const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 13 };
const td: React.CSSProperties = { padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 14 };
const presetBadge: React.CSSProperties = {
  display: "inline-block",
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  padding: "2px 8px",
  borderRadius: 4,
  color: "#3B82F6",
  background: "rgba(59,130,246,0.12)",
  border: "1px solid rgba(59,130,246,0.4)",
};
