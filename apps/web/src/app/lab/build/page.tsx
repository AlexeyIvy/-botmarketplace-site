"use client";

// ---------------------------------------------------------------------------
// Phase 3B — Build tab: palette + canvas + inspector
// Phase 3C — Validation drawer (§13.3, §28 Error presentation hierarchy)
// Phase 4B — DSL Preview tab + server-side error mapping in ValidationDrawer
// Per docs/23-lab-v2-ide-spec.md §6.3, §6.3.1, §6.4, §13.3, §28, Phase 4B
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
  ReactFlowProvider,
  addEdge,
  ConnectionMode,
  type Connection,
  type Node,
  type Edge,
  type OnConnectStart,
  type OnConnectEnd,
  type IsValidConnection,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useLabGraphStore } from "../useLabGraphStore";
import type { LabNode, LabEdge, ValidationState, ServerCompileIssue } from "../useLabGraphStore";
import type { ValidationIssue } from "../validationTypes";
import { listGraphs, createGraph, fetchGraph, patchGraph, type PersistedGraph } from "../labApi";
import { getTemplate, GRAPH_TEMPLATES } from "./templates";
import {
  BLOCK_DEF_MAP,
  PORT_TYPE_COLOR,
  isPortTypeCompatible,
  type PortDataType,
  type LabNodeData,
} from "./blockDefs";
import type { StrategyEdgeData } from "./edges/StrategyEdge";
import { ConnectionContextProvider, useConnectionContext } from "./ConnectionContext";
import StrategyNode from "./nodes/StrategyNode";
import StrategyEdge from "./edges/StrategyEdge";
import BlockPalette from "./BlockPalette";
import InspectorPanel from "./InspectorPanel";
import JsonHighlight from "./JsonHighlight";

// ---------------------------------------------------------------------------
// React Flow node/edge type registrations
// ---------------------------------------------------------------------------

const nodeTypes = { strategyNode: StrategyNode };
const edgeTypes = { strategyEdge: StrategyEdge };

// ---------------------------------------------------------------------------
// Cycle detection — DFS to check if adding source→target creates a cycle
// ---------------------------------------------------------------------------

function wouldCreateCycle(
  nodes: Node[],
  edges: Edge[],
  sourceNodeId: string,
  targetNodeId: string
): boolean {
  const adj: Record<string, string[]> = {};
  for (const n of nodes) adj[n.id] = [];
  for (const e of edges) {
    adj[e.source] = adj[e.source] ?? [];
    adj[e.source].push(e.target);
  }
  adj[sourceNodeId] = adj[sourceNodeId] ?? [];
  adj[sourceNodeId].push(targetNodeId);

  const visited = new Set<string>();
  const stack = [targetNodeId];
  while (stack.length > 0) {
    const cur = stack.pop()!;
    if (cur === sourceNodeId) return true;
    if (visited.has(cur)) continue;
    visited.add(cur);
    for (const next of adj[cur] ?? []) stack.push(next);
  }
  return false;
}

// ---------------------------------------------------------------------------
// Simple inline toast — no external dependency
// Per §6.3.1: "Toast notification (top-right, 3s, dismissable)"
// ---------------------------------------------------------------------------

interface ToastMessage {
  id: number;
  text: string;
}
let _toastSeq = 0;

