"use client";

import { useState } from "react";

// ---------------------------------------------------------------------------
// Types (mirrored from backend planParser.ts — no shared package in this repo)
// ---------------------------------------------------------------------------

export type DangerLevel = "LOW" | "MEDIUM" | "HIGH";

export interface ActionItem {
  actionId: string;
  type: string;
  title: string;
  dangerLevel: DangerLevel;
  requiresConfirmation: boolean;
  dependsOn: string[];
  input: Record<string, unknown>;
  preconditions: string[];
  expectedOutcome: string;
}

export interface ActionPlan {
  planId: string;
  createdAt: string;
  expiresAt: string;
  actions: ActionItem[];
  note?: string;
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "10px",
  overflow: "hidden",
  fontSize: "13px",
  width: "100%",
};

const cardHeaderStyle: React.CSSProperties = {
  padding: "8px 12px",
  background: "rgba(255,255,255,0.04)",
  borderBottom: "1px solid var(--border)",
  display: "flex",
  alignItems: "center",
  gap: "6px",
  fontWeight: 600,
  color: "var(--text-primary)",
};

const actionRowStyle: React.CSSProperties = {
  borderBottom: "1px solid var(--border)",
  padding: "10px 12px",
  display: "flex",
  flexDirection: "column",
  gap: "6px",
};

const badgeStyle = (level: DangerLevel): React.CSSProperties => {
  const colors: Record<DangerLevel, { bg: string; color: string }> = {
    LOW:    { bg: "rgba(63,185,80,0.15)",  color: "#3fb950" },
    MEDIUM: { bg: "rgba(210,153,34,0.15)", color: "#e3b341" },
    HIGH:   { bg: "rgba(248,81,73,0.15)",  color: "#f85149" },
  };
  return {
    display: "inline-block",
    padding: "1px 7px",
    borderRadius: "10px",
    fontSize: "11px",
    fontWeight: 600,
    ...colors[level],
  };
};

const typeBadgeStyle: React.CSSProperties = {
  display: "inline-block",
  padding: "1px 7px",
  borderRadius: "4px",
  fontSize: "11px",
  fontWeight: 600,
  background: "rgba(88,166,255,0.15)",
  color: "#58a6ff",
  fontFamily: "monospace",
};

const btnRow: React.CSSProperties = {
  display: "flex",
  gap: "6px",
  marginTop: "4px",
};

const confirmBtnStyle: React.CSSProperties = {
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: "6px",
  padding: "5px 12px",
  fontSize: "12px",
  fontWeight: 600,
  cursor: "pointer",
};

const cancelBtnStyle: React.CSSProperties = {
  background: "transparent",
  color: "var(--text-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  padding: "5px 12px",
  fontSize: "12px",
  cursor: "pointer",
};

const jsonToggleStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--text-secondary)",
  fontSize: "11px",
  cursor: "pointer",
  padding: "0",
  textDecoration: "underline",
};

const jsonPreStyle: React.CSSProperties = {
  background: "rgba(0,0,0,0.3)",
  borderRadius: "4px",
  padding: "6px 8px",
  fontSize: "11px",
  color: "var(--text-secondary)",
  overflowX: "auto",
  whiteSpace: "pre-wrap",
  wordBreak: "break-all",
  margin: "0",
  maxHeight: "120px",
  overflowY: "auto",
};

const toastStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#e3b341",
  padding: "4px 0 0 0",
};

// ---------------------------------------------------------------------------
// Single action row
// ---------------------------------------------------------------------------

type ActionStatus = "pending" | "cancelled" | "confirmed_stub";

interface ActionItemRowProps {
  item: ActionItem;
}

function ActionItemRow({ item }: ActionItemRowProps) {
  const [status, setStatus] = useState<ActionStatus>("pending");
  const [showJson, setShowJson] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  function handleConfirm() {
    // Stage 18a: execution not yet implemented — show stub message
    setToast("✓ Noted — execution coming in Stage 18b");
    setStatus("confirmed_stub");
    setTimeout(() => setToast(null), 4000);
  }

  function handleCancel() {
    setStatus("cancelled");
  }

  if (status === "cancelled") {
    return (
      <div style={{ ...actionRowStyle, opacity: 0.45 }}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          <span style={typeBadgeStyle}>{item.type}</span>
          <span style={{ color: "var(--text-secondary)", textDecoration: "line-through" }}>{item.title}</span>
          <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Cancelled</span>
        </div>
      </div>
    );
  }

  return (
    <div style={actionRowStyle}>
      {/* Top row: type badge + title + danger */}
      <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
        <span style={typeBadgeStyle}>{item.type}</span>
        <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{item.title}</span>
        <span style={badgeStyle(item.dangerLevel)}>{item.dangerLevel}</span>
      </div>

      {/* Expected outcome */}
      {item.expectedOutcome && (
        <div style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
          {item.expectedOutcome}
        </div>
      )}

      {/* Preconditions */}
      {item.preconditions.length > 0 && (
        <div style={{ color: "#e3b341", fontSize: "11px" }}>
          ⚠ {item.preconditions.join("; ")}
        </div>
      )}

      {/* JSON toggle */}
      <div>
        <button style={jsonToggleStyle} onClick={() => setShowJson((v) => !v)}>
          {showJson ? "Hide input ▲" : "Show input ▼"}
        </button>
        {showJson && (
          <pre style={jsonPreStyle}>
            {JSON.stringify(item.input, null, 2)}
          </pre>
        )}
      </div>

      {/* Action buttons */}
      {status === "confirmed_stub" ? (
        <div style={toastStyle}>✓ Noted — execution coming in Stage 18b</div>
      ) : (
        <div style={btnRow}>
          <button style={confirmBtnStyle} onClick={handleConfirm}>
            Confirm
          </button>
          <button style={cancelBtnStyle} onClick={handleCancel}>
            Cancel
          </button>
        </div>
      )}

      {toast && status !== "confirmed_stub" && (
        <div style={toastStyle}>{toast}</div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ActionPlanCard
// ---------------------------------------------------------------------------

interface ActionPlanCardProps {
  plan: ActionPlan;
}

export function ActionPlanCard({ plan }: ActionPlanCardProps) {
  return (
    <div style={cardStyle}>
      <div style={cardHeaderStyle}>
        <span>⚡</span>
        <span>Proposed Actions ({plan.actions.length})</span>
        {plan.actions.length === 0 && (
          <span style={{ fontWeight: 400, color: "var(--text-secondary)", marginLeft: "4px" }}>
            — no actions available
          </span>
        )}
      </div>

      {plan.note && (
        <div style={{ padding: "8px 12px", color: "var(--text-secondary)", fontSize: "12px", borderBottom: "1px solid var(--border)" }}>
          {plan.note}
        </div>
      )}

      {plan.actions.length === 0 && !plan.note && (
        <div style={{ padding: "12px", color: "var(--text-secondary)", fontSize: "12px" }}>
          The assistant could not map this request to any available actions.
          Try rephrasing or use the Explain tab for guidance.
        </div>
      )}

      {plan.actions.map((item) => (
        <ActionItemRow key={item.actionId} item={item} />
      ))}

      <div style={{ padding: "6px 12px", fontSize: "11px", color: "var(--text-secondary)", borderTop: plan.actions.length > 0 ? "1px solid var(--border)" : "none" }}>
        Plan ID: {plan.planId.slice(0, 8)}… · Expires {new Date(plan.expiresAt).toLocaleTimeString()}
      </div>
    </div>
  );
}
