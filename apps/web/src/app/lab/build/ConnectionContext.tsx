"use client";

// ---------------------------------------------------------------------------
// Phase 3B — Connection drag context
// Per §6.3.1: "Use a React context value (e.g., dragSourcePortType) that is
// set on onConnectStart and cleared on onConnectEnd."
// ---------------------------------------------------------------------------

import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";
import type { PortDataType } from "./blockDefs";

interface ConnectionDragState {
  sourceType: PortDataType | null;
  // Last rejection reason, used by onConnectEnd to render tooltip/toast
  lastRejectionReason: string | null;
}

interface ConnectionContextValue extends ConnectionDragState {
  setSourceType: (t: PortDataType | null) => void;
  setLastRejectionReason: (reason: string | null) => void;
}

const ConnectionContext = createContext<ConnectionContextValue>({
  sourceType: null,
  lastRejectionReason: null,
  setSourceType: () => undefined,
  setLastRejectionReason: () => undefined,
});

export function ConnectionContextProvider({ children }: { children: ReactNode }) {
  const [sourceType, setSourceType] = useState<PortDataType | null>(null);
  const [lastRejectionReason, setLastRejectionReason] = useState<string | null>(null);

  return (
    <ConnectionContext.Provider
      value={{ sourceType, lastRejectionReason, setSourceType, setLastRejectionReason }}
    >
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnectionContext() {
  return useContext(ConnectionContext);
}
