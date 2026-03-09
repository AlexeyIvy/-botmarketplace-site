"use client";

/**
 * /lab/data — Dataset Builder (Phase 2A)
 *
 * Implements §6.2 mandatory controls from the Lab v2 IDE spec:
 * exchange, environment, market type, symbol, data type, interval,
 * date range, timezone, optional name.
 *
 * Calls POST /api/v1/lab/datasets (synchronous, up to ~30s).
 * On success: updates useLabGraphStore.activeDatasetId.
 * Shows list of existing datasets from GET /api/v1/lab/datasets.
 */

import { useEffect, useState } from "react";
import { apiFetch, getWorkspaceId } from "../../../lib/api";
import { useLabGraphStore } from "../useLabGraphStore";
import { DatasetPreview } from "../DatasetPreview";

// ---------------------------------------------------------------------------
// DatasetDetail — response shape for GET /lab/datasets/:id (quality fields)
// ---------------------------------------------------------------------------

interface DatasetDetail {
  datasetId:     string;
  qualityJson:   unknown;
  engineVersion: string;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExchangeConnection {
  id: string;
  exchange: string;
  name: string;
  status: "UNKNOWN" | "CONNECTED" | "FAILED";
}

interface DatasetListItem {
  datasetId: string;
  exchange: string;
  symbol: string;
  interval: string;
  fromTsMs: string;
  toTsMs: string;
  candleCount: number;
  status: "READY" | "PARTIAL" | "FAILED";
  name: string | null;
  datasetHash: string;
  fetchedAt: string;
  createdAt: string;
}

interface CreateDatasetResult {
  datasetId: string;
  name: string | null;
  datasetHash: string;
  status: "READY" | "PARTIAL" | "FAILED";
  candleCount: number;
  fetchedAt: string;
  engineVersion: string;
  qualityJson: unknown;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVALS = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"] as const;
const MAX_RANGE_DAYS = 365;
const MAX_CANDLES = 100_000;

const INTERVAL_MS: Record<string, number> = {
  M1: 60_000, M5: 300_000, M15: 900_000, M30: 1_800_000,
  H1: 3_600_000, H4: 14_400_000, D1: 86_400_000,
};

const TIMEZONES = [
  "UTC",
  "Europe/London",
  "Europe/Moscow",
  "Asia/Dubai",
  "Asia/Tokyo",
  "America/New_York",
  "America/Chicago",
  "America/Los_Angeles",
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isoDate(ts: number): string {
  return new Date(ts).toISOString().slice(0, 10);
}

function formatDateShort(isoOrMs: string): string {
  return new Date(isoOrMs).toLocaleDateString("en-GB", {
    year: "numeric", month: "short", day: "2-digit",
  });
}

function estimateCandles(fromDate: string, toDate: string, interval: string): number {
  if (!fromDate || !toDate) return 0;
  const fromMs = new Date(fromDate).getTime();
  const toMs = new Date(toDate).getTime();
  if (!isFinite(fromMs) || !isFinite(toMs) || fromMs >= toMs) return 0;
  const ms = INTERVAL_MS[interval] ?? 0;
  if (!ms) return 0;
  return Math.ceil((toMs - fromMs) / ms);
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: "READY" | "PARTIAL" | "FAILED" }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    READY:   { bg: "rgba(63,185,80,0.15)",  fg: "#3fb950" },
    PARTIAL: { bg: "rgba(210,153,34,0.15)", fg: "#d29922" },
    FAILED:  { bg: "rgba(248,81,73,0.15)",  fg: "#f85149" },
  };
  const c = colors[status] ?? colors.FAILED;
  return (
    <span style={{
      background: c.bg, color: c.fg,
      padding: "2px 8px", borderRadius: 4,
      fontSize: 11, fontWeight: 600, letterSpacing: "0.03em",
    }}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Dataset list row
// ---------------------------------------------------------------------------

function DatasetRow({
  ds,
  isActive,
  onSelect,
}: {
  ds: DatasetListItem;
  isActive: boolean;
  onSelect: () => void;
}) {
  const from  = formatDateShort(new Date(Number(ds.fromTsMs)).toISOString());
  const to    = formatDateShort(new Date(Number(ds.toTsMs)).toISOString());
  const label = ds.name ?? `${ds.symbol} · ${ds.interval}`;

  return (
    <div
      onClick={onSelect}
      style={{
        padding: "10px 14px",
        borderBottom: "1px solid var(--border)",
        cursor: "pointer",
        background: isActive ? "rgba(88,166,255,0.08)" : "transparent",
        borderLeft: isActive ? "3px solid var(--accent, #58a6ff)" : "3px solid transparent",
        transition: "background 0.15s",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {label}
        </span>
        <StatusBadge status={ds.status} />
      </div>
      <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>
        {from} → {to} · {ds.candleCount.toLocaleString()} candles
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function LabDataPage() {
  const setActiveDatasetId = useLabGraphStore((s) => s.setActiveDatasetId);
  const activeDatasetId    = useLabGraphStore((s) => s.activeDatasetId);

  // Form state
  const [connections, setConnections]   = useState<ExchangeConnection[]>([]);
  const [connectionId, setConnectionId] = useState<string>("");
  const [symbol, setSymbol]             = useState("BTCUSDT");
  const [interval, setInterval]         = useState<string>("H1");
  const [fromDate, setFromDate]         = useState(() => isoDate(Date.now() - 30 * 86_400_000));
  const [toDate, setToDate]             = useState(() => isoDate(Date.now() - 86_400_000));
  const [timezone, setTimezone]         = useState("UTC");
  const [datasetName, setDatasetName]   = useState("");

  // UI state
  const [submitting, setSubmitting]   = useState(false);
  const [result, setResult]           = useState<CreateDatasetResult | null>(null);
  const [error, setError]             = useState<string | null>(null);
  const [datasets, setDatasets]       = useState<DatasetListItem[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [showForm, setShowForm]       = useState(true);

  useEffect(() => {
    if (!getWorkspaceId()) return;
    apiFetch<ExchangeConnection[]>("/exchanges").then((res) => {
      if (res.ok) setConnections(res.data);
    });
    loadDatasets();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadDatasets() {
    if (!getWorkspaceId()) return;
    setLoadingList(true);
    apiFetch<DatasetListItem[]>("/lab/datasets").then((res) => {
      if (res.ok) setDatasets(res.data);
      setLoadingList(false);
    });
  }

  // Client-side validation
  const fromMs    = new Date(fromDate).getTime();
  const toMs      = new Date(toDate).getTime();
  const rangeMs   = isFinite(fromMs) && isFinite(toMs) ? toMs - fromMs : 0;
  const rangeDays = rangeMs / 86_400_000;
  const estimatedCandles = estimateCandles(fromDate, toDate, interval);

  const validationErrors: string[] = [];
  if (!symbol.trim()) {
    validationErrors.push("Symbol is required.");
  }
  if (!fromDate || !toDate) {
    validationErrors.push("Date range is required.");
  } else if (fromMs >= toMs) {
    validationErrors.push("Start date must be before end date.");
  } else if (rangeDays > MAX_RANGE_DAYS) {
    validationErrors.push(`Date range must not exceed ${MAX_RANGE_DAYS} days (currently ${Math.ceil(rangeDays)} days).`);
  }
  if (estimatedCandles > MAX_CANDLES) {
    validationErrors.push(`Estimated ~${estimatedCandles.toLocaleString()} candles exceeds 100,000 limit. Use a larger interval or shorter range.`);
  }

  const canSubmit = validationErrors.length === 0 && !submitting;

  async function handleSubmit() {
    if (!canSubmit) return;
    if (!getWorkspaceId()) {
      setError("Workspace not set. Log in first.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setResult(null);

    const selectedConn  = connections.find((c) => c.id === connectionId);
    const exchangeName  = selectedConn?.exchange ?? "BYBIT";

    const res = await apiFetch<CreateDatasetResult>("/lab/datasets", {
      method: "POST",
      body: JSON.stringify({
        exchange:  exchangeName,
        symbol:    symbol.trim().toUpperCase(),
        interval,
        fromTs:    new Date(fromDate + "T00:00:00Z").toISOString(),
        toTs:      new Date(toDate   + "T23:59:59Z").toISOString(),
        ...(datasetName.trim() ? { name: datasetName.trim() } : {}),
      }),
    });

    setSubmitting(false);

    if (res.ok) {
      setResult(res.data);
      setActiveDatasetId(res.data.datasetId);
      setShowForm(false);
      loadDatasets();
    } else {
      const detail      = res.problem.detail ?? res.problem.title ?? "Unknown error";
      const fieldErrors = res.problem.errors?.map((e) => `${e.field}: ${e.message}`).join("; ");
      setError(fieldErrors ? `${detail} — ${fieldErrors}` : detail);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={pageStyle}>
      {/* Left: dataset list sidebar */}
      <div style={sidebarStyle}>
        <div style={sidebarHeaderStyle}>
          <span style={sectionLabelStyle}>Datasets</span>
          <button
            onClick={() => { setShowForm(true); setResult(null); setError(null); }}
            style={newBtnStyle}
            title="New dataset"
          >
            + New
          </button>
        </div>

        {loadingList && (
          <div style={{ padding: "12px 14px", fontSize: 12, color: "var(--text-secondary)" }}>
            Loading…
          </div>
        )}

        {!loadingList && datasets.length === 0 && (
          <div style={{ padding: "12px 14px", fontSize: 12, color: "var(--text-secondary)" }}>
            No datasets yet.
          </div>
        )}

        {datasets.map((ds) => (
          <DatasetRow
            key={ds.datasetId}
            ds={ds}
            isActive={activeDatasetId === ds.datasetId}
            onSelect={() => {
              setActiveDatasetId(ds.datasetId);
              setResult(null);
              setShowForm(false);
            }}
          />
        ))}
      </div>

      {/* Right: form or result or info */}
      <div style={mainStyle}>
        {showForm ? (
          <DatasetForm
            connections={connections}
            connectionId={connectionId}
            setConnectionId={setConnectionId}
            symbol={symbol}
            setSymbol={setSymbol}
            interval={interval}
            setInterval={setInterval}
            fromDate={fromDate}
            setFromDate={setFromDate}
            toDate={toDate}
            setToDate={setToDate}
            timezone={timezone}
            setTimezone={setTimezone}
            datasetName={datasetName}
            setDatasetName={setDatasetName}
            validationErrors={validationErrors}
            estimatedCandles={estimatedCandles}
            submitting={submitting}
            canSubmit={canSubmit}
            error={error}
            onSubmit={handleSubmit}
          />
        ) : result ? (
          <DatasetResult
            result={result}
            onNewDataset={() => { setShowForm(true); setResult(null); setError(null); }}
          />
        ) : activeDatasetId ? (
          <ActiveDatasetInfo
            datasetId={activeDatasetId}
            datasets={datasets}
            onNewDataset={() => { setShowForm(true); setResult(null); setError(null); }}
          />
        ) : (
          <EmptyState onNewDataset={() => setShowForm(true)} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DatasetForm
// ---------------------------------------------------------------------------

function DatasetForm({
  connections, connectionId, setConnectionId,
  symbol, setSymbol,
  interval, setInterval,
  fromDate, setFromDate,
  toDate, setToDate,
  timezone, setTimezone,
  datasetName, setDatasetName,
  validationErrors, estimatedCandles,
  submitting, canSubmit, error,
  onSubmit,
}: {
  connections: ExchangeConnection[];
  connectionId: string; setConnectionId: (v: string) => void;
  symbol: string; setSymbol: (v: string) => void;
  interval: string; setInterval: (v: string) => void;
  fromDate: string; setFromDate: (v: string) => void;
  toDate: string; setToDate: (v: string) => void;
  timezone: string; setTimezone: (v: string) => void;
  datasetName: string; setDatasetName: (v: string) => void;
  validationErrors: string[];
  estimatedCandles: number;
  submitting: boolean;
  canSubmit: boolean;
  error: string | null;
  onSubmit: () => void;
}) {
  return (
    <div style={formWrapStyle}>
      <h2 style={formTitleStyle}>New Dataset</h2>

      <FormField label="Exchange Connection">
        <select
          style={inputStyle}
          value={connectionId}
          onChange={(e) => setConnectionId(e.target.value)}
          disabled={submitting}
        >
          <option value="">Bybit (public — no connection required)</option>
          {connections.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} · {c.exchange} [{c.status}]
            </option>
          ))}
        </select>
      </FormField>

      <FormField label="Environment">
        <select style={{ ...inputStyle, opacity: 0.6 }} disabled>
          <option>Demo (testnet)</option>
        </select>
        <div style={hintStyle}>Real environment available in a future phase.</div>
      </FormField>

      <FormField label="Market Type">
        <select style={{ ...inputStyle, opacity: 0.6 }} disabled>
          <option>Linear (USDT perpetual)</option>
        </select>
        <div style={hintStyle}>Inverse and spot available in a future phase.</div>
      </FormField>

      <FormField label="Symbol">
        <input
          type="text"
          style={inputStyle}
          value={symbol}
          placeholder="e.g. BTCUSDT"
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          disabled={submitting}
          autoCapitalize="characters"
        />
      </FormField>

      <FormField label="Data Type">
        <select style={{ ...inputStyle, opacity: 0.6 }} disabled>
          <option>Candles (OHLCV)</option>
        </select>
        <div style={hintStyle}>Funding history and open interest in a future phase.</div>
      </FormField>

      <FormField label="Timeframe">
        <select
          style={inputStyle}
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
          disabled={submitting}
        >
          {INTERVALS.map((i) => (
            <option key={i} value={i}>{i}</option>
          ))}
        </select>
      </FormField>

      <FormField label="Date Range (max 365 days)">
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="date"
            style={{ ...inputStyle, flex: 1 }}
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            disabled={submitting}
          />
          <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>→</span>
          <input
            type="date"
            style={{ ...inputStyle, flex: 1 }}
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            disabled={submitting}
          />
        </div>
        {estimatedCandles > 0 && (
          <div style={{
            ...hintStyle,
            color: estimatedCandles > MAX_CANDLES
              ? "#f85149"
              : estimatedCandles > 80_000
              ? "#d29922"
              : "var(--text-secondary)",
          }}>
            ~{estimatedCandles.toLocaleString()} candles estimated
            {estimatedCandles > 80_000 && estimatedCandles <= MAX_CANDLES && " — approaching 100k limit"}
            {estimatedCandles > MAX_CANDLES && " — exceeds 100k limit"}
          </div>
        )}
      </FormField>

      <FormField label="Timezone">
        <select
          style={inputStyle}
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          disabled={submitting}
        >
          {TIMEZONES.map((tz) => (
            <option key={tz} value={tz}>{tz}</option>
          ))}
        </select>
      </FormField>

      <FormField label="Dataset Name (optional)">
        <input
          type="text"
          style={inputStyle}
          value={datasetName}
          placeholder="e.g. BTC 1H 2024 Q4"
          onChange={(e) => setDatasetName(e.target.value)}
          disabled={submitting}
          maxLength={100}
        />
      </FormField>

      {validationErrors.length > 0 && (
        <div style={validationBoxStyle}>
          {validationErrors.map((e, i) => (
            <div key={i} style={{ marginTop: i > 0 ? 4 : 0 }}>⚠ {e}</div>
          ))}
        </div>
      )}

      {error && (
        <div style={errorBoxStyle}>{error}</div>
      )}

      <button
        style={{ ...submitBtnStyle, opacity: canSubmit ? 1 : 0.5, cursor: canSubmit ? "pointer" : "not-allowed" }}
        disabled={!canSubmit}
        onClick={onSubmit}
      >
        {submitting ? "Fetching data… (may take up to 30s)" : "Fetch Dataset"}
      </button>

      {submitting && (
        <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 8 }}>
          Fetching candles from Bybit and computing quality metrics. Please wait — this is synchronous and may take up to 30 seconds for large ranges.
        </div>
      )}
    </div>
  );
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DatasetResult
// ---------------------------------------------------------------------------

function DatasetResult({
  result,
  onNewDataset,
}: {
  result: CreateDatasetResult;
  onNewDataset: () => void;
}) {
  return (
    <div style={formWrapStyle}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <h2 style={{ ...formTitleStyle, margin: 0 }}>Dataset Created</h2>
        <StatusBadge status={result.status} />
      </div>

      {result.status === "PARTIAL" && (
        <div style={warningBoxStyle}>
          Dataset is PARTIAL — some candles could not be fetched. Inspect quality details below.
        </div>
      )}
      {result.status === "FAILED" && (
        <div style={errorBoxStyle}>
          Dataset FAILED — data could not be retrieved. Try again or adjust the parameters.
        </div>
      )}

      <div style={metaGridStyle}>
        <MetaRow label="Dataset ID" value={result.datasetId} mono />
      </div>

      <QualitySummary
        status={result.status}
        qualityJson={result.qualityJson}
        candleCount={result.candleCount}
        datasetHash={result.datasetHash}
        fetchedAt={result.fetchedAt}
        engineVersion={result.engineVersion}
      />

      {result.status !== "FAILED" && (
        <DatasetPreview datasetId={result.datasetId} status={result.status} />
      )}
      {result.status === "FAILED" && (
        <div style={{ ...errorBoxStyle, marginTop: 16 }}>
          Preview unavailable — dataset is unusable. No candle data was stored.
        </div>
      )}

      <button onClick={onNewDataset} style={{ ...secondaryBtnStyle, marginTop: 20 }}>
        New Dataset
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ActiveDatasetInfo
// ---------------------------------------------------------------------------

function ActiveDatasetInfo({
  datasetId,
  datasets,
  onNewDataset,
}: {
  datasetId: string;
  datasets: DatasetListItem[];
  onNewDataset: () => void;
}) {
  const ds = datasets.find((d) => d.datasetId === datasetId);

  // Fetch full detail (qualityJson + engineVersion) from GET /lab/datasets/:id
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  useEffect(() => {
    if (!datasetId || !getWorkspaceId()) return;
    setDetail(null);
    apiFetch<DatasetDetail>(`/lab/datasets/${datasetId}`).then((res) => {
      if (res.ok) setDetail(res.data);
    });
  }, [datasetId]);

  if (!ds) {
    return (
      <div style={formWrapStyle}>
        <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          Dataset <code style={{ fontSize: 11 }}>{datasetId}</code> is active.
        </div>
        <button onClick={onNewDataset} style={{ ...secondaryBtnStyle, marginTop: 16 }}>New Dataset</button>
      </div>
    );
  }

  const from  = formatDateShort(new Date(Number(ds.fromTsMs)).toISOString());
  const to    = formatDateShort(new Date(Number(ds.toTsMs)).toISOString());
  const label = ds.name ?? `${ds.exchange} · ${ds.symbol} · ${ds.interval}`;

  return (
    <div style={formWrapStyle}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <h2 style={{ ...formTitleStyle, margin: 0 }}>{label}</h2>
        <StatusBadge status={ds.status} />
      </div>

      {ds.status === "PARTIAL" && (
        <div style={warningBoxStyle}>
          Dataset is PARTIAL — some candles could not be fetched. See quality details below.
        </div>
      )}
      {ds.status === "FAILED" && (
        <div style={errorBoxStyle}>
          Dataset FAILED — no usable candle data is available. Create a new dataset to continue.
        </div>
      )}

      <div style={metaGridStyle}>
        <MetaRow label="Exchange"   value={ds.exchange} />
        <MetaRow label="Symbol"     value={ds.symbol} />
        <MetaRow label="Interval"   value={ds.interval} />
        <MetaRow label="Range"      value={`${from} → ${to}`} />
        <MetaRow label="Dataset ID" value={ds.datasetId} mono />
      </div>

      <QualitySummary
        status={ds.status}
        qualityJson={detail?.qualityJson ?? null}
        candleCount={ds.candleCount}
        datasetHash={ds.datasetHash}
        fetchedAt={ds.fetchedAt}
        engineVersion={detail?.engineVersion}
      />

      {ds.status !== "FAILED" && (
        <DatasetPreview datasetId={ds.datasetId} status={ds.status} />
      )}
      {ds.status === "FAILED" && (
        <div style={{ ...errorBoxStyle, marginTop: 16 }}>
          Preview unavailable — dataset is unusable. No candle data was stored.
        </div>
      )}

      <button onClick={onNewDataset} style={{ ...secondaryBtnStyle, marginTop: 20 }}>
        New Dataset
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// EmptyState
// ---------------------------------------------------------------------------

function EmptyState({ onNewDataset }: { onNewDataset: () => void }) {
  return (
    <div style={{ padding: "48px 40px", maxWidth: 480 }}>
      <h2 style={{ fontSize: 18, marginBottom: 12, color: "var(--text-primary)" }}>
        Dataset Builder
      </h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>
        Connect an exchange, select an instrument, define a timeframe and date range,
        and fetch a reusable market dataset for strategy research.
      </p>
      <button onClick={onNewDataset} style={submitBtnStyle}>
        New Dataset
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// QualitySummary — Phase 2C
// Collapsible quality block: compact one-liner → expanded detail table.
// Works for both DatasetResult (after submit) and ActiveDatasetInfo (selected).
// ---------------------------------------------------------------------------

type QualityStatus = "READY" | "PARTIAL" | "FAILED";

const QUALITY_KNOWN_FIELDS = ["gapsCount", "maxGapMs", "dupeAttempts", "sanityIssuesCount"];

const QUALITY_STATUS_META: Record<QualityStatus, { color: string; label: string; detail: string }> = {
  READY:   {
    color:  "#3fb950",
    label:  "All clear",
    detail: "All candles fetched and validated successfully.",
  },
  PARTIAL: {
    color:  "#d29922",
    label:  "Partial",
    detail: "Some candles could not be fetched. Data may have gaps — use results with caution.",
  },
  FAILED:  {
    color:  "#f85149",
    label:  "Unusable",
    detail: "Dataset build failed. No candle data is available. Adjust parameters and try again.",
  },
};

function QualitySummary({
  status,
  qualityJson,
  candleCount,
  datasetHash,
  fetchedAt,
  engineVersion,
}: {
  status:        QualityStatus;
  qualityJson:   unknown;
  candleCount?:  number;
  datasetHash?:  string;
  fetchedAt?:    string | Date;
  engineVersion?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const [rawOpen,  setRawOpen]  = useState(false);

  const q: Record<string, unknown> =
    qualityJson != null && typeof qualityJson === "object" && !Array.isArray(qualityJson)
      ? (qualityJson as Record<string, unknown>)
      : {};

  const gapsCount    = typeof q.gapsCount          === "number" ? (q.gapsCount as number)         : null;
  const maxGapMs     = typeof q.maxGapMs            === "number" ? (q.maxGapMs as number)           : null;
  const dupeAttempts = typeof q.dupeAttempts        === "number" ? (q.dupeAttempts as number)       : null;
  const sanityIssues = typeof q.sanityIssuesCount   === "number" ? (q.sanityIssuesCount as number)  : null;

  const extraEntries = Object.entries(q).filter(([k]) => !QUALITY_KNOWN_FIELDS.includes(k));
  const issueCount   = (gapsCount ?? 0) + (dupeAttempts ?? 0) + (sanityIssues ?? 0);

  const meta = QUALITY_STATUS_META[status];

  // Compact summary suffix shown next to the status detail line
  const compactSuffix =
    status === "FAILED"
      ? ""
      : candleCount != null
      ? ` · ${candleCount.toLocaleString()} candles · ${issueCount === 0 ? "no issues" : `${issueCount} issue${issueCount > 1 ? "s" : ""}`}`
      : "";

  return (
    <div style={qualitySectionStyle}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={sectionLabelStyle}>Quality</span>
        <span style={{ fontSize: 11, color: meta.color, fontWeight: 600 }}>{meta.label}</span>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setExpanded((e) => !e)}
          style={toggleBtnStyle}
          aria-expanded={expanded}
        >
          {expanded ? "▲ Less" : "▼ Details"}
        </button>
      </div>

      {/* Compact summary line */}
      <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        {meta.detail}
        {!expanded && compactSuffix}
      </div>

      {/* Expanded table */}
      {expanded && (
        <div style={{ marginTop: 12 }}>
          <div style={metaGridStyle}>
            {candleCount != null && (
              <MetaRow label="Candles"       value={candleCount.toLocaleString()} />
            )}
            {gapsCount !== null && (
              <MetaRow label="Gaps"          value={gapsCount === 0 ? "None" : String(gapsCount)} />
            )}
            {maxGapMs !== null && (
              <MetaRow label="Max gap"       value={maxGapMs === 0 ? "—" : `${Math.round(maxGapMs / 60_000)} min`} />
            )}
            {dupeAttempts !== null && (
              <MetaRow label="Dupe attempts" value={String(dupeAttempts)} />
            )}
            {sanityIssues !== null && (
              <MetaRow label="Sanity issues" value={sanityIssues === 0 ? "None" : String(sanityIssues)} />
            )}
            {datasetHash && (
              <MetaRow label="Hash"          value={datasetHash.slice(0, 20) + "…"} mono />
            )}
            {fetchedAt && (
              <MetaRow label="Fetched at"    value={new Date(fetchedAt).toLocaleString()} />
            )}
            {engineVersion && (
              <MetaRow label="Engine"        value={engineVersion} mono />
            )}
          </div>

          {/* Raw details expander for unexpected qualityJson fields */}
          {extraEntries.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <button onClick={() => setRawOpen((r) => !r)} style={toggleBtnStyle}>
                {rawOpen ? "▲ Hide raw" : "▼ Raw details"}
              </button>
              {rawOpen && (
                <div style={{ marginTop: 6, border: "1px solid var(--border)", borderRadius: 4, padding: "6px 10px" }}>
                  {extraEntries.map(([k, v]) => (
                    <div
                      key={k}
                      style={{
                        display: "flex", gap: 8, padding: "3px 0",
                        borderBottom: "1px solid var(--border)", fontSize: 11,
                      }}
                    >
                      <span style={{ color: "var(--text-secondary)", width: 140, flexShrink: 0, fontFamily: "monospace" }}>
                        {k}
                      </span>
                      <span style={{ color: "var(--text-primary)", fontFamily: "monospace", wordBreak: "break-all" }}>
                        {typeof v === "object" ? JSON.stringify(v) : String(v ?? "")}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// MetaRow
// ---------------------------------------------------------------------------

function MetaRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", gap: 12, padding: "5px 0", borderBottom: "1px solid var(--border)" }}>
      <span style={{ fontSize: 12, color: "var(--text-secondary)", width: 120, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 12, color: "var(--text-primary)", fontFamily: mono ? "monospace" : undefined, wordBreak: "break-all" }}>
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const pageStyle: React.CSSProperties = {
  display: "flex",
  height: "100%",
  overflow: "hidden",
};

const sidebarStyle: React.CSSProperties = {
  width: 260,
  flexShrink: 0,
  borderRight: "1px solid var(--border)",
  display: "flex",
  flexDirection: "column",
  overflow: "auto",
};

const sidebarHeaderStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "12px 14px",
  borderBottom: "1px solid var(--border)",
  flexShrink: 0,
};

const mainStyle: React.CSSProperties = {
  flex: 1,
  overflow: "auto",
};

const formWrapStyle: React.CSSProperties = {
  padding: "28px 32px",
  maxWidth: 560,
};

const formTitleStyle: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: 20,
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: 11,
  fontWeight: 600,
  color: "var(--text-secondary)",
  marginBottom: 6,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
};

const inputStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.07)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6,
  padding: "8px 10px",
  color: "inherit",
  fontSize: 13,
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
};

const hintStyle: React.CSSProperties = {
  fontSize: 11,
  color: "var(--text-secondary)",
  marginTop: 4,
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "var(--text-secondary)",
};

const validationBoxStyle: React.CSSProperties = {
  background: "rgba(210,153,34,0.12)",
  border: "1px solid rgba(210,153,34,0.4)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#d29922",
  marginBottom: 16,
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,81,73,0.12)",
  border: "1px solid rgba(248,81,73,0.4)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#f85149",
  marginBottom: 16,
};

const warningBoxStyle: React.CSSProperties = {
  background: "rgba(210,153,34,0.12)",
  border: "1px solid rgba(210,153,34,0.4)",
  borderRadius: 6,
  padding: "10px 14px",
  fontSize: 12,
  color: "#d29922",
  marginBottom: 16,
};

const metaGridStyle: React.CSSProperties = {
  border: "1px solid var(--border)",
  borderRadius: 6,
  overflow: "hidden",
  padding: "4px 12px",
};

const submitBtnStyle: React.CSSProperties = {
  background: "var(--accent, #3b82f6)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  padding: "10px 20px",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
  width: "100%",
  marginTop: 8,
};

const secondaryBtnStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.07)",
  color: "var(--text-primary)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 6,
  padding: "8px 16px",
  fontSize: 13,
  cursor: "pointer",
};

const newBtnStyle: React.CSSProperties = {
  background: "var(--accent, #3b82f6)",
  color: "#fff",
  border: "none",
  borderRadius: 4,
  padding: "4px 10px",
  fontSize: 11,
  fontWeight: 600,
  cursor: "pointer",
};

const qualitySectionStyle: React.CSSProperties = {
  marginTop: 20,
  border: "1px solid var(--border)",
  borderRadius: 6,
  padding: "12px 14px",
};

const toggleBtnStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--text-secondary)",
  fontSize: 11,
  cursor: "pointer",
  padding: 0,
};