function Toast({ message, onDone }: { message: ToastMessage; onDone: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDone, 3000);
    return () => clearTimeout(timer);
  }, [onDone]);

  return (
    <div
      style={{
        background: "rgba(14,18,24,0.95)",
        border: "1px solid rgba(212,76,76,0.45)",
        borderRadius: 6,
        padding: "7px 12px",
        fontSize: 11,
        color: "rgba(255,255,255,0.85)",
        boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        gap: 8,
        maxWidth: 300,
        fontFamily: "inherit",
      }}
    >
      <span style={{ color: "#D44C4C", fontSize: 13 }}>⚠</span>
      {message.text}
      <button
        onClick={onDone}
        style={{
          marginLeft: "auto",
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "rgba(255,255,255,0.3)",
          fontSize: 13,
          lineHeight: 1,
          padding: 0,
          flexShrink: 0,
        }}
      >
        ✕
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ValidationDrawer — Phase 3C
// Per §13.3 + §28 (Level 5: bottom drawer, persistent, clickable to focus node)
// ---------------------------------------------------------------------------

interface ValidationDrawerProps {
  issues: ValidationIssue[];
  validationState: ValidationState;
  /** Phase 4B: server-side compile issues to show alongside client-side issues */
  serverIssues?: ServerCompileIssue[];
}

function ValidationDrawer({ issues, validationState, serverIssues = [] }: ValidationDrawerProps) {
  const [open, setOpen] = useState(true);
  const nodes = useLabGraphStore((s) => s.nodes);
  const setNodes = useLabGraphStore((s) => s.setNodes);
  const { setCenter } = useReactFlow();

  const errorCount = issues.filter((i) => i.severity === "error").length + serverIssues.filter((i) => i.severity === "error").length;
  const warnCount = issues.filter((i) => i.severity === "warning").length + serverIssues.filter((i) => i.severity === "warning").length;

  const statusColor =
    validationState === "ok"
      ? "#52A97C"
      : validationState === "warning"
      ? "#FBBF24"
      : validationState === "error"
      ? "#D44C4C"
      : "rgba(255,255,255,0.25)";

  const statusLabel =
    validationState === "idle"
      ? "—"
      : validationState === "ok"
      ? "✓ Valid"
      : validationState === "warning"
      ? `${warnCount} warning${warnCount !== 1 ? "s" : ""}`
      : errorCount > 0 && warnCount > 0
      ? `${errorCount} error${errorCount !== 1 ? "s" : ""} · ${warnCount} warning${warnCount !== 1 ? "s" : ""}`
      : `${errorCount} error${errorCount !== 1 ? "s" : ""}`;

  const focusNode = useCallback(
    (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId);
      if (!node) return;
      // Select the node and center canvas on it
      setNodes(nodes.map((n) => ({ ...n, selected: n.id === nodeId })));
      setCenter(node.position.x + 70, node.position.y + 40, {
        zoom: 1.5,
        duration: 400,
      });
    },
    [nodes, setNodes, setCenter]
  );

  return (
    <div
      style={{
        background: "rgba(10,14,20,0.97)",
        borderTop: "1px solid rgba(255,255,255,0.07)",
        flexShrink: 0,
        maxHeight: open ? 200 : 28,
        overflow: "hidden",
        transition: "max-height 0.2s ease",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Drawer header — always visible, acts as tab */}
      <div
        onClick={() => setOpen((v) => !v)}
        style={{
          height: 28,
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "0 12px",
          cursor: "pointer",
          userSelect: "none",
          flexShrink: 0,
          borderBottom: open ? "1px solid rgba(255,255,255,0.05)" : "none",
        }}
      >
        <span
          style={{
            fontSize: 10,
            color: "rgba(255,255,255,0.35)",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          Validation
        </span>
        <span
          style={{ fontSize: 11, color: statusColor, fontWeight: 600, lineHeight: 1 }}
        >
          {statusLabel}
        </span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: 10,
            color: "rgba(255,255,255,0.2)",
          }}
        >
          {open ? "▼" : "▲"}
        </span>
      </div>

      {/* Issue list */}
      <div style={{ overflowY: "auto", flex: 1 }}>
        {/* Phase 4B: server-side compile issues */}
        {serverIssues.length > 0 && (
          <div style={{ padding: "4px 12px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Server (compile)
            </span>
            {serverIssues.map((issue, idx) => (
              <div
                key={`srv_${idx}`}
                onClick={() => issue.nodeId && focusNode(issue.nodeId)}
                role={issue.nodeId ? "button" : undefined}
                tabIndex={issue.nodeId ? 0 : undefined}
                onKeyDown={(e) => {
                  if (issue.nodeId && (e.key === "Enter" || e.key === " ")) focusNode(issue.nodeId);
                }}
                style={{
                  display: "flex", alignItems: "flex-start", gap: 8,
                  padding: "4px 0", cursor: issue.nodeId ? "pointer" : "default",
                }}
              >
                <span style={{ fontSize: 12, color: issue.severity === "error" ? "#D44C4C" : "#FBBF24", flexShrink: 0, lineHeight: 1.4 }}>
                  {issue.severity === "error" ? "⊗" : "⚠"}
                </span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.65)", lineHeight: 1.4 }}>
                  {issue.message}
                  {issue.nodeId && <span style={{ marginLeft: 5, fontSize: 10, color: "rgba(255,255,255,0.25)" }}>↗ focus</span>}
                </span>
              </div>
            ))}
          </div>
        )}
        {issues.length === 0 && serverIssues.length === 0 ? (
          <div
            style={{
              padding: "8px 12px",
              fontSize: 11,
              color:
                validationState === "idle"
                  ? "rgba(255,255,255,0.25)"
                  : "#52A97C",
              lineHeight: 1.5,
            }}
          >
            {validationState === "idle"
              ? "Add blocks to the canvas to begin validation."
              : "✓ Graph is valid. All required blocks are present and connected."}
          </div>
        ) : (
          issues.map((issue) => (
            <div
              key={issue.id}
              onClick={() => issue.nodeId && focusNode(issue.nodeId)}
              role={issue.nodeId ? "button" : undefined}
              tabIndex={issue.nodeId ? 0 : undefined}
              onKeyDown={(e) => {
                if (issue.nodeId && (e.key === "Enter" || e.key === " ")) {
                  focusNode(issue.nodeId);
                }
              }}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 8,
                padding: "5px 12px",
                cursor: issue.nodeId ? "pointer" : "default",
                transition: "background 0.1s",
              }}
              onMouseEnter={(e) => {
                if (issue.nodeId)
                  (e.currentTarget as HTMLDivElement).style.background =
                    "rgba(255,255,255,0.04)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.background =
                  "transparent";
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  color: issue.severity === "error" ? "#D44C4C" : "#FBBF24",
                  flexShrink: 0,
                  lineHeight: 1.4,
                }}
              >
                {issue.severity === "error" ? "⊗" : "⚠"}
              </span>
              <span
                style={{
                  fontSize: 11,
                  color: "rgba(255,255,255,0.7)",
                  lineHeight: 1.4,
                }}
              >
                {issue.message}
                {issue.nodeId && (
                  <span
                    style={{
                      marginLeft: 5,
                      fontSize: 10,
                      color: "rgba(255,255,255,0.25)",
                    }}
                  >
                    ↗ focus
                  </span>
                )}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Canvas inner — must be inside ReactFlowProvider + ConnectionContextProvider
// ---------------------------------------------------------------------------

// PersistedGraph type imported from labApi.ts (A2-2)

function LabBuildCanvas() {
  const nodes = useLabGraphStore((s) => s.nodes);
  const edges = useLabGraphStore((s) => s.edges);
  const onNodesChange = useLabGraphStore((s) => s.onNodesChange);
  const onEdgesChange = useLabGraphStore((s) => s.onEdgesChange);
  const setEdges = useLabGraphStore((s) => s.setEdges);
  const addNodeToStore = useLabGraphStore((s) => s.addNode);
  const updateNodeParam = useLabGraphStore((s) => s.updateNodeParam);
  const markDownstreamStale = useLabGraphStore((s) => s.markDownstreamStale);
  // Phase 3C: validation state
  const validationIssues = useLabGraphStore((s) => s.validationIssues);
  const validationState = useLabGraphStore((s) => s.validationState);
  // Phase 4B: compile state + DSL preview
  const lastCompileResult = useLabGraphStore((s) => s.lastCompileResult);
  const serverIssues = useLabGraphStore((s) => s.serverIssues);
  const [buildView, setBuildView] = useState<"canvas" | "dsl">("canvas");
  // Phase 3A: graph hydration + selector
  const activeGraphId = useLabGraphStore((s) => s.activeGraphId);
  const hydrateGraph = useLabGraphStore((s) => s.hydrateGraph);
  const saveGraphNow = useLabGraphStore((s) => s.saveGraphNow);
  const saveState = useLabGraphStore((s) => s.saveState);
  const [isInitializing, setIsInitializing] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const [availableGraphs, setAvailableGraphs] = useState<PersistedGraph[]>([]);
  const initRanRef = useRef(false);
  // B1-2: inline graph rename state
  const [isRenaming, setIsRenaming] = useState(false);
  const [draftName, setDraftName] = useState("");

  const { undo, redo } = useLabGraphStore.temporal.getState();
  const { getNodes, getEdges, screenToFlowPosition, setNodes } = useReactFlow<
    LabNode,
    LabEdge
  >();

  const { setSourceType, setLastRejectionReason } = useConnectionContext();
  const lastRejectionRef = useRef<string | null>(null);

  // Phase 3A: on mount, load or create persisted graph draft
  useEffect(() => {
    // If store already has an activeGraphId (e.g. from a prior navigation), skip init
    if (activeGraphId !== null) return;
    // Guard against StrictMode double-invoke
    if (initRanRef.current) return;
    initRanRef.current = true;

    let cancelled = false;
    setIsInitializing(true);
    setInitError(null);

    (async () => {
      try {
        // Step 1: list workspace graphs (most-recent first) — A2-2: via labApi
        const graphs = await listGraphs();

        let graph: PersistedGraph;
        let allGraphs: PersistedGraph[];

        if (graphs.length > 0) {
          // Step 2a: hydrate from most recent graph
          graph = graphs[0];
          allGraphs = graphs;
        } else {
          // Step 2b: create first draft — A2-2: via labApi
          graph = await createGraph("Untitled Graph", { nodes: [], edges: [] });
          allGraphs = [graph];
        }

        if (cancelled) return;

        // Step 3: store available graphs for selector, hydrate Zustand (suppresses autosave)
        setAvailableGraphs(allGraphs);
        const gj = graph.graphJson ?? { nodes: [], edges: [] };
        hydrateGraph(graph.id, gj.nodes ?? [], gj.edges ?? []);
      } catch (err) {
        if (!cancelled) {
          setInitError(err instanceof Error ? err.message : "Failed to load graph");
        }
      } finally {
        if (!cancelled) setIsInitializing(false);
      }
    })();

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Phase 3A corrective: minimal graph selector — flush + hydrate on switch
  // A2-2: uses labApi.fetchGraph instead of inline fetch
  const handleSelectGraph = useCallback(async (targetId: string) => {
    if (!targetId || targetId === activeGraphId) return;
    // Flush current dirty state before switching
    await saveGraphNow();
    // Fetch fresh data from API to avoid stale-cache bug (A→B→A scenario)
    try {
      const fresh = await fetchGraph(targetId);
      const gj = fresh.graphJson ?? { nodes: [], edges: [] };
      hydrateGraph(fresh.id, gj.nodes ?? [], gj.edges ?? []);
    } catch {
      // fetch failed — stay on current graph
    }
  }, [activeGraphId, saveGraphNow, hydrateGraph]);

  // A2-4: create a new empty graph, add to selector, switch to it
  const handleNewGraph = useCallback(async () => {
    await saveGraphNow();
    try {
      const newGraph = await createGraph("Untitled Graph", { nodes: [], edges: [] });
      setAvailableGraphs((prev) => [...prev, newGraph]);
      const gj = newGraph.graphJson ?? { nodes: [], edges: [] };
      hydrateGraph(newGraph.id, gj.nodes ?? [], gj.edges ?? []);
    } catch {
      // creation failed — stay on current graph
    }
  }, [saveGraphNow, hydrateGraph]);

  // B1-1: load a hardcoded template into the canvas
  const handleLoadTemplate = useCallback((templateId: string) => {
    const tpl = getTemplate(templateId);
    if (!tpl) return;
    const store = useLabGraphStore.getState();
    store.setNodes(tpl.nodes);
    store.setEdges(tpl.edges);
  }, []);

  // B1-2: commit inline rename via PATCH
  const commitRename = useCallback(async () => {
    if (!activeGraphId || !draftName.trim()) return;
    try {
      await patchGraph(activeGraphId, { name: draftName.trim() });
      setAvailableGraphs((prev) =>
        prev.map((g) => (g.id === activeGraphId ? { ...g, name: draftName.trim() } : g)),
      );
    } catch {
      // rename failed — revert silently
    }
  }, [activeGraphId, draftName]);

  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const showToast = useCallback((text: string) => {
    const id = ++_toastSeq;
    setToasts((prev) => [...prev, { id, text }]);
  }, []);
  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // ── isValidConnection ───────────────────────────────────────────────────
  // Per §6.3.1 + §9.1: enforce type compatibility + cycle detection.

  const isValidConnection: IsValidConnection<LabEdge> = useCallback(
    (connection): boolean => {
      const { source, sourceHandle, target, targetHandle } = connection;
      if (!source || !target || !sourceHandle || !targetHandle) {
        lastRejectionRef.current = "Connect an output to an input port";
        return false;
      }
      if (source === target) {
        lastRejectionRef.current = "Cannot connect a node to itself";
        return false;
      }

      const allNodes = getNodes();
      const sourceNodeData = allNodes.find((n) => n.id === source)?.data as
        | LabNodeData
        | undefined;
      const targetNodeData = allNodes.find((n) => n.id === target)?.data as
        | LabNodeData
        | undefined;
      if (!sourceNodeData || !targetNodeData) return false;

      const sourceDef = BLOCK_DEF_MAP[sourceNodeData.blockType];
      const targetDef = BLOCK_DEF_MAP[targetNodeData.blockType];
      if (!sourceDef || !targetDef) return false;

      const sourcePort = sourceDef.outputs.find((p) => p.id === sourceHandle);
      const targetPort = targetDef.inputs.find((p) => p.id === targetHandle);

      if (!sourcePort || !targetPort) {
        lastRejectionRef.current = "Connect an output to an input port";
        return false;
      }

      if (!isPortTypeCompatible(sourcePort.dataType, targetPort.dataType)) {
        lastRejectionRef.current = `Type mismatch: ${sourcePort.dataType} → ${targetPort.dataType} not compatible`;
        setLastRejectionReason(lastRejectionRef.current);
        return false;
      }

      if (wouldCreateCycle(allNodes, getEdges(), source, target)) {
        lastRejectionRef.current =
          "Cannot connect: this would create a cycle in the graph";
        setLastRejectionReason(lastRejectionRef.current);
        return false;
      }

      lastRejectionRef.current = null;
      setLastRejectionReason(null);
      return true;
    },
    [getNodes, getEdges, setLastRejectionReason]
  );

  // ── onConnectStart ──────────────────────────────────────────────────────

  const onConnectStart: OnConnectStart = useCallback(
    (_, { nodeId, handleId, handleType }) => {
      if (!nodeId || !handleId) return;
      const nodeData = getNodes().find((n) => n.id === nodeId)?.data as
        | LabNodeData
        | undefined;
      if (!nodeData) return;
      const def = BLOCK_DEF_MAP[nodeData.blockType];
      if (!def) return;
      const portType =
        handleType === "source"
          ? def.outputs.find((p) => p.id === handleId)?.dataType ?? null
          : def.inputs.find((p) => p.id === handleId)?.dataType ?? null;
      setSourceType(portType as PortDataType | null);
    },
    [getNodes, setSourceType]
  );

  // ── onConnect ───────────────────────────────────────────────────────────

  const onConnect = useCallback(
    (connection: Connection) => {
      const { source, sourceHandle, target, targetHandle } = connection;
      if (!source || !target || !sourceHandle || !targetHandle) return;

      const sourceNodeData = getNodes().find((n) => n.id === source)?.data as
        | LabNodeData
        | undefined;
      const sourceDef = sourceNodeData
        ? BLOCK_DEF_MAP[sourceNodeData.blockType]
        : undefined;
      const sourcePort = sourceDef?.outputs.find((p) => p.id === sourceHandle);
      const dataType: PortDataType | undefined = sourcePort?.dataType;

      // Cardinality: replace existing edge on occupied input (§6.3.1)
      const existingEdge = getEdges().find(
        (e) => e.target === target && e.targetHandle === targetHandle
      );
      let currentEdges = getEdges();
      if (existingEdge) {
        markDownstreamStale(target);
        currentEdges = currentEdges.filter((e) => e.id !== existingEdge.id);
      }

      const edgeData: StrategyEdgeData = {
        dataType: dataType ?? ("Series<number>" as PortDataType),
        isStale: false,
        isInvalid: false,
      };

      const newEdges = addEdge(
        {
          ...connection,
          type: "strategyEdge",
          data: edgeData,
          style: dataType
            ? { stroke: PORT_TYPE_COLOR[dataType] + "CC", strokeWidth: 2 }
            : undefined,
        },
        currentEdges
      );
      setEdges(newEdges);
    },
    [getNodes, getEdges, setEdges, markDownstreamStale]
  );

  // ── onConnectEnd ────────────────────────────────────────────────────────

  const onConnectEnd: OnConnectEnd = useCallback(
    (_event, connectionState) => {
      setSourceType(null);
      if (!connectionState?.isValid && lastRejectionRef.current) {
        const reason = lastRejectionRef.current;
        if (reason.includes("cycle")) {
          showToast(reason);
        }
        lastRejectionRef.current = null;
        setLastRejectionReason(null);
      }
    },
    [setSourceType, setLastRejectionReason, showToast]
  );

  // ── onEdgesDelete — mark downstream stale (§6.3.1) ─────────────────────

  const onEdgesDelete = useCallback(
    (deletedEdges: LabEdge[]) => {
      for (const edge of deletedEdges) {
        markDownstreamStale(edge.target);
      }
    },
    [markDownstreamStale]
  );

  // ── Keyboard shortcuts (A1-3: scoped to canvas focus) ───────────────────
  // Per docs/25 §A1-3: only fire when canvas container is focused or
  // contains focus. Prevents undo/redo/select-all from firing when a modal,
  // inspector input, or other non-canvas element is active.

  const canvasContainerRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const canvasEl = canvasContainerRef.current;
      if (!canvasEl) return;
      // Only act when canvas container is focused or contains focus
      if (
        !canvasEl.contains(document.activeElement) &&
        document.activeElement !== document.body
      ) {
        return;
      }

      const meta = e.metaKey || e.ctrlKey;
      if (meta && e.key === "z" && !e.shiftKey) {
        e.preventDefault(); undo(); return;
      }
      if (meta && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
        e.preventDefault(); redo(); return;
      }
      if (meta && e.key === "a") {
        e.preventDefault();
        setNodes(getNodes().map((n) => ({ ...n, selected: true })));
        return;
      }
      // Cmd+Shift+F → focus palette search (§6.3)
      if (meta && e.shiftKey && e.key === "F") {
        e.preventDefault();
        document.getElementById("block-palette-search")?.focus();
        return;
      }
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

  // ── Drag-from-palette → drop on canvas ─────────────────────────────────

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const blockType = e.dataTransfer.getData("application/lab-block-type");
      if (!blockType) return;
      const pos = screenToFlowPosition({ x: e.clientX, y: e.clientY });
      addNodeToStore(blockType, pos);
    },
    [screenToFlowPosition, addNodeToStore]
  );

  // ── Add via palette +/double-click ──────────────────────────────────────

  const handleAddBlock = useCallback(
    (blockType: string) => {
      const cx = window.innerWidth / 2;
      const cy = window.innerHeight / 2;
      const pos = screenToFlowPosition({ x: cx, y: cy });
      addNodeToStore(blockType, {
        x: pos.x + (Math.random() - 0.5) * 120,
        y: pos.y + (Math.random() - 0.5) * 120,
      });
    },
    [screenToFlowPosition, addNodeToStore]
  );

  const selectedNodes = nodes.filter((n) => n.selected);
  const selectedEdges = edges.filter((e) => e.selected);

  // Phase 3A: loading overlay while hydrating
  if (isInitializing) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        background: "rgba(8,12,18,0.97)",
        color: "rgba(255,255,255,0.45)",
        fontSize: 13,
        gap: 10,
      }}>
        <span style={{ opacity: 0.6 }}>⋯</span>
        Loading graph…
      </div>
    );
  }

  if (initError) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        background: "rgba(8,12,18,0.97)",
        color: "#D44C4C",
        fontSize: 13,
        flexDirection: "column",
        gap: 8,
      }}>
        <span>Failed to load graph</span>
        <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 11 }}>{initError}</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", width: "100%", height: "100%", overflow: "hidden" }}>
      {/* A2-4 + B1-2: Graph selector with inline rename */}
      <div style={graphSelectorBarStyle}>
        <span style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", flexShrink: 0 }}>Graph:</span>
        <select
          value={activeGraphId ?? ""}
          onChange={(e) => { void handleSelectGraph(e.target.value); }}
          disabled={saveState === "saving" || isInitializing}
          style={graphSelectorStyle}
        >
          {availableGraphs.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
        {/* B1-2: inline editable graph name */}
        {isRenaming ? (
          <input
            autoFocus
            value={draftName}
            onChange={(e) => setDraftName(e.target.value)}
            onBlur={() => { void commitRename(); setIsRenaming(false); }}
            onKeyDown={(e) => {
              if (e.key === "Enter") { void commitRename(); setIsRenaming(false); }
              if (e.key === "Escape") setIsRenaming(false);
            }}
            style={renameInputStyle}
          />
        ) : (
          <span
            onDoubleClick={() => {
              const current = availableGraphs.find((g) => g.id === activeGraphId);
              setDraftName(current?.name ?? "Untitled Graph");
              setIsRenaming(true);
            }}
            style={graphNameLabelStyle}
            title="Double-click to rename"
          >
            {availableGraphs.find((g) => g.id === activeGraphId)?.name ?? ""}
          </span>
        )}
        <button
          onClick={() => { void handleNewGraph(); }}
          disabled={saveState === "saving" || isInitializing}
          style={{
            padding: "2px 8px",
            fontSize: 11,
            fontWeight: 600,
            background: "rgba(59,130,246,0.15)",
            border: "1px solid rgba(59,130,246,0.3)",
            borderRadius: 4,
            color: "#3B82F6",
            cursor: "pointer",
            fontFamily: "inherit",
            flexShrink: 0,
          }}
        >
          + New
        </button>
      </div>
      {/* Phase 4B: Build view tab switcher — Canvas | DSL Preview */}
      <div style={buildViewTabBarStyle}>
        <button
          onClick={() => setBuildView("canvas")}
          style={{
            ...buildViewTabStyle,
            ...(buildView === "canvas" ? buildViewTabActiveStyle : {}),
          }}
        >
          Canvas
        </button>
        <button
          onClick={() => setBuildView("dsl")}
          disabled={!lastCompileResult}
          style={{
            ...buildViewTabStyle,
            ...(buildView === "dsl" ? buildViewTabActiveStyle : {}),
            opacity: lastCompileResult ? 1 : 0.4,
            cursor: lastCompileResult ? "pointer" : "not-allowed",
          }}
          title={lastCompileResult ? "View generated DSL" : "Compile the graph first to see DSL preview"}
        >
          DSL Preview {lastCompileResult ? `(v${lastCompileResult.strategyVersion})` : ""}
        </button>
      </div>

      {/* Main content area */}
      {buildView === "dsl" && lastCompileResult ? (
        /* DSL Preview — read-only JSON view of compiled strategy */
        <div style={{ flex: 1, overflow: "auto", padding: 16, background: "rgba(8,12,18,0.98)" }}>
          <div style={{ marginBottom: 10, fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
            Strategy v{lastCompileResult.strategyVersion} — {lastCompileResult.strategyVersionId}
          </div>
          {/* A2-5: syntax-highlighted JSON via JsonHighlight + DOMPurify */}
          <JsonHighlight data={lastCompileResult.compiledDsl} />
        </div>
      ) : (
        /* Canvas view */
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left: Block Palette */}
          <div style={{ width: 180, flexShrink: 0, height: "100%" }}>
            <BlockPalette onAddBlock={handleAddBlock} />
          </div>

          {/* Center: React Flow Canvas + Validation Drawer */}
          <div
            style={{
              flex: 1,
              height: "100%",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* Canvas area — A1-3: ref + tabIndex for keyboard focus scoping */}
            <div
              ref={canvasContainerRef}
              tabIndex={0}
              style={{ flex: 1, position: "relative", overflow: "hidden", outline: "none" }}
              onDragOver={onDragOver}
              onDrop={onDrop}
            >
              {/* B1-1: Empty canvas onboarding — strategy template gallery */}
              {nodes.length === 0 && (
                <div style={emptyCanvasHintStyle}>
                  <p style={emptyCanvasHintTextStyle}>
                    Drag a block from the palette — or load a strategy template:
                  </p>
                  <div style={templateGalleryStyle}>
                    {GRAPH_TEMPLATES.map((tpl) => (
                      <button
                        key={tpl.id}
                        onClick={() => handleLoadTemplate(tpl.id)}
                        style={templateCardStyle}
                        title={tpl.description}
                      >
                        <span style={templateCardLabelStyle}>{tpl.label}</span>
                        <span style={templateCardDescStyle}>{tpl.description}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <ReactFlow<LabNode, LabEdge>
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onConnectStart={onConnectStart}
                onConnectEnd={onConnectEnd}
                onEdgesDelete={onEdgesDelete}
                isValidConnection={isValidConnection}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                deleteKeyCode={["Delete", "Backspace"]}
                selectionKeyCode="Shift"
                multiSelectionKeyCode={["Meta", "Control"]}
                connectionMode={ConnectionMode.Loose}
                edgesReconnectable
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

              {/* Toasts — top-right per §6.3.1 */}
              <div
                style={{
                  position: "absolute",
                  top: 12,
                  right: 12,
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                  zIndex: 100,
                  pointerEvents: "none",
                }}
              >
                {toasts.map((t) => (
                  <div key={t.id} style={{ pointerEvents: "all" }}>
                    <Toast message={t} onDone={() => dismissToast(t.id)} />
                  </div>
                ))}
              </div>
            </div>

            {/* Phase 3C + 4B: Validation Drawer — client + server issues */}
            <ValidationDrawer
              issues={validationIssues}
              validationState={validationState}
              serverIssues={serverIssues}
            />
          </div>

          {/* Right: Inspector Panel */}
          <div style={{ width: 220, flexShrink: 0, height: "100%" }}>
            <InspectorPanel
              selectedNodes={selectedNodes}
              selectedEdges={selectedEdges}
              allNodes={nodes}
              allEdges={edges}
              onParamChange={updateNodeParam}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Build page — wraps in ReactFlowProvider + ConnectionContextProvider
// ---------------------------------------------------------------------------

export default function LabBuildPage() {
  return (
    <ReactFlowProvider>
      <ConnectionContextProvider>
        <LabBuildCanvas />
      </ConnectionContextProvider>
    </ReactFlowProvider>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const minimapStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 6,
};

// Phase 3A corrective: graph selector bar
const graphSelectorBarStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "4px 10px",
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  background: "rgba(8,12,18,0.95)",
  flexShrink: 0,
};

const graphSelectorStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 4,
  color: "rgba(255,255,255,0.8)",
  fontSize: 12,
  padding: "2px 6px",
  fontFamily: "inherit",
  cursor: "pointer",
  outline: "none",
};

// Phase 4B: Build view tab bar (Canvas | DSL Preview)
const buildViewTabBarStyle: React.CSSProperties = {
  display: "flex",
  borderBottom: "1px solid rgba(255,255,255,0.07)",
  background: "rgba(10,14,20,0.98)",
  flexShrink: 0,
};

const buildViewTabStyle: React.CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  fontWeight: 500,
  background: "none",
  border: "none",
  borderBottom: "2px solid transparent",
  color: "rgba(255,255,255,0.4)",
  cursor: "pointer",
  fontFamily: "inherit",
};

const buildViewTabActiveStyle: React.CSSProperties = {
  color: "rgba(255,255,255,0.88)",
  borderBottom: "2px solid #3B82F6",
};

// B1-2: inline rename styles
const renameInputStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(59,130,246,0.5)",
  borderRadius: 4,
  color: "rgba(255,255,255,0.9)",
  fontSize: 12,
  padding: "2px 6px",
  fontFamily: "inherit",
  outline: "none",
  minWidth: 100,
};

const graphNameLabelStyle: React.CSSProperties = {
  fontSize: 12,
  color: "rgba(255,255,255,0.6)",
  cursor: "default",
  padding: "2px 4px",
  borderRadius: 3,
  userSelect: "none",
  borderBottom: "1px dashed rgba(255,255,255,0.15)",
};

// B1-1: empty canvas onboarding styles
const emptyCanvasHintStyle: React.CSSProperties = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  zIndex: 10,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 14,
  pointerEvents: "all",
};

const emptyCanvasHintTextStyle: React.CSSProperties = {
  fontSize: 13,
  color: "rgba(255,255,255,0.45)",
  textAlign: "center",
  lineHeight: 1.6,
  margin: 0,
};

const kbdStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 3,
  padding: "1px 5px",
  fontSize: 11,
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  color: "rgba(255,255,255,0.6)",
};

const templateGalleryStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 10,
  maxWidth: 760,
  width: "100%",
};

const templateCardStyle: React.CSSProperties = {
  padding: "12px 14px",
  fontSize: 12,
  textAlign: "left",
  background: "rgba(59,130,246,0.08)",
  border: "1px solid rgba(59,130,246,0.2)",
  borderRadius: 8,
  color: "#e0e0e0",
  cursor: "pointer",
  fontFamily: "inherit",
  display: "flex",
  flexDirection: "column",
  gap: 6,
  transition: "border-color 0.15s, background 0.15s",
};

const templateCardLabelStyle: React.CSSProperties = {
  fontWeight: 700,
  fontSize: 13,
  color: "#3B82F6",
};

const templateCardDescStyle: React.CSSProperties = {
  fontSize: 11,
  color: "rgba(255,255,255,0.45)",
  lineHeight: 1.4,
  overflow: "hidden",
  display: "-webkit-box",
  WebkitLineClamp: 2,
  WebkitBoxOrient: "vertical",
};
