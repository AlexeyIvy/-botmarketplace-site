import { create } from "zustand";
import { temporal } from "zundo";
import type { Node, Edge, NodeChange, EdgeChange } from "@xyflow/react";
import { applyNodeChanges, applyEdgeChanges } from "@xyflow/react";
import { BLOCK_DEF_MAP, type LabNodeData } from "./build/blockDefs";
import { validateGraph, type ValidationIssue } from "./validationTypes";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ValidationState = "idle" | "ok" | "warning" | "error" | "stale";
export type RunState = "idle" | "running" | "done" | "failed";
export type CompileState = "idle" | "compiling" | "success" | "error";

/**
 * Phase 3A: Persistence lifecycle state.
 * Invariants (docs/24 §4):
 *   - saveState !== validationState (independent concerns)
 *   - saveState !== compileState (independent concerns)
 *   - dirty graph != invalid graph
 *   - dirty graph != non-compilable graph
 */
export type SaveState =
  | "clean"                     // persisted; matches DB
  | "dirty"                     // local mutations not yet saved
  | "saving"                    // PATCH in-flight
  | "save_error"                // last PATCH failed
  | "stale_against_last_compile"; // saved but graph changed since last compile

/** Issue returned by the server compile endpoint */
export interface ServerCompileIssue {
  severity: "error" | "warning";
  message: string;
  nodeId?: string;
}

/** Result stored after a successful compile */
export interface CompileResult {
  strategyVersionId: string;
  strategyVersion: number;
  compiledDsl: Record<string, unknown>;
  validationIssues: ServerCompileIssue[];
}

export type LabNode = Node<LabNodeData>;
export type LabEdge = Edge;

export interface LabGraphState {
  activeConnectionId: string | null;
  activeDatasetId: string | null;
  activeGraphId: string | null;
  validationState: ValidationState;
  runState: RunState;
  nodes: LabNode[];
  edges: LabEdge[];
  /** Phase 3C: in-memory validation issues; never persisted */
  validationIssues: ValidationIssue[];
  /** Phase 4: compile state */
  compileState: CompileState;
  /** Phase 4: last successful compile result */
  lastCompileResult: CompileResult | null;
  /** Phase 4: server-side issues from last compile attempt (mapped to nodes) */
  serverIssues: ServerCompileIssue[];
  /** Phase 3A: persistence lifecycle state (independent of validation/compile) */
  saveState: SaveState;
  /**
   * Phase 3A: true while hydrateGraph is running.
   * Prevents mutations during hydration from triggering autosave.
   * NOT tracked in undo history.
   */
  _hydrating: boolean;
}

interface LabGraphActions {
  setActiveConnectionId: (id: string | null) => void;
  setActiveDatasetId: (id: string | null) => void;
  setActiveGraphId: (id: string | null) => void;
  setValidationState: (state: ValidationState) => void;
  setRunState: (state: RunState) => void;
  // Phase 3A: React Flow change handlers
  onNodesChange: (changes: NodeChange<LabNode>[]) => void;
  onEdgesChange: (changes: EdgeChange<LabEdge>[]) => void;
  // Phase 3A: direct setters for undo/redo
  setNodes: (nodes: LabNode[]) => void;
  setEdges: (edges: LabEdge[]) => void;
  // Phase 3B: add a block node at a given canvas position
  addNode: (blockType: string, position: { x: number; y: number }) => void;
  // Phase 3B: update a single param on a node
  updateNodeParam: (nodeId: string, paramId: string, value: unknown) => void;
  // Phase 3B: mark direct target of removed edge as stale
  markDownstreamStale: (removedEdgeTargetId: string) => void;
  // Phase 3C: run graph validation and update validationIssues + validationState
  runValidation: () => void;
  // Phase 4: compile state setters
  setCompileState: (state: CompileState) => void;
  setLastCompileResult: (result: CompileResult | null) => void;
  setServerIssues: (issues: ServerCompileIssue[]) => void;
  // Phase 3A: persistence actions
  setSaveState: (state: SaveState) => void;
  /**
   * Hydrate the store from a persisted graph record.
   * Sets _hydrating = true, restores nodes/edges/activeGraphId,
   * then sets _hydrating = false. Does NOT schedule autosave.
   */
  hydrateGraph: (graphId: string, nodes: LabNode[], edges: LabEdge[]) => void;
  /**
   * Flush current graph to backend immediately (used before graph switch).
   * Returns true on success, false on failure.
   */
  saveGraphNow: () => Promise<boolean>;
}

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

