import { create } from "zustand";
import { temporal } from "zundo";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ValidationState = "idle" | "ok" | "warning" | "error" | "stale";
export type RunState = "idle" | "running" | "done" | "failed";

// Node / Edge are typed as unknown here — Phase 3 will narrow these with
// React Flow types when the canvas is introduced.
export interface LabGraphState {
  activeConnectionId: string | null;
  activeDatasetId: string | null;
  activeGraphId: string | null;
  validationState: ValidationState;
  runState: RunState;
  nodes: unknown[];
  edges: unknown[];
}

interface LabGraphActions {
  setActiveConnectionId: (id: string | null) => void;
  setActiveDatasetId: (id: string | null) => void;
  setActiveGraphId: (id: string | null) => void;
  setValidationState: (state: ValidationState) => void;
  setRunState: (state: RunState) => void;
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
// Store — Phase 1B
// zundo provides undo/redo history wiring.
// Graph functionality (nodes / edges mutations) is deferred to Phase 3.
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
    }),
    // zundo options: only track the fields relevant to undo/redo graph history.
    // Connection / dataset selection is intentionally excluded (they are
    // navigation choices, not graph mutations).
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
