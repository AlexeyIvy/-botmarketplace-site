"use client";

import { useEffect, useState } from "react";
import {
  instantiatePreset,
  type InstantiateOverrides,
  type PresetSummary,
  type PresetTimeframe,
} from "../../../lib/api/presets";
import type { ProblemDetails } from "../../../lib/api";

const TIMEFRAMES: PresetTimeframe[] = ["M1", "M5", "M15", "H1"];

interface FormState {
  name: string;
  symbol: string;
  timeframe: PresetTimeframe;
  quoteAmount: string;
  maxOpenPositions: string;
}

function initialFormState(preset: PresetSummary): FormState {
  const cfg = preset.defaultBotConfigJson;
  return {
    name: preset.name,
    symbol: cfg.symbol,
    timeframe: cfg.timeframe,
    quoteAmount: String(cfg.quoteAmount),
    maxOpenPositions: String(cfg.maxOpenPositions),
  };
}

export function InstantiateDialog({
  preset,
  adminToken,
  onClose,
  onCreated,
}: {
  preset: PresetSummary;
  adminToken?: string;
  onClose: () => void;
  onCreated: (botId: string) => void;
}) {
  const [form, setForm] = useState<FormState>(() => initialFormState(preset));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<ProblemDetails | string | null>(null);

  useEffect(() => {
    setForm(initialFormState(preset));
  }, [preset]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !submitting) onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, submitting]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const quoteAmount = Number(form.quoteAmount);
    const maxOpenPositions = Number(form.maxOpenPositions);
    if (!Number.isFinite(quoteAmount) || quoteAmount <= 0) {
      setError("quoteAmount must be a positive number");
      return;
    }
    if (!Number.isInteger(maxOpenPositions) || maxOpenPositions < 1) {
      setError("maxOpenPositions must be a positive integer");
      return;
    }
    if (form.symbol.trim().length === 0) {
      setError("symbol is required");
      return;
    }
    if (form.name.trim().length === 0 || form.name.length > 120) {
      setError("name must be 1..120 chars");
      return;
    }

    const overrides: InstantiateOverrides = {
      name: form.name,
      symbol: form.symbol.trim(),
      timeframe: form.timeframe,
      quoteAmount,
      maxOpenPositions,
    };

    setSubmitting(true);
    const res = await instantiatePreset(preset.slug, { overrides }, { adminToken });
    setSubmitting(false);

    if (!res.ok) {
      setError(res.problem);
      return;
    }
    onCreated(res.data.botId);
  }

  const hasBundleHint =
    preset.datasetBundleHintJson != null &&
    typeof preset.datasetBundleHintJson === "object" &&
    Object.keys(preset.datasetBundleHintJson as Record<string, unknown>).length > 0;

  return (
    <div style={overlayStyle} onClick={() => !submitting && onClose()}>
      <div
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`Configure preset ${preset.name}`}
      >
        <header style={headerStyle}>
          <h2 style={titleStyle}>{preset.name}</h2>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            style={closeBtnStyle}
            aria-label="Close"
          >
            ×
          </button>
        </header>

        <p style={descStyle}>{preset.description}</p>

        {hasBundleHint && (
          <div style={hintBoxStyle}>
            This preset uses multi-interval data. Configure the dataset bundle
            on the bot page after creation.
          </div>
        )}

        <form onSubmit={handleSubmit} style={formStyle}>
          <Field label="Bot name">
            <input
              style={inputStyle}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              maxLength={120}
              required
            />
          </Field>

          <div style={rowStyle}>
            <Field label="Symbol">
              <input
                style={inputStyle}
                value={form.symbol}
                onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })}
                required
              />
            </Field>
            <Field label="Timeframe">
              <select
                style={inputStyle}
                value={form.timeframe}
                onChange={(e) => setForm({ ...form, timeframe: e.target.value as PresetTimeframe })}
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </select>
            </Field>
          </div>

          <div style={rowStyle}>
            <Field label="Quote amount (USDT)">
              <input
                style={inputStyle}
                type="number"
                step="any"
                min="0"
                value={form.quoteAmount}
                onChange={(e) => setForm({ ...form, quoteAmount: e.target.value })}
                required
              />
            </Field>
            <Field label="Max open positions">
              <input
                style={inputStyle}
                type="number"
                step="1"
                min="1"
                value={form.maxOpenPositions}
                onChange={(e) => setForm({ ...form, maxOpenPositions: e.target.value })}
                required
              />
            </Field>
          </div>

          {error && <ErrorBox error={error} />}

          <footer style={footerStyle}>
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              style={secondaryBtnStyle}
            >
              Cancel
            </button>
            <button type="submit" disabled={submitting} style={primaryBtnStyle}>
              {submitting ? "Creating…" : "Create bot"}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={fieldStyle}>
      <span style={fieldLabelStyle}>{label}</span>
      {children}
    </label>
  );
}

function ErrorBox({ error }: { error: ProblemDetails | string }) {
  const text = typeof error === "string" ? error : `${error.title}: ${error.detail}`;
  const fieldErrors =
    typeof error === "object" && Array.isArray(error.errors) ? error.errors : [];
  return (
    <div style={errorBoxStyle}>
      <strong style={{ color: "#f87171" }}>{text}</strong>
      {fieldErrors.length > 0 && (
        <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 12 }}>
          {fieldErrors.map((fe, i) => (
            <li key={i}>
              <code>{fe.field}</code>: {fe.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 1000,
  background: "rgba(0,0,0,0.5)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 16,
};

const modalStyle: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 10,
  padding: 24,
  width: "100%",
  maxWidth: 540,
  maxHeight: "90vh",
  overflowY: "auto",
  boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
  marginBottom: 8,
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 18,
  fontWeight: 600,
  color: "var(--text-primary)",
};

const closeBtnStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "rgba(255,255,255,0.55)",
  fontSize: 22,
  lineHeight: 1,
  cursor: "pointer",
  padding: 0,
  width: 28,
  height: 28,
};

const descStyle: React.CSSProperties = {
  margin: "0 0 16px",
  color: "var(--text-secondary)",
  fontSize: 13,
  lineHeight: 1.5,
};

const hintBoxStyle: React.CSSProperties = {
  background: "rgba(59,130,246,0.08)",
  border: "1px solid rgba(59,130,246,0.3)",
  borderRadius: 6,
  padding: "8px 12px",
  marginBottom: 16,
  fontSize: 12,
  color: "#93c5fd",
};

const formStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 12,
};

const rowStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 12,
};

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
};

const fieldLabelStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-secondary)",
};

const inputStyle: React.CSSProperties = {
  padding: "7px 10px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 13,
  fontFamily: "inherit",
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,113,113,0.08)",
  border: "1px solid rgba(248,113,113,0.4)",
  borderRadius: 6,
  padding: "8px 12px",
  fontSize: 13,
};

const footerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
  gap: 8,
  marginTop: 8,
};

const primaryBtnStyle: React.CSSProperties = {
  padding: "8px 16px",
  fontSize: 13,
  fontWeight: 600,
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontFamily: "inherit",
};

const secondaryBtnStyle: React.CSSProperties = {
  padding: "8px 16px",
  fontSize: 13,
  fontWeight: 500,
  background: "transparent",
  color: "var(--text-primary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  cursor: "pointer",
  fontFamily: "inherit",
};
