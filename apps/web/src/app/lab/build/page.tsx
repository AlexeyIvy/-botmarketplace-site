"use client";

import { useCallback, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useLabGraphStore } from "../useLabGraphStore";

// ---------------------------------------------------------------------------
// Canvas inner — must be inside ReactFlowProvider for useReactFlow()
// ---------------------------------------------------------------------------

function LabBuildCanvas() {
  const nodes = useLabGraphStore((s) => s.nodes);
  const edges = useLabGraphStore((s) => s.edges);
  const onNodesChange = useLabGraphStore((s) => s.onNodesChange);
  const onEdgesChange = useLabGraphStore((s) => s.onEdgesChange);

  const { undo, redo } = useLabGraphStore.temporal.getState();
  const { getNodes, setNodes } = useReactFlow();

  // ---------------------------------------------------------------------------
  // Keyboard shortcuts — Phase 3A base set
  // ---------------------------------------------------------------------------

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;

      // Cmd/Ctrl+Z → undo
      if (meta && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        undo();
        return;
      }

      // Cmd/Ctrl+Y or Cmd/Ctrl+Shift+Z → redo
      if (meta && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
        e.preventDefault();
        redo();
        return;
      }

      // Cmd/Ctrl+A → select all nodes
      if (meta && e.key === "a") {
        e.preventDefault();
        setNodes(getNodes().map((n) => ({ ...n, selected: true })));
        return;
      }

      // Escape → deselect all (React Flow handles this natively via deleteKeyCode
      // but we wire Escape for deselect explicitly for reliability)
      if (e.key === "Escape") {
        setNodes(getNodes().map((n) => ({ ...n, selected: false })));
        return;
      }
    },
    [undo, redo, getNodes, setNodes]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div style={canvasWrapperStyle}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        // Delete/Backspace removes selected nodes and edges natively
        deleteKeyCode={["Delete", "Backspace"]}
        // Escape deselects (also handled in our keydown for reliability)
        selectionKeyCode="Shift"
        multiSelectionKeyCode={["Meta", "Control"]}
        fitView
        colorMode="dark"
        proOptions={{ hideAttribution: false }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="rgba(255,255,255,0.08)"
        />
        <Controls />
        <MiniMap
          style={minimapStyle}
          nodeColor="rgba(255,255,255,0.15)"
          maskColor="rgba(0,0,0,0.5)"
        />
      </ReactFlow>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Build page — wraps canvas in ReactFlowProvider
// ---------------------------------------------------------------------------

export default function LabBuildPage() {
  return (
    <ReactFlowProvider>
      <LabBuildCanvas />
    </ReactFlowProvider>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const canvasWrapperStyle: React.CSSProperties = {
  width: "100%",
  height: "100%",
  background: "var(--bg-primary)",
};

const minimapStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 6,
};
