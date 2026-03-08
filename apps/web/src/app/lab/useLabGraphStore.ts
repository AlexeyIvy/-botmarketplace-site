import { create } from "zustand";
import { temporal } from "zundo";
import type { Node, Edge, NodeChange, EdgeChange } from "@xyflow/react";
import { applyNodeChanges, applyEdgeChanges } from "@xyflow/react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ValidationState = "idle" | "ok" | "warning" | "error" | "stale";
export type RunState = "idle" | "running" | "done" | "failed";

export interface LabGraphState {
  activeConnectionId: string | null;
  activeDatasetId: string | null;
  activeGraphId: string | null;
  validationState: ValidationState;
  runState: RunState;
  nodes: Node[];
  edges: Edge[];
}

interface LabGraphActions {
  setActiveConnectionId: (id: string | null) => void;
  setActiveDatasetId: (id: string | null) => void;
  setActiveGraphId: (id: string | null) => void;
  setValidationState: (state: ValidationState) => void;
  setRunState: (state: RunState) => void;
  // Phase 3A: React Flow change handlers
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  // Phase 3A: direct setters for undo/redo
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
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
};

// ---------------------------------------------------------------------------
// Store — Phase 3A
// zundo provides undo/redo history. React Flow types now replace unknown[].
// ---------------------------------------------------------------------------

export const useLabGraphStore = create<LabGraphState & LabGraphActions>()(
  temporal(
    (set) => ({
      ...initialState,
      setActiveConnectionId: (id) => set({ activeConnectionId: id }),
      setActiveDatasetId: (id) => set({ activeDatasetId: id }),
      setActiveGraphId: (id) => set({ activeGraphId: id }),
      setValidationState: (state) => set({ validationState: state }),
      setRunState: (state) => set({ runState: state }),
      onNodesChange: (changes) =>
        set((state) => ({ nodes: applyNodeChanges(changes, state.nodes) })),
      onEdgesChange: (changes) =>
        set((state) => ({ edges: applyEdgeChanges(changes, state.edges) })),
      setNodes: (nodes) => set({ nodes }),
      setEdges: (edges) => set({ edges }),
    }),
    // zundo options: only track graph state for undo/redo history.
    // Connection / dataset selection is excluded (navigation, not mutations).
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
