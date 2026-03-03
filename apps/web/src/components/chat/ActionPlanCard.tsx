"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

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

interface ExecuteResponse {
  actionId: string;
  type: string;
  status: string;
  result: Record<string, unknown>;
  executedAt: string;
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

const confirmBtnDisabledStyle: React.CSSProperties = {
  ...confirmBtnStyle,
  opacity: 0.4,
  cursor: "not-allowed",
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

// ---------------------------------------------------------------------------
// Per-action execution state (managed at card level for cross-action dep checks)
// ---------------------------------------------------------------------------

type ActionStatus = "pending" | "executing" | "executed" | "failed" | "cancelled";

interface ActionState {
  status: ActionStatus;
  result?: Record<string, unknown>;
  error?: string;
}

// ---------------------------------------------------------------------------
// Single action row
// ---------------------------------------------------------------------------

interface ActionItemRowProps {
  item: ActionItem;
  planId: string;
  state: ActionState;
  depsExecuted: boolean;
  onExecuting: (actionId: string) => void;
  onExecuted: (actionId: string, result: Record<string, unknown>) => void;
  onFailed: (actionId: string, error: string) => void;
  onCancelled: (actionId: string) => void;
}

function ActionItemRow({ item, planId, state, depsExecuted, onExecuting, onExecuted, onFailed, onCancelled }: ActionItemRowProps) {
  const [showJson, setShowJson] = useState(false);

  async function handleConfirm() {
    if (state.status !== "pending") return;
    onExecuting(item.actionId);

    const res = await apiFetch<ExecuteResponse>("/ai/execute", {
      method: "POST",
      body: JSON.stringify({ planId, actionId: item.actionId }),
    });

    if (res.ok) {
      onExecuted(item.actionId, res.data.result);
    } else {
      onFailed(item.actionId, res.problem.detail ?? "Execution failed");
    }
  }

  if (state.status === "cancelled") {
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

  if (state.status === "executed") {
    return (
      <div style={actionRowStyle}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
          <span style={typeBadgeStyle}>{item.type}</span>
          <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{item.title}</span>
          <span style={{ fontSize: "11px", color: "#3fb950", fontWeight: 600 }}>✓ Done</span>
        </div>
        {state.result && Object.keys(state.result).length > 0 && (
          <pre style={{ ...jsonPreStyle, borderLeft: "2px solid #3fb950" }}>
            {JSON.stringify(state.result, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  if (state.status === "failed") {
    return (
      <div style={{ ...actionRowStyle, borderLeft: "2px solid #f85149" }}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
          <span style={typeBadgeStyle}>{item.type}</span>
          <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{item.title}</span>
          <span style={{ fontSize: "11px", color: "#f85149", fontWeight: 600 }}>✗ Failed</span>
        </div>
        {state.error && (
          <div style={{ fontSize: "12px", color: "#f85149" }}>{state.error}</div>
        )}
      </div>
    );
  }

  const isExecuting = state.status === "executing";
  const canConfirm = depsExecuted && !isExecuting;
  const blockReason = !depsExecuted ? "Complete previous steps first" : null;

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

      {/* Dependency block hint */}
      {blockReason && (
        <div style={{ fontSize: "11px", color: "var(--text-secondary)", fontStyle: "italic" }}>
          🔒 {blockReason}
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

      {/* HIGH danger warning */}
      {item.dangerLevel === "HIGH" && state.status === "pending" && (
        <div style={{ fontSize: "11px", color: "#f85149", background: "rgba(248,81,73,0.08)", borderRadius: "4px", padding: "4px 8px" }}>
          ⚠ High-risk action — this will stop an active run. Confirm carefully.
        </div>
      )}

      {/* Action buttons */}
      <div style={btnRow}>
        <button
          style={canConfirm ? confirmBtnStyle : confirmBtnDisabledStyle}
          onClick={canConfirm ? handleConfirm : undefined}
          disabled={!canConfirm}
        >
          {isExecuting ? "Running…" : "Confirm"}
        </button>
        {!isExecuting && (
          <button style={cancelBtnStyle} onClick={() => onCancelled(item.actionId)}>
            Cancel
          </button>
        )}
      </div>
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
  // Track per-action state at card level to enforce dependency ordering
  const [actionStates, setActionStates] = useState<Record<string, ActionState>>(() => {
    const init: Record<string, ActionState> = {};
    for (const a of plan.actions) init[a.actionId] = { status: "pending" };
    return init;
  });

  function setActionState(actionId: string, update: Partial<ActionState>) {
    setActionStates((prev) => ({
      ...prev,
      [actionId]: { ...prev[actionId], ...update },
    }));
  }

  function areDepsExecuted(item: ActionItem): boolean {
    if (!item.dependsOn || item.dependsOn.length === 0) return true;
    return item.dependsOn.every(
      (depId) => actionStates[depId]?.status === "executed",
    );
  }

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
        <ActionItemRow
          key={item.actionId}
          item={item}
          planId={plan.planId}
          state={actionStates[item.actionId] ?? { status: "pending" }}
          depsExecuted={areDepsExecuted(item)}
          onExecuting={(id) => setActionState(id, { status: "executing" })}
          onExecuted={(id, result) => setActionState(id, { status: "executed", result })}
          onFailed={(id, error) => setActionState(id, { status: "failed", error })}
          onCancelled={(id) => setActionState(id, { status: "cancelled" })}
        />
      ))}

      <div style={{ padding: "6px 12px", fontSize: "11px", color: "var(--text-secondary)", borderTop: plan.actions.length > 0 ? "1px solid var(--border)" : "none" }}>
        Plan ID: {plan.planId.slice(0, 8)}… · Expires {new Date(plan.expiresAt).toLocaleTimeString()}
      </div>
    </div>
  );
}