const initialState: LabGraphState = {
  activeConnectionId: null,
  activeDatasetId: null,
  activeGraphId: null,
  validationState: "idle",
  runState: "idle",
  nodes: [],
  edges: [],
  validationIssues: [],
  compileState: "idle",
  lastCompileResult: null,
  serverIssues: [],
  saveState: "clean",
  _hydrating: false,
};

// ---------------------------------------------------------------------------
// ID generator
// ---------------------------------------------------------------------------

let _nodeSeq = 0;
function nextNodeId(): string {
  return `n${++_nodeSeq}_${Date.now()}`;
}

// ---------------------------------------------------------------------------
// Debounce timers — module-level refs
// ---------------------------------------------------------------------------

/** 500ms validation debounce — per §13.3 */
let _validationTimer: ReturnType<typeof setTimeout> | null = null;

function scheduleValidation(runValidationFn: () => void) {
  if (_validationTimer !== null) clearTimeout(_validationTimer);
  _validationTimer = setTimeout(() => {
    _validationTimer = null;
    runValidationFn();
  }, 500);
}

/** 1500ms auto-save debounce — Phase 3A */
let _saveTimer: ReturnType<typeof setTimeout> | null = null;

function scheduleAutoSave(saveNowFn: () => Promise<boolean>) {
  if (_saveTimer !== null) clearTimeout(_saveTimer);
  _saveTimer = setTimeout(() => {
    _saveTimer = null;
    saveNowFn().catch(() => {
      // failure is reflected in saveState; no unhandled rejection
    });
  }, 1500);
}

// ---------------------------------------------------------------------------
// Store — Phase 3A base + Phase 3B additions + Phase 3C validation + Phase 3A persistence
// zundo provides undo/redo history.
// ---------------------------------------------------------------------------

