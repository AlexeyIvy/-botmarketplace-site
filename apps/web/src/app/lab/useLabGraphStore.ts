import { create } from "zustand";
import { temporal } from "zundo";
import type { Node, Edge, NodeChange, EdgeChange } from "@xyflow/react";
import { applyNodeChanges, applyEdgeChanges } from "@xyflow/react";
import { BLOCK_DEF_MAP, type LabNodeData } from "./build/blockDefs";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ValidationState = "idle" | "ok" | "warning" | "error" | "stale";
export type RunState = "idle" | "running" | "done" | "failed";

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
// ID generator
// ---------------------------------------------------------------------------

let _nodeSeq = 0;
function nextNodeId(): string {
  return `n${++_nodeSeq}_${Date.now()}`;
}

// ---------------------------------------------------------------------------
// Store — Phase 3A base + Phase 3B additions
// zundo provides undo/redo history.
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
        set((state) => ({
          nodes: applyNodeChanges(changes, state.nodes),
        })),

      onEdgesChange: (changes) =>
        set((state) => ({
          edges: applyEdgeChanges(changes, state.edges),
        })),

      setNodes: (nodes) => set({ nodes }),
      setEdges: (edges) => set({ edges }),

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
      },
    }),
    // zundo: only track graph state for undo/redo history.
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
