"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken, clearAuth } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FundingCandidate {
  symbol: string;
  currentRate: number;
  annualizedYieldPct: number;
  basisBps: number;
  streak: number;
  avgRate: number;
}

interface ScannerResponse {
  candidates: FundingCandidate[];
  updatedAt: string;
}

type SortKey = keyof Pick<FundingCandidate, "symbol" | "annualizedYieldPct" | "basisBps" | "streak" | "avgRate" | "currentRate">;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function FundingScannerPage() {
  const router = useRouter();

  // Filters
  const [minYield, setMinYield] = useState("5");
  const [maxBasis, setMaxBasis] = useState("50");
  const [minStreak, setMinStreak] = useState("3");

  // Data
  const [candidates, setCandidates] = useState<FundingCandidate[]>([]);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  // Sort
  const [sortKey, setSortKey] = useState<SortKey>("annualizedYieldPct");
  const [sortAsc, setSortAsc] = useState(false);

  // Hedge entry modal
  const [hedgeCandidate, setHedgeCandidate] = useState<FundingCandidate | null>(null);
  const [hedgeSize, setHedgeSize] = useState("1000");
  const [hedgeBotRunId, setHedgeBotRunId] = useState("");
  const [hedgeSubmitting, setHedgeSubmitting] = useState(false);
  const [hedgeResult, setHedgeResult] = useState<{ ok: boolean; message: string } | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams({
      minYield,
      maxBasis,
      minStreak,
      limit: "50",
    });

    const res = await apiFetch<ScannerResponse>(
      `/terminal/funding/scanner?${params}`,
    );

    setLoading(false);

    if (res.ok) {
      setCandidates(res.data.candidates);
      setUpdatedAt(res.data.updatedAt);
    } else if (res.problem.status === 401) {
      setSessionExpired(true);
      clearAuth();
    } else {
      setError(res.problem.detail);
    }
  }, [minYield, maxBasis, minStreak]);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    fetchData();
  }, [router, fetchData]);

  // Sort logic
  const sorted = [...candidates].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "string" && typeof bv === "string") {
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Hedge entry handlers
  // ---------------------------------------------------------------------------

  function openHedgeModal(candidate: FundingCandidate) {
    setHedgeCandidate(candidate);
    setHedgeResult(null);
    setHedgeSubmitting(false);
  }

  function closeHedgeModal() {
    setHedgeCandidate(null);
    setHedgeResult(null);
  }

  async function handleHedgeEntry() {
    if (!hedgeCandidate || !hedgeBotRunId.trim()) return;

    setHedgeSubmitting(true);
    setHedgeResult(null);

    // Step 1: Create hedge position (PLANNED)
    const entryRes = await apiFetch<{ id: string; symbol: string; status: string }>(
      "/hedges/entry",
      {
        method: "POST",
        body: JSON.stringify({
          symbol: hedgeCandidate.symbol,
          botRunId: hedgeBotRunId.trim(),
          positionSizeUsd: parseFloat(hedgeSize),
          entryBasisBps: hedgeCandidate.basisBps,
        }),
      },
    );

    if (!entryRes.ok) {
      setHedgeSubmitting(false);
      setHedgeResult({ ok: false, message: entryRes.problem.detail });
      return;
    }

    // Step 2: Execute entry (spot buy + perp short)
    const hedgeId = entryRes.data.id;
    const sizeUsd = parseFloat(hedgeSize);
    // Estimate quantity: positionSize / spotPrice approximation
    // For now, pass the USD size as qty placeholder — the botWorker will normalize
    const quantity = hedgeCandidate.currentRate !== 0 ? sizeUsd / 100 : sizeUsd;

    const execRes = await apiFetch<{ hedgeId: string; status: string }>(
      `/hedges/${hedgeId}/execute`,
      {
        method: "POST",
        body: JSON.stringify({ quantity }),
      },
    );

    setHedgeSubmitting(false);

    if (execRes.ok) {
      setHedgeResult({
        ok: true,
        message: `Hedge ${hedgeCandidate.symbol} opened. Status: ${execRes.data.status}`,
      });
    } else {
      setHedgeResult({ ok: false, message: execRes.problem.detail });
    }
  }

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  function yieldColor(yieldPct: number): string {
    const abs = Math.abs(yieldPct);
    if (abs > 20) return "#3fb950";   // green
    if (abs > 10) return "#d29922";   // yellow
    return "var(--text-secondary)";    // grey
  }

  function formatRate(rate: number): string {
    return (rate * 100).toFixed(4) + "%";
  }

  function formatYield(yieldPct: number): string {
    return yieldPct.toFixed(2) + "%";
  }

  function formatBasis(bps: number): string {
    return bps.toFixed(1) + " bps";
  }

  function sortIndicator(key: SortKey): string {
    if (sortKey !== key) return "";
    return sortAsc ? " \u25B2" : " \u25BC";
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
      <h1 style={heading}>Funding Scanner</h1>
      <p style={subtitle}>
        Ranked funding arbitrage candidates from the last 7 days of data.
        {" "}
        <button
          onClick={() => router.push("/terminal/hedges")}
          style={{ ...linkBtn, fontSize: 14 }}
        >
          View Hedge Dashboard
        </button>
      </p>

      {/* Filters */}
      <div style={filterRow}>
        <label style={filterLabel}>
          Min Yield %
          <input
            type="number"
            value={minYield}
            onChange={(e) => setMinYield(e.target.value)}
            style={filterInput}
            min="0"
            step="1"
          />
        </label>
        <label style={filterLabel}>
          Max Basis (bps)
          <input
            type="number"
            value={maxBasis}
            onChange={(e) => setMaxBasis(e.target.value)}
            style={filterInput}
            min="0"
            step="5"
          />
        </label>
        <label style={filterLabel}>
          Min Streak
          <input
            type="number"
            value={minStreak}
            onChange={(e) => setMinStreak(e.target.value)}
            style={filterInput}
            min="0"
            step="1"
          />
        </label>
        <button onClick={fetchData} disabled={loading} style={refreshBtn}>
          {loading ? "Loading\u2026" : "Refresh"}
        </button>
      </div>

      {/* Error */}
      {error && <p style={errorText}>{error}</p>}

      {/* Updated at */}
      {updatedAt && (
        <p style={updatedText}>
          Last updated: {new Date(updatedAt).toLocaleString()}
        </p>
      )}

      {/* Table */}
      {!loading && candidates.length === 0 && !error && (
        <p style={emptyText}>No candidates match filters</p>
      )}

      {candidates.length > 0 && (
        <div style={tableWrap}>
          <table style={table}>
            <thead>
              <tr>
                <th style={th} onClick={() => handleSort("symbol")}>
                  Symbol{sortIndicator("symbol")}
                </th>
                <th style={thRight} onClick={() => handleSort("annualizedYieldPct")}>
                  Yield %{sortIndicator("annualizedYieldPct")}
                </th>
                <th style={thRight} onClick={() => handleSort("basisBps")}>
                  Basis{sortIndicator("basisBps")}
                </th>
                <th style={thRight} onClick={() => handleSort("streak")}>
                  Streak{sortIndicator("streak")}
                </th>
                <th style={thRight} onClick={() => handleSort("avgRate")}>
                  Avg Rate{sortIndicator("avgRate")}
                </th>
                <th style={thRight} onClick={() => handleSort("currentRate")}>
                  Current Rate{sortIndicator("currentRate")}
                </th>
                <th style={{ ...th, textAlign: "center" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((c) => (
                <tr key={c.symbol} style={row}>
                  <td style={td}>{c.symbol}</td>
                  <td style={{ ...tdRight, color: yieldColor(c.annualizedYieldPct), fontWeight: 600 }}>
                    {formatYield(c.annualizedYieldPct)}
                  </td>
                  <td style={tdRight}>{formatBasis(c.basisBps)}</td>
                  <td style={tdRight}>{c.streak}</td>
                  <td style={tdRight}>{formatRate(c.avgRate)}</td>
                  <td style={tdRight}>{formatRate(c.currentRate)}</td>
                  <td style={{ ...td, textAlign: "center" }}>
                    <button
                      onClick={() => openHedgeModal(c)}
                      style={hedgeBtn}
                    >
                      Hedge
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Hedge Entry Modal */}
      {hedgeCandidate && (
        <div style={modalOverlay} onClick={closeHedgeModal}>
          <div style={modalContent} onClick={(e) => e.stopPropagation()}>
            <h2 style={modalTitle}>Open Hedge: {hedgeCandidate.symbol}</h2>

            <div style={modalInfoGrid}>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Yield</span>
                <span style={{ ...modalInfoValue, color: yieldColor(hedgeCandidate.annualizedYieldPct) }}>
                  {formatYield(hedgeCandidate.annualizedYieldPct)}
                </span>
              </div>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Basis</span>
                <span style={modalInfoValue}>{formatBasis(hedgeCandidate.basisBps)}</span>
              </div>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Streak</span>
                <span style={modalInfoValue}>{hedgeCandidate.streak}</span>
              </div>
              <div style={modalInfoItem}>
                <span style={modalInfoLabel}>Current Rate</span>
                <span style={modalInfoValue}>{formatRate(hedgeCandidate.currentRate)}</span>
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={filterLabel}>
                Position Size (USD)
                <input
                  type="number"
                  value={hedgeSize}
                  onChange={(e) => setHedgeSize(e.target.value)}
                  style={{ ...filterInput, width: "100%" }}
                  min="10"
                  step="100"
                />
              </label>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={filterLabel}>
                Bot Run ID
                <input
                  type="text"
                  value={hedgeBotRunId}
                  onChange={(e) => setHedgeBotRunId(e.target.value)}
                  style={{ ...filterInput, width: "100%" }}
                  placeholder="Enter active bot run ID"
                />
              </label>
            </div>

            {hedgeResult && (
              <p style={{ ...hedgeResult.ok ? successText : errorText, marginBottom: 12 }}>
                {hedgeResult.message}
              </p>
            )}

            <div style={modalActions}>
              <button onClick={closeHedgeModal} style={cancelBtn}>
                Cancel
              </button>
              <button
                onClick={handleHedgeEntry}
                disabled={hedgeSubmitting || !hedgeBotRunId.trim() || !hedgeSize}
                style={{
                  ...confirmBtn,
                  opacity: hedgeSubmitting || !hedgeBotRunId.trim() ? 0.6 : 1,
                }}
              >
                {hedgeSubmitting ? "Submitting..." : "Confirm Entry"}
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
  marginBottom: 12,
};

const successText: React.CSSProperties = {
  color: "#3fb950",
  fontSize: 14,
  marginBottom: 12,
};

const updatedText: React.CSSProperties = {
  fontSize: 12,
  color: "var(--text-secondary)",
  marginBottom: 12,
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
  cursor: "pointer",
  userSelect: "none",
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

const hedgeBtn: React.CSSProperties = {
  padding: "4px 12px",
  borderRadius: 4,
  border: "1px solid var(--accent)",
  background: "transparent",
  color: "var(--accent)",
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

const confirmBtn: React.CSSProperties = {
  padding: "8px 20px",
  borderRadius: 6,
  border: "1px solid var(--accent)",
  background: "var(--accent)",
  color: "#fff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};
