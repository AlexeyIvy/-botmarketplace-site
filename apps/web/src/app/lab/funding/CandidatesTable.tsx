"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  instantiatePreset,
  type InstantiateOverrides,
} from "../../../lib/api/presets";
import type { FundingCandidate } from "../../../lib/api/funding";
import type { ProblemDetails } from "../../../lib/api";

/**
 * Sortable funding candidates table (docs/55-T3 §UI).
 *
 * One row per candidate. Click any column header to sort; clicking the
 * same column twice toggles asc/desc. The default sort is
 * `annualizedYieldPct DESC` — the operator's "best opportunity" view.
 *
 * The "Open hedge bot" action instantiates the funding-arb preset with
 * just the `symbol` overridden — every other field falls through to the
 * preset's `defaultBotConfigJson` (BTCUSDT defaults). The current row's
 * symbol replaces it. Successful instantiation routes to the new bot's
 * factory page.
 *
 * Beta-state caveat: the funding-arb preset is published with
 * `visibility = "BETA"` (PR #366), so non-admin operators can already
 * use it from the library — the action button here is just a shortcut
 * out of the scanner table.
 */

type SortKey = keyof Pick<
  FundingCandidate,
  "symbol" | "currentRate" | "annualizedYieldPct" | "basisBps" | "streak"
> | "nextFundingAt";

type SortDir = "asc" | "desc";

const FUNDING_ARB_SLUG = "funding-arb";

