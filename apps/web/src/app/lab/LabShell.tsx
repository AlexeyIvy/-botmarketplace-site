"use client";

import { useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type LabTab = "classic" | "data" | "build" | "test";

const TABS: { id: LabTab; label: string }[] = [
  { id: "classic", label: "Classic mode" },
  { id: "data", label: "Data" },
  { id: "build", label: "Build" },
  { id: "test", label: "Test" },
];

// ---------------------------------------------------------------------------
// Context Bar — static placeholder (Phase 1A)
// Phase 1B will wire this to useLabGraphStore
// ---------------------------------------------------------------------------

function LabContextBar() {
  return (
    <div style={contextBarStyle}>
      <span style={ctxTitleStyle}>Research Lab</span>
      <div style={ctxItemsStyle}>
        <CtxBadge label="Connection" value="— not selected" />
        <CtxBadge label="Dataset" value="— not selected" />
        <CtxBadge label="Validation" value="idle" dimmed />
        <CtxBadge label="Run" value="idle" dimmed />
      </div>
    </div>
  );
}

function CtxBadge({ label, value, dimmed }: { label: string; value: string; dimmed?: boolean }) {
  return (
    <div style={ctxBadgeStyle}>
      <span style={{ color: "var(--text-secondary)", fontSize: 11 }}>{label}:</span>
      <span style={{
        fontSize: 12,
        marginLeft: 4,
        color: dimmed ? "var(--text-secondary)" : "var(--text-primary)",
      }}>
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
// Placeholder tab content
// ---------------------------------------------------------------------------

function PlaceholderTab({ title, text }: { title: string; text: string }) {
  return (
    <div style={{ padding: "48px 40px" }}>
      <h2 style={{ fontSize: 18, marginBottom: 12, color: "var(--text-primary)" }}>{title}</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.6 }}>{text}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Lab Shell — Phase 1A multi-panel layout
// ---------------------------------------------------------------------------

interface LabShellProps {
  classicContent: React.ReactNode;
}

export function LabShell({ classicContent }: LabShellProps) {
  const [activeTab, setActiveTab] = useState<LabTab>("classic");

  return (
    <div style={shellStyle}>
      {/* Top Context Bar — static placeholder */}
      <LabContextBar />

      {/* Main resizable layout */}
      <Group orientation="vertical" style={{ flex: 1, minHeight: 0 }}>

        {/* Row: tabbed main area + right inspector */}
        <Panel minSize={20}>
          <Group orientation="horizontal">

            {/* Left/Main: tab bar + tab content */}
            <Panel minSize={30}>
              <div style={tabAreaStyle}>

                {/* Tab bar */}
                <div style={tabBarStyle} role="tablist" aria-label="Lab sections">
                  {TABS.map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        role="tab"
                        aria-selected={isActive}
                        style={{
                          ...tabBtnStyle,
                          ...(isActive ? tabBtnActiveStyle : {}),
                        }}
                        onClick={() => setActiveTab(tab.id)}
                      >
                        {tab.label}
                      </button>
                    );
                  })}
                </div>

                {/* Tab content */}
                <div style={tabContentStyle} role="tabpanel">
                  {activeTab === "classic" && classicContent}
                  {activeTab === "data" && (
                    <PlaceholderTab
                      title="Data"
                      text="Dataset builder coming in Phase 2. You will be able to connect an exchange, select instruments, define timeframes and date ranges, and build reusable market datasets."
                    />
                  )}
                  {activeTab === "build" && (
                    <PlaceholderTab
                      title="Build"
                      text="Strategy canvas coming in Phase 3. You will be able to visually compose strategies from typed building blocks using a node-based editor."
                    />
                  )}
                  {activeTab === "test" && (
                    <PlaceholderTab
                      title="Test"
                      text="Test runner coming in Phase 5. You will be able to run reproducible backtests against explicit datasets with full diagnostics and equity curve."
                    />
                  )}
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
  transition: "color 0.15s, border-color 0.15s",
};

const tabBtnActiveStyle: React.CSSProperties = {
  color: "var(--text-primary)",
  borderBottomColor: "var(--accent)",
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
  transition: "background 0.15s",
};

const resizeHandleV: React.CSSProperties = {
  height: 4,
  background: "var(--border)",
  cursor: "row-resize",
  flexShrink: 0,
  transition: "background 0.15s",
};
