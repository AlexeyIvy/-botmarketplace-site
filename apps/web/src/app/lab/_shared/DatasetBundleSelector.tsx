"use client";

/**
 * Multi-interval dataset bundle selector (docs/52-T5).
 *
 * Lets a user opt in to multi-TF backtests on top of an already-selected
 * "primary" dataset. The primary's interval is fixed (driven by the parent
 * dataset select); extra timeframes are added via the "+ Add timeframe"
 * button — up to {@link MAX_EXTRA_TFS} additional TFs (so the bundle never
 * exceeds 4 intervals total, matching the api-side cap).
 *
 * The component owns no state of its own — `bundle` and `onChange` are the
 * single source of truth so the parent can persist the bundle alongside
 * the form's other fields.
 *
 * Contract:
 *   - When `bundle === null`, the picker is collapsed; clicking
 *     "+ Add timeframe" creates the first bundle entry, automatically
 *     including the primary as `{ [primaryInterval]: primaryDatasetId }`.
 *   - When the user removes the last extra TF, `onChange(null)` is called
 *     so the parent reverts to the legacy single-TF code path.
 *   - For each requested interval, the selector lists every dataset whose
 *     `(symbol, interval)` matches and is `READY`; intervals with no
 *     matching dataset are still listed but disabled with a hint
 *     ("No dataset available — sync data first.").
 */

import { useMemo } from "react";

// ---------------------------------------------------------------------------
// Types — duplicated locally to avoid forcing every panel to import api types
// ---------------------------------------------------------------------------

export type CandleInterval = "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1";

export type DatasetBundle = Partial<Record<CandleInterval, string>>;

/** Subset of the datasets list shape the lab panels already pass around. */
export interface BundleDatasetItem {
  datasetId: string;
  name: string | null;
  symbol: string;
  interval: string;
  status: "READY" | "PARTIAL" | "FAILED";
}

export const ALL_INTERVALS: CandleInterval[] = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"];
export const MAX_EXTRA_TFS = 3; // primary + 3 extras = 4 total, matches api cap

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface DatasetBundleSelectorProps {
  primaryInterval: CandleInterval;
  primaryDatasetId: string;
  primarySymbol: string;
  availableDatasets: BundleDatasetItem[];
  bundle: DatasetBundle | null;
  onChange: (bundle: DatasetBundle | null) => void;
  disabled?: boolean;
}