export function CandidatesTable({
  candidates,
}: {
  candidates: FundingCandidate[];
}) {
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("annualizedYieldPct");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ProblemDetails | string | null>(null);

  const sorted = useMemo(() => {
    const copy = [...candidates];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      // null `nextFundingAt` rows sink to the bottom regardless of dir.
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      const as = String(av);
      const bs = String(bv);
      return sortDir === "asc" ? as.localeCompare(bs) : bs.localeCompare(as);
    });
    return copy;
  }, [candidates, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      // First click on a new column picks the most-useful default
      // direction for that field — descending for numeric metrics
      // (higher yield first), ascending for symbol/time.
      setSortDir(key === "symbol" || key === "nextFundingAt" ? "asc" : "desc");
    }
  }

  async function handleOpenHedgeBot(symbol: string) {
    setError(null);
    setBusy(symbol);
    const overrides: InstantiateOverrides = { symbol };
    const res = await instantiatePreset(FUNDING_ARB_SLUG, { overrides });
    setBusy(null);
    if (!res.ok) {
      setError(res.problem);
      return;
    }
    router.push(`/factory/bots/${res.data.botId}`);
  }

  return (
    <div>
      {error && (
        <div style={errorBoxStyle}>
          {typeof error === "string" ? (
            error
          ) : (
            <>
              <strong>{error.title}:</strong> {error.detail}
            </>
          )}
        </div>
      )}
      <div style={tableScrollStyle}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <Th label="Symbol" sortKey="symbol" current={sortKey} dir={sortDir} onSort={toggleSort} />
              <Th label="Funding (8h)" sortKey="currentRate" current={sortKey} dir={sortDir} onSort={toggleSort} align="right" />
              <Th label="Annualized" sortKey="annualizedYieldPct" current={sortKey} dir={sortDir} onSort={toggleSort} align="right" />
              <Th label="Basis (bps)" sortKey="basisBps" current={sortKey} dir={sortDir} onSort={toggleSort} align="right" />
              <Th label="Streak" sortKey="streak" current={sortKey} dir={sortDir} onSort={toggleSort} align="right" />
              <Th label="Next funding" sortKey="nextFundingAt" current={sortKey} dir={sortDir} onSort={toggleSort} />
              <th style={thActionStyle}>Action</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((c) => (
              <tr key={c.symbol} style={trStyle}>
                <td style={tdSymbolStyle}>{c.symbol}</td>
                <td style={tdNumStyle}>{formatFundingRate(c.currentRate)}</td>
                <td style={tdNumStyle}>{formatPct(c.annualizedYieldPct)}</td>
                <td style={tdNumStyle}>{c.basisBps.toFixed(1)}</td>
                <td style={tdNumStyle}>{c.streak}</td>
                <td style={tdStyle}>{formatNextFunding(c.nextFundingAt)}</td>
                <td style={tdActionStyle}>
                  <button
                    type="button"
                    onClick={() => handleOpenHedgeBot(c.symbol)}
                    disabled={busy !== null}
                    style={busy === c.symbol ? actionBtnBusyStyle : actionBtnStyle}
                    title="Instantiate the funding-arb preset with this symbol"
                  >
                    {busy === c.symbol ? "Opening…" : "Open hedge bot"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({
  label,
  sortKey,
  current,
  dir,
  onSort,
  align,
}: {
  label: string;
  sortKey: SortKey;
  current: SortKey;
  dir: SortDir;
  onSort: (k: SortKey) => void;
  align?: "right";
}) {
  const active = current === sortKey;
  const indicator = active ? (dir === "asc" ? " ▲" : " ▼") : "";
  return (
    <th
      style={{
        ...thStyle,
        ...(align === "right" ? { textAlign: "right" } : null),
        ...(active ? { color: "var(--text-primary)" } : null),
      }}
    >
      <button type="button" onClick={() => onSort(sortKey)} style={thBtnStyle}>
        {label}
        {indicator}
      </button>
    </th>
  );
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

function formatFundingRate(rate: number): string {
  // Decimal → percent, 4 sig digits. 0.0001 → "0.0100%".
  return `${(rate * 100).toFixed(4)}%`;
}

function formatPct(pct: number): string {
  return `${pct.toFixed(2)}%`;
}

function formatNextFunding(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  // Shows in operator's local TZ. Format: "May 04 16:00".
  return d.toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Styles — match the lab/library page conventions (CSS vars, no Tailwind).
// ---------------------------------------------------------------------------

const tableScrollStyle: React.CSSProperties = {
  overflowX: "auto",
  border: "1px solid var(--border)",
  borderRadius: 6,
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 13,
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 12px",
  background: "var(--bg-secondary)",
  borderBottom: "1px solid var(--border)",
  color: "var(--text-secondary)",
  fontWeight: 600,
  whiteSpace: "nowrap",
};

const thActionStyle: React.CSSProperties = {
  ...thStyle,
  textAlign: "right",
};

const thBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "none",
  color: "inherit",
  font: "inherit",
  padding: 0,
  cursor: "pointer",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  fontSize: 11,
};

const trStyle: React.CSSProperties = {
  borderBottom: "1px solid var(--border)",
};

const tdStyle: React.CSSProperties = {
  padding: "10px 12px",
  color: "var(--text-primary)",
  whiteSpace: "nowrap",
};

const tdSymbolStyle: React.CSSProperties = {
  ...tdStyle,
  fontWeight: 600,
  fontFamily: "'SF Mono', 'Fira Code', monospace",
};

const tdNumStyle: React.CSSProperties = {
  ...tdStyle,
  textAlign: "right",
  fontFamily: "'SF Mono', 'Fira Code', monospace",
};

const tdActionStyle: React.CSSProperties = {
  padding: "8px 12px",
  textAlign: "right",
};

const actionBtnStyle: React.CSSProperties = {
  padding: "5px 10px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 4,
  cursor: "pointer",
  fontSize: 12,
  fontWeight: 600,
  fontFamily: "inherit",
};

const actionBtnBusyStyle: React.CSSProperties = {
  ...actionBtnStyle,
  background: "var(--bg-secondary)",
  color: "var(--text-secondary)",
  cursor: "wait",
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,113,113,0.08)",
  border: "1px solid rgba(248,113,113,0.4)",
  borderRadius: 6,
  padding: "8px 12px",
  marginBottom: 12,
  fontSize: 13,
  color: "#fca5a5",
};