export const useLabGraphStore = create<LabGraphState & LabGraphActions>()(
  temporal(
    (set, get) => ({
      ...initialState,

      setActiveConnectionId: (id) => set({ activeConnectionId: id }),
      setActiveDatasetId: (id) => set({ activeDatasetId: id }),
      setActiveGraphId: (id) => set({ activeGraphId: id }),
      setValidationState: (state) => set({ validationState: state }),
      setRunState: (state) => set({ runState: state }),
      setSaveState: (state) => set({ saveState: state }),

      onNodesChange: (changes) => {
        set((state) => ({
          nodes: applyNodeChanges(changes, state.nodes),
        }));
        scheduleValidation(get().runValidation);
        if (!get()._hydrating) {
          set({ saveState: "dirty" });
          scheduleAutoSave(get().saveGraphNow);
        }
      },

      onEdgesChange: (changes) => {
        set((state) => ({
          edges: applyEdgeChanges(changes, state.edges),
        }));
        scheduleValidation(get().runValidation);
        if (!get()._hydrating) {
          set({ saveState: "dirty" });
          scheduleAutoSave(get().saveGraphNow);
        }
      },

      setNodes: (nodes) => {
        set({ nodes });
        if (!get()._hydrating) {
          set({ saveState: "dirty" });
          scheduleAutoSave(get().saveGraphNow);
        }
      },

      setEdges: (edges) => {
        set({ edges });
        scheduleValidation(get().runValidation);
        if (!get()._hydrating) {
          set({ saveState: "dirty" });
          scheduleAutoSave(get().saveGraphNow);
        }
      },

      // Phase 3B — add block node to canvas
      addNode: (blockType, position) => {
        const def = BLOCK_DEF_MAP[blockType];
        if (!def) return;

        const params: Record<string, unknown> = {};
        for (const p of def.params) {
          params[p.id] = p.defaultValue;
        }

        const newNode: LabNode = {
          id: nextNodeId(),
          type: "strategyNode",
          position,
          data: { blockType, params, isStale: false },
        };

        set((state) => ({ nodes: [...state.nodes, newNode] }));
        scheduleValidation(get().runValidation);
        if (!get()._hydrating) {
          set({ saveState: "dirty" });
          scheduleAutoSave(get().saveGraphNow);
        }
      },

      // Phase 3B — update single param on a node
      updateNodeParam: (nodeId, paramId, value) => {
        set((state) => ({
          nodes: state.nodes.map((n) => {
            if (n.id !== nodeId) return n;
            return {
              ...n,
              data: { ...n.data, params: { ...n.data.params, [paramId]: value } },
            };
          }),
        }));
        scheduleValidation(get().runValidation);
        if (!get()._hydrating) {
          set({ saveState: "dirty" });
          scheduleAutoSave(get().saveGraphNow);
        }
      },

      // Phase 3B — mark direct target of removed edge as stale
      // Full downstream propagation is Phase 3C.
      markDownstreamStale: (removedEdgeTargetId) => {
        set((state) => ({
          nodes: state.nodes.map((n) => {
            if (n.id !== removedEdgeTargetId) return n;
            return { ...n, data: { ...n.data, isStale: true } };
          }),
        }));
        // markDownstreamStale is a visual marker only; does not dirty the graph
      },

      // Phase 4 — compile state setters
      setCompileState: (state) => set({ compileState: state }),
      setLastCompileResult: (result) => {
        set({ lastCompileResult: result });
        // After a successful compile, mark graph as stale-against-last-compile
        // only when it subsequently becomes dirty again (handled in mutations above).
        // On compile success, transition save state: if currently clean, mark
        // stale_against_last_compile will be set on next mutation. No change needed here.
      },
      setServerIssues: (issues) => set({ serverIssues: issues }),

      // Phase 3C — run validation synchronously, update issues + validationState
      runValidation: () => {
        const { nodes, edges } = get();
        const issues = validateGraph(nodes, edges);

        const hasErrors = issues.some((i) => i.severity === "error");
        const hasWarnings = issues.some((i) => i.severity === "warning");

        const newValidationState: ValidationState =
          nodes.length === 0
            ? "idle"
            : hasErrors
            ? "error"
            : hasWarnings
            ? "warning"
            : "ok";

        set({
          validationIssues: issues,
          validationState: newValidationState,
        });
      },

      // Phase 3A — hydrate from persisted graph record
      // Sets _hydrating = true to suppress autosave during restore
      hydrateGraph: (graphId, nodes, edges) => {
        set({ _hydrating: true });
        set({
          activeGraphId: graphId,
          nodes,
          edges,
          saveState: "clean",
        });
        set({ _hydrating: false });
        // Run validation once after hydration (no autosave)
        scheduleValidation(get().runValidation);
      },

      // Phase 3A — flush save immediately (called before graph switch or on demand)
      saveGraphNow: async () => {
        const { activeGraphId, nodes, edges, saveState } = get();
        if (!activeGraphId) return false;
        // Nothing to save if already clean
        if (saveState === "clean") return true;

        set({ saveState: "saving" });
        try {
          const res = await fetch(`/api/v1/lab/graphs/${activeGraphId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ graphJson: { nodes, edges } }),
          });
          if (!res.ok) {
            set({ saveState: "save_error" });
            return false;
          }
          set({ saveState: "clean" });
          return true;
        } catch {
          set({ saveState: "save_error" });
          return false;
        }
      },
    }),
    // zundo: only track graph state for undo/redo history.
    // saveState, _hydrating, validationIssues are excluded — derived or transient state.
    {
      partialize: (state) => ({
        activeGraphId: state.activeGraphId,
        validationState: state.validationState,
        nodes: state.nodes,
        edges: state.edges,
      }),
    }
  )
);