export function DatasetBundleSelector(props: DatasetBundleSelectorProps) {
  const {
    primaryInterval,
    primaryDatasetId,
    primarySymbol,
    availableDatasets,
    bundle,
    onChange,
    disabled = false,
  } = props;

  // Datasets matching the primary symbol — we only ever pair intervals on the
  // same symbol so it is safe to filter once at the top level.
  const symbolDatasets = useMemo(
    () => availableDatasets.filter((d) => d.symbol === primarySymbol && d.status !== "FAILED"),
    [availableDatasets, primarySymbol],
  );

  /** Intervals (other than primary) for which at least one ready dataset exists. */
  const intervalAvailability = useMemo(() => {
    const out: Record<CandleInterval, boolean> = {
      M1: false, M5: false, M15: false, M30: false, H1: false, H4: false, D1: false,
    };
    for (const d of symbolDatasets) {
      if ((ALL_INTERVALS as string[]).includes(d.interval)) {
        out[d.interval as CandleInterval] = true;
      }
    }
    return out;
  }, [symbolDatasets]);

  const extras = useMemo(() => {
    if (!bundle) return [];
    return (Object.keys(bundle) as CandleInterval[])
      .filter((tf) => tf !== primaryInterval)
      .map((tf) => ({ interval: tf, datasetId: bundle[tf] as string }));
  }, [bundle, primaryInterval]);

  const remainingSlots = MAX_EXTRA_TFS - extras.length;
  const canAdd = !disabled && remainingSlots > 0;

  function withPrimary(extraEntries: Array<{ interval: CandleInterval; datasetId: string }>): DatasetBundle | null {
    if (extraEntries.length === 0) return null;
    const out: DatasetBundle = { [primaryInterval]: primaryDatasetId };
    for (const e of extraEntries) {
      out[e.interval] = e.datasetId;
    }
    return out;
  }

  function chooseFirstAvailableInterval(): CandleInterval | null {
    const used = new Set<CandleInterval>([primaryInterval, ...extras.map((e) => e.interval)]);
    for (const tf of ALL_INTERVALS) {
      if (!used.has(tf) && intervalAvailability[tf]) return tf;
    }
    // No interval has data — fall back to the first unused one and let the
    // user see the "no dataset" hint.
    for (const tf of ALL_INTERVALS) {
      if (!used.has(tf)) return tf;
    }
    return null;
  }

  function handleAdd() {
    const tf = chooseFirstAvailableInterval();
    if (!tf) return;
    const firstDataset = symbolDatasets.find((d) => d.interval === tf && d.status === "READY");
    const next = [...extras, { interval: tf, datasetId: firstDataset?.datasetId ?? "" }];
    onChange(withPrimary(next));
  }

  function handleRemove(idx: number) {
    const next = extras.filter((_, i) => i !== idx);
    onChange(withPrimary(next));
  }

  function handleIntervalChange(idx: number, nextInterval: CandleInterval) {
    const firstDataset = symbolDatasets.find((d) => d.interval === nextInterval && d.status === "READY");
    const updated = extras.map((row, i) => (i === idx
      ? { interval: nextInterval, datasetId: firstDataset?.datasetId ?? "" }
      : row));
    onChange(withPrimary(updated));
  }

  function handleDatasetChange(idx: number, nextDatasetId: string) {
    const updated = extras.map((row, i) => (i === idx ? { ...row, datasetId: nextDatasetId } : row));
    onChange(withPrimary(updated));
  }

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <span style={titleStyle}>Multi-interval bundle</span>
        <span style={primaryBadgeStyle}>
          primary: {primaryInterval}
        </span>
      </div>

      {extras.length === 0 ? (
        <p style={hintStyle}>
          Single timeframe — using only the primary dataset above. Add another
          timeframe to give DSL indicators with{" "}
          <code style={codeStyle}>sourceTimeframe</code> access to higher-TF
          context.
        </p>
      ) : (
        <ul style={listStyle}>
          {extras.map((row, idx) => (
            <ExtraRow
              key={idx}
              row={row}
              idx={idx}
              extrasUsed={extras.map((e) => e.interval)}
              primaryInterval={primaryInterval}
              symbolDatasets={symbolDatasets}
              intervalAvailability={intervalAvailability}
              onRemove={handleRemove}
              onIntervalChange={handleIntervalChange}
              onDatasetChange={handleDatasetChange}
              disabled={disabled}
            />
          ))}
        </ul>
      )}

      <button
        type="button"
        onClick={handleAdd}
        disabled={!canAdd}
        style={addButtonStyle(canAdd)}
      >
        + Add timeframe ({remainingSlots} left)
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component — one extra-TF row
// ---------------------------------------------------------------------------

function ExtraRow({
  row,
  idx,
  extrasUsed,
  primaryInterval,
  symbolDatasets,
  intervalAvailability,
  onRemove,
  onIntervalChange,
  onDatasetChange,
  disabled,
}: {
  row: { interval: CandleInterval; datasetId: string };
  idx: number;
  extrasUsed: CandleInterval[];
  primaryInterval: CandleInterval;
  symbolDatasets: BundleDatasetItem[];
  intervalAvailability: Record<CandleInterval, boolean>;
  onRemove: (idx: number) => void;
  onIntervalChange: (idx: number, tf: CandleInterval) => void;
  onDatasetChange: (idx: number, datasetId: string) => void;
  disabled: boolean;
}) {
  const datasetsForInterval = symbolDatasets.filter(
    (d) => d.interval === row.interval && d.status === "READY",
  );
  const intervalIsAvailable = intervalAvailability[row.interval];
  const usedSet = new Set<CandleInterval>([primaryInterval, ...extrasUsed.filter((tf, i) => i !== idx)]);

  return (
    <li style={rowStyle}>
      <select
        value={row.interval}
        onChange={(e) => onIntervalChange(idx, e.target.value as CandleInterval)}
        disabled={disabled}
        style={smallSelectStyle}
        aria-label={`Bundle interval ${idx + 1}`}
      >
        {ALL_INTERVALS.map((tf) => (
          <option key={tf} value={tf} disabled={usedSet.has(tf)}>
            {tf}{!intervalAvailability[tf] ? " — no data" : ""}
          </option>
        ))}
      </select>

      {intervalIsAvailable ? (
        <select
          value={row.datasetId}
          onChange={(e) => onDatasetChange(idx, e.target.value)}
          disabled={disabled}
          style={smallSelectStyle}
          aria-label={`Bundle dataset ${idx + 1}`}
        >
          {datasetsForInterval.map((d) => (
            <option key={d.datasetId} value={d.datasetId}>
              {d.name ?? `${d.symbol} · ${d.interval}`}
            </option>
          ))}
        </select>
      ) : (
        <span style={emptyHintStyle}>
          No dataset for {row.interval}. Sync data first.
        </span>
      )}

      <button
        type="button"
        onClick={() => onRemove(idx)}
        disabled={disabled}
        style={removeButtonStyle}
        aria-label="Remove timeframe"
      >
        ×
      </button>
    </li>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.02)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  padding: "10px 12px",
  display: "flex",
  flexDirection: "column",
  gap: 8,
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const titleStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: "var(--text-primary)",
};

const primaryBadgeStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 600,
  color: "rgba(255,255,255,0.55)",
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.18)",
  borderRadius: 3,
  padding: "1px 6px",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
};

const hintStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 11,
  color: "var(--text-secondary)",
  lineHeight: 1.5,
};

const codeStyle: React.CSSProperties = {
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  fontSize: 11,
  background: "rgba(255,255,255,0.06)",
  padding: "0 4px",
  borderRadius: 2,
};

const listStyle: React.CSSProperties = {
  listStyle: "none",
  margin: 0,
  padding: 0,
  display: "flex",
  flexDirection: "column",
  gap: 6,
};

const rowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
};

const smallSelectStyle: React.CSSProperties = {
  padding: "4px 8px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 4,
  color: "var(--text-primary)",
  fontSize: 12,
  fontFamily: "inherit",
  flex: 1,
  minWidth: 0,
};

const emptyHintStyle: React.CSSProperties = {
  flex: 1,
  fontSize: 11,
  color: "#fbbf24",
  fontStyle: "italic",
};

const removeButtonStyle: React.CSSProperties = {
  width: 22,
  height: 22,
  border: "none",
  background: "transparent",
  color: "rgba(255,255,255,0.45)",
  fontSize: 16,
  lineHeight: 1,
  cursor: "pointer",
  borderRadius: 3,
};

const addButtonStyle = (enabled: boolean): React.CSSProperties => ({
  alignSelf: "flex-start",
  padding: "4px 10px",
  fontSize: 11,
  fontWeight: 500,
  background: enabled ? "rgba(59,130,246,0.12)" : "transparent",
  color: enabled ? "#3B82F6" : "rgba(255,255,255,0.25)",
  border: `1px solid ${enabled ? "rgba(59,130,246,0.3)" : "var(--border)"}`,
  borderRadius: 4,
  cursor: enabled ? "pointer" : "not-allowed",
  fontFamily: "inherit",
});
