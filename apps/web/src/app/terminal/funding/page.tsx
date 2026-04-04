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
                </tr>
              ))}
            </tbody>
          </table>
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
