"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { useLabGraphStore } from "./useLabGraphStore";

// ---------------------------------------------------------------------------
// Tab definitions — order matches spec
// ---------------------------------------------------------------------------

const TABS = [
  { id: "classic", label: "Classic mode", href: "/lab" },
  { id: "data",    label: "Data",         href: "/lab/data" },
  { id: "build",   label: "Build",        href: "/lab/build" },
  { id: "test",    label: "Test",         href: "/lab/test" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function getActiveTab(pathname: string): TabId {
  if (pathname === "/lab" || pathname === "/lab/") return "classic";
  if (pathname.startsWith("/lab/data"))  return "data";
  if (pathname.startsWith("/lab/build")) return "build";
  if (pathname.startsWith("/lab/test"))  return "test";
  return "classic";
}

// ---------------------------------------------------------------------------
// Context Bar — Phase 1B + Phase 4B
// Phase 4B: adds Compile & Save button + success badge
// ---------------------------------------------------------------------------

function LabContextBar({ activeTab }: { activeTab: TabId }) {
  const activeConnectionId = useLabGraphStore((s) => s.activeConnectionId);
  const activeDatasetId    = useLabGraphStore((s) => s.activeDatasetId);
  const validationState    = useLabGraphStore((s) => s.validationState);
  const runState           = useLabGraphStore((s) => s.runState);
  // Phase 4
  const nodes              = useLabGraphStore((s) => s.nodes);
  const edges              = useLabGraphStore((s) => s.edges);
  const activeGraphId      = useLabGraphStore((s) => s.activeGraphId);
  const compileState       = useLabGraphStore((s) => s.compileState);
  const lastCompileResult  = useLabGraphStore((s) => s.lastCompileResult);
  const setCompileState    = useLabGraphStore((s) => s.setCompileState);
  const setLastCompileResult = useLabGraphStore((s) => s.setLastCompileResult);
  const setServerIssues    = useLabGraphStore((s) => s.setServerIssues);
  // Phase 3A: persistence state (independent of compile/validation)
  const saveState          = useLabGraphStore((s) => s.saveState);

  // Phase 3A: show toast when save_error transitions in
  const [showSaveErrorToast, setShowSaveErrorToast] = useState(false);
  useEffect(() => {
    if (saveState === "save_error") {
      setShowSaveErrorToast(true);
      const t = setTimeout(() => setShowSaveErrorToast(false), 5000);
      return () => clearTimeout(t);
    }
  }, [saveState]);

  const isOnBuildTab  = activeTab === "build";
  const graphIsEmpty  = nodes.length === 0;
  // Phase 3A: compile requires a persisted graph (activeGraphId set by mount hydration)
  const compileDisabled = !isOnBuildTab || graphIsEmpty || compileState === "compiling" || !activeGraphId;

  const handleCompile = useCallback(async () => {
    if (compileDisabled) return;
    setCompileState("compiling");
    setServerIssues([]);

    const graphJson = { nodes, edges };

    try {
      // Phase 3A: activeGraphId must already be set by mount hydration.
      // Compile is no longer the first persistence path.
      const graphId = activeGraphId;
      if (!graphId) {
        setCompileState("error");
        return;
      }

      // Compile against the persisted graph record
      const compileRes = await fetch(`/api/v1/lab/graphs/${graphId}/compile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ graphJson, symbol: "BTCUSDT", timeframe: "M15" }),
      });

      if (compileRes.status === 422) {
        const body = await compileRes.json() as { validationIssues: import("./useLabGraphStore").ServerCompileIssue[] };
        setServerIssues(body.validationIssues ?? []);
        setCompileState("error");
        return;
      }

      if (!compileRes.ok) {
        setCompileState("error");
        return;
      }

      const result = await compileRes.json() as import("./useLabGraphStore").CompileResult;
      setLastCompileResult(result);
      setServerIssues(result.validationIssues ?? []);
      setCompileState("success");
    } catch {
      setCompileState("error");
    }
  }, [
    compileDisabled, nodes, edges, activeGraphId,
    setCompileState, setLastCompileResult, setServerIssues,
  ]);

  const compileLabel =
    compileState === "compiling" ? "Compiling…" :
    compileState === "success"   ? "Compile & Save" :
    "Compile & Save";

  const compileBtnColor =
    compileState === "success" ? "#52A97C" :
    compileState === "error"   ? "#D44C4C" :
    "#3B82F6";

  // Phase 3A: save state label + color (independent of compile/validation)
  const saveLabel =
    saveState === "clean"                      ? "Saved" :
    saveState === "dirty"                      ? "Unsaved" :
    saveState === "saving"                     ? "Saving…" :
    saveState === "save_error"                 ? "Save Error" :
    saveState === "stale_against_last_compile" ? "Saved · recompile needed" :
    "—";

  const saveLabelColor =
    saveState === "clean"                      ? "#52A97C" :
    saveState === "dirty"                      ? "rgba(255,255,255,0.45)" :
    saveState === "saving"                     ? "#FBBF24" :
    saveState === "save_error"                 ? "#D44C4C" :
    saveState === "stale_against_last_compile" ? "#FBBF24" :
    "rgba(255,255,255,0.25)";

  return (
    <div style={contextBarStyle}>
      <span style={ctxTitleStyle}>Research Lab</span>
      <div style={ctxItemsStyle}>
        <CtxBadge
          label="Connection"
          value={activeConnectionId ?? "— not selected"}
          dimmed={activeConnectionId === null}
        />
        <CtxBadge
          label="Dataset"
          value={activeDatasetId ?? "— not selected"}
          dimmed={activeDatasetId === null}
        />
        {/* A1-5: dimmed only when idle; error/warning state surfaces with colour */}
        <CtxBadge
          label="Validation"
          value={validationState}
          dimmed={validationState === "idle"}
          variant={validationState === "error" ? "error" : validationState === "warning" ? "warning" : undefined}
        />
        <CtxBadge
          label="Run"
          value={runState}
          dimmed={runState === "idle"}
          variant={runState === "failed" ? "error" : undefined}
        />
        {/* Phase 3A: save state badge — independent of compile/validation */}
        {isOnBuildTab && activeGraphId && (
          <div style={{ ...ctxBadgeStyle, borderColor: saveState === "save_error" ? "rgba(212,76,76,0.5)" : undefined }}>
            <span style={{ color: "var(--text-secondary)", fontSize: 11 }}>Save:</span>
            <span style={{ fontSize: 12, marginLeft: 4, color: saveLabelColor, fontWeight: saveState === "save_error" ? 600 : 400 }}>
              {saveLabel}
            </span>
          </div>
        )}
        {lastCompileResult && (
          <CtxBadge
            label="Compiled"
            value={`Strategy v${lastCompileResult.strategyVersion}`}
            dimmed={false}
          />
        )}
      </div>

      {/* Phase 3A: save error toast (non-silent) */}
      {showSaveErrorToast && (
        <div style={{
          position: "fixed",
          top: 56,
          right: 16,
          zIndex: 9999,
          background: "rgba(14,18,24,0.97)",
          border: "1px solid rgba(212,76,76,0.5)",
          borderRadius: 6,
          padding: "7px 14px",
          fontSize: 12,
          color: "#D44C4C",
          boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontFamily: "inherit",
        }}>
          <span>⚠</span>
          <span>Auto-save failed — your changes may not be persisted.</span>
          <button
            onClick={() => setShowSaveErrorToast(false)}
            style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(255,255,255,0.3)", fontSize: 13, padding: 0, marginLeft: 4 }}
          >✕</button>
        </div>
      )}

      {/* Phase 4B: Compile & Save button — only meaningful on Build tab */}
      {isOnBuildTab && (
        <button
          onClick={handleCompile}
          disabled={compileDisabled}
          style={{
            marginLeft: "auto",
            padding: "5px 14px",
            fontSize: 12,
            fontWeight: 600,
            background: compileDisabled ? "rgba(255,255,255,0.06)" : compileBtnColor,
            border: "none",
            borderRadius: 5,
            color: compileDisabled ? "rgba(255,255,255,0.3)" : "#fff",
            cursor: compileDisabled ? "not-allowed" : "pointer",
            transition: "background 0.15s",
            flexShrink: 0,
            fontFamily: "inherit",
          }}
        >
          {compileLabel}
        </button>
      )}
    </div>
  );
}

// A1-5: variant prop drives badge colour for error/warning states
const BADGE_VARIANT_COLOR: Record<string, string> = {
  error: "#D44C4C",
  warning: "#FBBF24",
};

function CtxBadge({
  label,
  value,
  dimmed,
  variant,
}: {
  label: string;
  value: string;
  dimmed?: boolean;
  variant?: "error" | "warning";
}) {
  const valueColor = variant
    ? BADGE_VARIANT_COLOR[variant]
    : dimmed
    ? "var(--text-secondary)"
    : "var(--text-primary)";

  return (
    <div
      style={{
        ...ctxBadgeStyle,
        borderColor: variant === "error" ? "rgba(212,76,76,0.4)" : variant === "warning" ? "rgba(251,191,36,0.3)" : undefined,
      }}
    >
      <span style={{ color: "var(--text-secondary)", fontSize: 11 }}>{label}:</span>
      <span
        style={{
          fontSize: 12,
          marginLeft: 4,
          color: valueColor,
          fontWeight: variant ? 600 : 400,
        }}
      >
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inspector placeholder panel (right side)
// ---------------------------------------------------------------------------

function InspectorPlaceholder() {
  return (
    <div style={inspectorStyle}>
      <div style={panelLabelStyle}>Inspector</div>
      <p style={placeholderTextStyle}>
        Select a node or block to inspect its properties.
      </p>
      <p style={{ ...placeholderTextStyle, marginTop: 8, fontSize: 11 }}>
        (Available in Phase 3)
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Diagnostics drawer placeholder (bottom)
// ---------------------------------------------------------------------------

function DiagnosticsPlaceholder() {
  return (
    <div style={diagnosticsStyle}>
      <span style={panelLabelStyle}>Diagnostics</span>
      <span style={{ ...placeholderTextStyle, marginLeft: 12 }}>
        No issues detected.
      </span>
      <span style={{ ...placeholderTextStyle, fontSize: 11, marginLeft: 4 }}>
        (Available in Phase 3)
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Lab Shell — Phase 1B: route-aware tabs + store-wired Context Bar
// ---------------------------------------------------------------------------

interface LabShellProps {
  children: React.ReactNode;
}

export function LabShell({ children }: LabShellProps) {
  const pathname  = usePathname();
  const activeTab = getActiveTab(pathname);

  return (
    <div style={shellStyle}>
      {/* Top Context Bar — reads from useLabGraphStore; Phase 4: Compile & Save button */}
      <LabContextBar activeTab={activeTab} />

      {/* Main resizable layout */}
      <Group orientation="vertical" style={{ flex: 1, minHeight: 0 }}>

        {/* Row: tabbed main area + right inspector */}
        <Panel minSize={20}>
          <Group orientation="horizontal">

            {/* Left/Main: tab bar + tab content (children from active route) */}
            <Panel minSize={30}>
              <div style={tabAreaStyle}>

                {/* Tab bar — Links for route-aware navigation */}
                <nav style={tabBarStyle} aria-label="Lab sections">
                  {TABS.map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                      <Link
                        key={tab.id}
                        href={tab.href}
                        role="tab"
                        aria-selected={isActive}
                        style={{
                          ...tabBtnStyle,
                          ...(isActive ? tabBtnActiveStyle : {}),
                        }}
                      >
                        {tab.label}
                      </Link>
                    );
                  })}
                </nav>

                {/* Tab content — provided by the active route */}
                <div style={tabContentStyle} role="tabpanel">
                  {children}
                </div>

              </div>
            </Panel>

            {/* Resize handle (horizontal) */}
            <Separator style={resizeHandleH} />

            {/* Right: Inspector placeholder */}
            <Panel defaultSize={22} minSize={8} collapsible>
              <InspectorPlaceholder />
            </Panel>

          </Group>
        </Panel>

        {/* Resize handle (vertical) */}
        <Separator style={resizeHandleV} />

        {/* Bottom: Diagnostics drawer placeholder */}
        <Panel defaultSize={8} minSize={4} collapsible>
          <DiagnosticsPlaceholder />
        </Panel>

      </Group>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const shellStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  height: "calc(100vh - var(--nav-height))",
  background: "var(--bg-primary)",
  overflow: "hidden",
};

const contextBarStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 20,
  padding: "0 20px",
  borderBottom: "1px solid var(--border)",
  background: "var(--bg-secondary)",
  flexShrink: 0,
  height: 44,
};

const ctxTitleStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: "var(--text-primary)",
  flexShrink: 0,
  paddingRight: 8,
  borderRight: "1px solid var(--border)",
};

const ctxItemsStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  flex: 1,
  flexWrap: "wrap",
  alignItems: "center",
};

const ctxBadgeStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  padding: "2px 8px",
  background: "rgba(255,255,255,0.03)",
  borderRadius: 4,
  border: "1px solid var(--border)",
  whiteSpace: "nowrap",
};

const tabAreaStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  height: "100%",
  overflow: "hidden",
};

const tabBarStyle: React.CSSProperties = {
  display: "flex",
  borderBottom: "1px solid var(--border)",
  background: "var(--bg-secondary)",
  flexShrink: 0,
};

const tabBtnStyle: React.CSSProperties = {
  padding: "10px 18px",
  fontSize: 13,
  fontWeight: 500,
  background: "none",
  border: "none",
  borderBottom: "2px solid transparent",
  color: "var(--text-secondary)",
  cursor: "pointer",
  textDecoration: "none",
  display: "inline-block",
};

const tabBtnActiveStyle: React.CSSProperties = {
  color: "var(--text-primary)",
  borderBottom: "2px solid var(--accent)",
  background: "rgba(255,255,255,0.02)",
};

const tabContentStyle: React.CSSProperties = {
  flex: 1,
  overflow: "auto",
  minHeight: 0,
};

const inspectorStyle: React.CSSProperties = {
  height: "100%",
  borderLeft: "1px solid var(--border)",
  background: "var(--bg-secondary)",
  padding: "16px",
  overflow: "auto",
};

const diagnosticsStyle: React.CSSProperties = {
  height: "100%",
  borderTop: "1px solid var(--border)",
  background: "var(--bg-secondary)",
  padding: "0 16px",
  display: "flex",
  alignItems: "center",
};

const panelLabelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "var(--text-secondary)",
  flexShrink: 0,
};

const placeholderTextStyle: React.CSSProperties = {
  fontSize: 13,
  color: "var(--text-secondary)",
  lineHeight: 1.6,
};

const resizeHandleH: React.CSSProperties = {
  width: 4,
  background: "var(--border)",
  cursor: "col-resize",
  flexShrink: 0,
};

const resizeHandleV: React.CSSProperties = {
  height: 4,
  background: "var(--border)",
  cursor: "row-resize",
  flexShrink: 0,
};
