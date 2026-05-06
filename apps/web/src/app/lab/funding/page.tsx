"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  scanFundingCandidates,
  type FundingCandidate,
  type ScannerOptions,
} from "../../../lib/api/funding";
import { getToken, getWorkspaceId, type ProblemDetails } from "../../../lib/api";
import { CandidatesTable } from "./CandidatesTable";

/**
 * Lab → Funding scanner page (docs/55-T3 §UI).
 *
 * Lists ranked funding-arb candidates returned by the API scanner with
 * filter inputs (min yield, max basis, min streak, top-N). Each row
 * carries an "Open hedge bot" action that instantiates the funding-arb
 * preset with the row's symbol.
 *
 * Page-level concerns (auth, workspace, top-of-page error / empty state,
 * filter form, scan trigger) live here. Per-row sort + action live in
 * `CandidatesTable.tsx` to keep the file sizes manageable.
 */

const DEFAULT_OPTS: ScannerOptions = {
  minYield: 5,
  maxBasis: 50,
  minStreak: 3,
  limit: 20,
};

export default function LabFundingPage() {
  const router = useRouter();

  const [opts, setOpts] = useState<ScannerOptions>(DEFAULT_OPTS);
  const [candidates, setCandidates] = useState<FundingCandidate[] | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<ProblemDetails | null>(null);

  // workspaceId is read from localStorage which is undefined on the server.
  // Reading it at render time produces SSR HTML with the "no workspace"
  // warning visible, then the client may have a workspaceId and not render
  // the warning → React error #418 hydration mismatch. Defer the read into
  // a mount-time effect so the first client render matches the SSR pass,
  // and gate the warning on `mounted` so it never flickers for users who
  // do have a workspace set.
  const [mounted, setMounted] = useState(false);
  const [workspaceId, setWorkspaceIdState] = useState<string | null>(null);
  useEffect(() => {
    setWorkspaceIdState(getWorkspaceId());
    setMounted(true);
  }, []);

  const runScan = useCallback(async () => {
    setScanning(true);
    setError(null);
    const res = await scanFundingCandidates(opts);
    setScanning(false);
    if (!res.ok) {
      setError(res.problem);
      return;
    }
    setCandidates(res.data.candidates);
    setUpdatedAt(res.data.updatedAt);
  }, [opts]);

  // Auth gate + initial scan in a single guarded effect. Splitting these
  // into sibling effects causes the scan request to fire before the
  // redirect lands (React runs both effects in the same commit), so an
  // unauthenticated visitor briefly sees a 401 error flash before the
  // redirect. Same posture as /exchanges/page.tsx.
  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    void runScan();
    // Run only on mount. runScan closes over the initial `opts` (DEFAULT_OPTS)
    // which is what we want for the first auto-scan; subsequent scans are
    // explicit via the button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <div>
          <h1 style={titleStyle}>Funding Scanner</h1>
          <p style={subtitleStyle}>
            Ranked funding-arbitrage candidates from the last 7 days. Click
            a column header to sort. Use{" "}
            <strong style={{ color: "#F59E0B" }}>Open hedge bot</strong> to
            spin up a funding-arb bot on that symbol.
          </p>
        </div>
        <div style={updatedStyle}>
          {updatedAt ? (
            <>
              <span style={{ color: "var(--text-secondary)" }}>Last scan:</span>{" "}
              {new Date(updatedAt).toLocaleTimeString()}
            </>
          ) : (
            <span style={{ color: "var(--text-secondary)" }}>Not scanned yet</span>
          )}
        </div>
      </header>

      {mounted && !workspaceId && (
        <div style={warnBoxStyle}>
          No active workspace. Set one on the Factory page before opening a
          hedge bot — instantiation will otherwise fail.
        </div>
      )}

      <FilterBar
        opts={opts}
        scanning={scanning}
        onChange={setOpts}
        onScan={runScan}
      />

      {error && (
        <div style={errorBoxStyle}>
          <strong>{error.title}:</strong> {error.detail}
        </div>
      )}

      {scanning && candidates === null && (
        <p style={emptyStyle}>Scanning…</p>
      )}

      {!scanning && candidates !== null && candidates.length === 0 && (
        <div style={emptyBoxStyle}>
          <p style={{ margin: 0, fontSize: 14, color: "var(--text-primary)" }}>
            No candidates match the current filters.
          </p>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: "var(--text-secondary)" }}>
            Try lowering Min yield or relaxing Max basis. The scanner reads
            from the last 7 days of funding snapshots — make sure the data
            cron has run recently.
          </p>
        </div>
      )}

      {candidates !== null && candidates.length > 0 && (
        <CandidatesTable candidates={candidates} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Filter bar
// ---------------------------------------------------------------------------

function FilterBar({
  opts,
  scanning,
  onChange,
  onScan,
}: {
  opts: ScannerOptions;
  scanning: boolean;
  onChange: (next: ScannerOptions) => void;
  onScan: () => void;
}) {
  function setField<K extends keyof ScannerOptions>(key: K, raw: string) {
    const n = Number(raw);
    onChange({ ...opts, [key]: Number.isFinite(n) ? n : undefined });
  }

  return (
    <form
      style={filterRowStyle}
      onSubmit={(e) => {
        e.preventDefault();
        if (!scanning) onScan();
      }}
    >
      <Field label="Min yield (%)" hint="Default 5">
        <input
          type="number"
          inputMode="decimal"
          step="0.5"
          min={0}
          value={opts.minYield ?? ""}
          onChange={(e) => setField("minYield", e.target.value)}
          style={filterInputStyle}
        />
      </Field>
      <Field label="Max basis (bps)" hint="Default 50">
        <input
          type="number"
          inputMode="decimal"
          step="1"
          min={0}
          value={opts.maxBasis ?? ""}
          onChange={(e) => setField("maxBasis", e.target.value)}
          style={filterInputStyle}
        />
      </Field>
      <Field label="Min streak" hint="Default 3">
        <input
          type="number"
          inputMode="numeric"
          step="1"
          min={1}
          value={opts.minStreak ?? ""}
          onChange={(e) => setField("minStreak", e.target.value)}
          style={filterInputStyle}
        />
      </Field>
      <Field label="Top N" hint="Default 20">
        <input
          type="number"
          inputMode="numeric"
          step="1"
          min={1}
          max={50}
          value={opts.limit ?? ""}
          onChange={(e) => setField("limit", e.target.value)}
          style={filterInputStyle}
        />
      </Field>
      <button type="submit" disabled={scanning} style={scanBtnStyle}>
        {scanning ? "Scanning…" : "Scan now"}
      </button>
    </form>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label style={fieldLabelStyle}>
      <span style={fieldLabelTextStyle}>
        {label}
        {hint && <span style={fieldHintStyle}> · {hint}</span>}
      </span>
      {children}
    </label>
  );
}

// ---------------------------------------------------------------------------
// Styles — mirror lab/library/page.tsx (CSS variables, inline objects).
// ---------------------------------------------------------------------------

const pageStyle: React.CSSProperties = {
  padding: "32px 24px 64px",
  maxWidth: 1200,
  margin: "0 auto",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 16,
  marginBottom: 20,
  flexWrap: "wrap",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 22,
  fontWeight: 600,
  color: "var(--text-primary)",
};

const subtitleStyle: React.CSSProperties = {
  margin: "4px 0 0",
  color: "var(--text-secondary)",
  fontSize: 13,
  maxWidth: 720,
  lineHeight: 1.5,
};

const updatedStyle: React.CSSProperties = {
  fontSize: 12,
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  color: "var(--text-primary)",
};

const filterRowStyle: React.CSSProperties = {
  display: "flex",
  gap: 12,
  marginBottom: 16,
  flexWrap: "wrap",
  alignItems: "flex-end",
};

const fieldLabelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
};

const fieldLabelTextStyle: React.CSSProperties = {
  fontSize: 11,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  color: "var(--text-secondary)",
};

const fieldHintStyle: React.CSSProperties = {
  textTransform: "none",
  letterSpacing: "0",
  color: "rgba(255,255,255,0.35)",
};

const filterInputStyle: React.CSSProperties = {
  padding: "6px 10px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 4,
  color: "var(--text-primary)",
  fontSize: 13,
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  width: 110,
};

const scanBtnStyle: React.CSSProperties = {
  padding: "8px 18px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  fontFamily: "inherit",
};

const emptyStyle: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 14,
};

const emptyBoxStyle: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: 24,
  textAlign: "center",
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,113,113,0.08)",
  border: "1px solid rgba(248,113,113,0.4)",
  borderRadius: 6,
  padding: "8px 12px",
  marginBottom: 16,
  fontSize: 13,
  color: "#fca5a5",
};

const warnBoxStyle: React.CSSProperties = {
  background: "rgba(251,191,36,0.08)",
  border: "1px solid rgba(251,191,36,0.4)",
  borderRadius: 6,
  padding: "8px 12px",
  marginBottom: 16,
  fontSize: 13,
  color: "#fbbf24",
};
