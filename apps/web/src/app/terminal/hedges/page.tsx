"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken, clearAuth } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LegExecution {
  id: string;
  side: string;
  price: number;
  quantity: number;
  fee: number;
  timestamp: string;
}

interface HedgePosition {
  id: string;
  botRunId: string;
  symbol: string;
  status: string;
  entryBasisBps: number;
  fundingCollected: number;
  createdAt: string;
  closedAt: string | null;
  legs: LegExecution[];
  pnl: number | null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function HedgeDashboardPage() {
  const router = useRouter();

  const [botRunId, setBotRunId] = useState("");
  const [hedges, setHedges] = useState<HedgePosition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  // Exit modal
  const [exitTarget, setExitTarget] = useState<HedgePosition | null>(null);
  const [exitSubmitting, setExitSubmitting] = useState(false);
  const [exitResult, setExitResult] = useState<{ ok: boolean; message: string } | null>(null);

  const fetchHedges = useCallback(async () => {
    if (!botRunId.trim()) return;
    setLoading(true);
    setError(null);

    const res = await apiFetch<HedgePosition[]>(
      `/hedges?botRunId=${encodeURIComponent(botRunId.trim())}`,
    );

    setLoading(false);

    if (res.ok) {
      setHedges(res.data);
    } else if (res.problem.status === 401) {
      setSessionExpired(true);
      clearAuth();
    } else {
      setError(res.problem.detail);
    }
  }, [botRunId]);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
    }
  }, [router]);

  // ---------------------------------------------------------------------------
  // Exit handlers
  // ---------------------------------------------------------------------------

  function openExitModal(hedge: HedgePosition) {
    setExitTarget(hedge);
    setExitResult(null);
    setExitSubmitting(false);
  }

  function closeExitModal() {
    setExitTarget(null);
    setExitResult(null);
  }

  async function handleExit() {
    if (!exitTarget) return;
    setExitSubmitting(true);
    setExitResult(null);

    const res = await apiFetch<{ hedgeId: string; status: string }>(
      `/hedges/${exitTarget.id}/exit`,
      { method: "POST", body: JSON.stringify({}) },
    );

    setExitSubmitting(false);

    if (res.ok) {
      setExitResult({ ok: true, message: `Exit initiated. Status: ${res.data.status}` });
      // Refresh list
      fetchHedges();
    } else {
      setExitResult({ ok: false, message: res.problem.detail });
    }
  }

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  function statusColor(status: string): string {
    switch (status) {
      case "OPEN": return "#3fb950";
      case "OPENING":
      case "CLOSING": return "#d29922";
      case "CLOSED": return "var(--text-secondary)";
      case "FAILED": return "#f85149";
      default: return "var(--text-primary)";
    }
  }

  function formatPnl(pnl: number | null): string {
    if (pnl === null) return "-";
    const sign = pnl >= 0 ? "+" : "";
    return `${sign}$${pnl.toFixed(2)}`;
  }

  function pnlColor(pnl: number | null): string {
    if (pnl === null) return "var(--text-secondary)";
    return pnl >= 0 ? "#3fb950" : "#f85149";
  }

  // ---------------------------------------------------------------------------
  // Session expired
  // ---------------------------------------------------------------------------

  if (sessionExpired) {
    return (
      <div style={wrap}>
        <div style={expiredBanner}>
          Session expired.{" "}
          <button onClick={() => router.push("/login")} style={linkBtn}>
            Log in
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Main render
  // ---------------------------------------------------------------------------

  return (
    <div style={wrap}>
      <h1 style={heading}>Hedge Dashboard</h1>
      <p style={subtitle}>
        Manage open funding arbitrage positions.{" "}
        <button
          onClick={() => router.push("/terminal/funding")}
          style={{ ...linkBtn, fontSize: 14 }}
        >
          Back to Scanner
        </button>
      </p>

      {/* Bot Run ID input */}
      <div style={filterRow}>
        <label style={filterLabel}>
          Bot Run ID
          <input
            type="text"
            value={botRunId}
            onChange={(e) => setBotRunId(e.target.value)}
            style={{ ...filterInput, width: 300 }}
            placeholder="Enter bot run ID to load hedges"
          />
        </label>
        <button
          onClick={fetchHedges}
          disabled={loading || !botRunId.trim()}
          style={{
            ...refreshBtn,
            opacity: !botRunId.trim() ? 0.6 : 1,
          }}
        >
          {loading ? "Loading..." : "Load"}
        </button>
      </div>

      {error && <p style={errorText}>{error}</p>}

      {!loading && hedges.length === 0 && botRunId.trim() && !error && (
        <p style={emptyText}>No hedge positions found for this run</p>
      )}

      {hedges.length > 0 && (
        <div style={tableWrap}>
          <table style={table}>
            <thead>
              <tr>
                <th style={th}>Symbol</th>
                <th style={th}>Status</th>
                <th style={thRight}>Entry Basis</th>
                <th style={thRight}>Funding Collected</th>
                <th style={thRight}>P&L</th>
                <th style={th}>Opened</th>
                <th style={{ ...th, textAlign: "center" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {hedges.map((h) => (
                <tr key={h.id} style={row}>
                  <td style={td}>{h.symbol}</td>
                  <td style={{ ...td, color: statusColor(h.status), fontWeight: 600 }}>
                    {h.status}
                  </td>
                  <td style={tdRight}>{h.entryBasisBps.toFixed(1)} bps</td>
                  <td style={tdRight}>${h.fundingCollected.toFixed(2)}</td>
                  <td style={{ ...tdRight, color: pnlColor(h.pnl), fontWeight: 600 }}>
                    {formatPnl(h.pnl)}
                  </td>
                  <td style={td}>{new Date(h.createdAt).toLocaleString()}</td>
                  <td style={{ ...td, textAlign: "center" }}>
                    {h.status === "OPEN" && (
                      <button onClick={() => openExitModal(h)} style={exitBtn}>
                        Exit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Exit Modal */}
      {exitTarget && (
        <div style={modalOverlay} onClick={closeExitModal}>
          <div style={modalContent} onClick={(e) => e.stopPropagation()}>
            <h2 style={modalTitle}>Exit Hedge: {exitTarget.symbol}</h2>

            <div style={modalInfoGrid}>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Status</span>
                <span style={{ ...modalInfoValue, color: statusColor(exitTarget.status) }}>
                  {exitTarget.status}
                </span>
              </div>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Entry Basis</span>
                <span style={modalInfoValue}>{exitTarget.entryBasisBps.toFixed(1)} bps</span>
              </div>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Funding Collected</span>
                <span style={modalInfoValue}>${exitTarget.fundingCollected.toFixed(2)}</span>
              </div>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Current P&L</span>
                <span style={{ ...modalInfoValue, color: pnlColor(exitTarget.pnl) }}>
                  {formatPnl(exitTarget.pnl)}
                </span>
              </div>
            </div>

            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
              This will place exit orders (spot sell + perp close) to unwind the position.
            </p>

            {exitResult && (
              <p style={{ ...(exitResult.ok ? successText : errorText), marginBottom: 12 }}>
                {exitResult.message}
              </p>
            )}

            <div style={modalActions}>
              <button onClick={closeExitModal} style={cancelBtn}>
                Cancel
              </button>
              <button
                onClick={handleExit}
                disabled={exitSubmitting}
                style={{
                  ...exitConfirmBtn,
                  opacity: exitSubmitting ? 0.6 : 1,
                }}
              >
                {exitSubmitting ? "Submitting..." : "Confirm Exit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const wrap: React.CSSProperties = {
  maxWidth: 1100,
  margin: "0 auto",
  padding: "48px 24px",
};

const heading: React.CSSProperties = {
  fontSize: 26,
  fontWeight: 700,
  marginBottom: 4,
  color: "var(--text-primary)",
};

const subtitle: React.CSSProperties = {
  fontSize: 14,
  color: "var(--text-secondary)",
  marginBottom: 24,
};

const filterRow: React.CSSProperties = {
  display: "flex",
  gap: 16,
  alignItems: "flex-end",
  flexWrap: "wrap",
  marginBottom: 20,
};

const filterLabel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  fontSize: 13,
  color: "var(--text-secondary)",
};

const filterInput: React.CSSProperties = {
  width: 90,
  padding: "6px 8px",
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "var(--bg-card)",
  color: "var(--text-primary)",
  fontSize: 14,
};

const refreshBtn: React.CSSProperties = {
  padding: "7px 16px",
  borderRadius: 6,
  border: "1px solid var(--accent)",
  background: "var(--accent)",
  color: "#fff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};

const errorText: React.CSSProperties = {
  color: "#f85149",
  fontSize: 14,
};

const successText: React.CSSProperties = {
  color: "#3fb950",
  fontSize: 14,
};

const emptyText: React.CSSProperties = {
  fontSize: 14,
  color: "var(--text-secondary)",
  textAlign: "center",
  padding: "40px 0",
};

const tableWrap: React.CSSProperties = {
  overflowX: "auto",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg-secondary)",
};

const table: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 14,
};

const th: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 12px",
  borderBottom: "1px solid var(--border)",
  color: "var(--text-secondary)",
  fontWeight: 600,
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  whiteSpace: "nowrap",
};

const thRight: React.CSSProperties = { ...th, textAlign: "right" };

const td: React.CSSProperties = {
  padding: "10px 12px",
  borderBottom: "1px solid var(--border)",
  color: "var(--text-primary)",
  whiteSpace: "nowrap",
};

const tdRight: React.CSSProperties = { ...td, textAlign: "right" };

const row: React.CSSProperties = {};

const exitBtn: React.CSSProperties = {
  padding: "4px 12px",
  borderRadius: 4,
  border: "1px solid #f85149",
  background: "transparent",
  color: "#f85149",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};

const expiredBanner: React.CSSProperties = {
  padding: 24,
  textAlign: "center",
  color: "var(--text-secondary)",
  fontSize: 16,
};

const linkBtn: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--accent)",
  cursor: "pointer",
  textDecoration: "underline",
  fontSize: 16,
};

// Modal styles

const modalOverlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0, 0, 0, 0.6)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const modalContent: React.CSSProperties = {
  background: "var(--bg-card, #1c1c1e)",
  borderRadius: 12,
  padding: "28px 32px",
  maxWidth: 440,
  width: "90%",
  border: "1px solid var(--border)",
};

const modalTitle: React.CSSProperties = {
  fontSize: 20,
  fontWeight: 700,
  color: "var(--text-primary)",
  marginBottom: 20,
};

const modalInfoGrid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 12,
  marginBottom: 20,
};

const modalInfoItem: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 2,
};

const modalInfoLabel: React.CSSProperties = {
  fontSize: 11,
  color: "var(--text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
};

const modalInfoValue: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 600,
  color: "var(--text-primary)",
};

const modalActions: React.CSSProperties = {
  display: "flex",
  gap: 12,
  justifyContent: "flex-end",
};

const cancelBtn: React.CSSProperties = {
  padding: "8px 20px",
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "transparent",
  color: "var(--text-secondary)",
  fontSize: 14,
  cursor: "pointer",
};

const exitConfirmBtn: React.CSSProperties = {
  padding: "8px 20px",
  borderRadius: 6,
  border: "1px solid #f85149",
  background: "#f85149",
  color: "#fff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};
