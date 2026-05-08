"use client";

import { WorkspaceGate } from "../../lib/workspace";
import { AuthLabClassicMode, GuestLabClassicMode } from "./ClassicMode";

// Classic mode — default tab for /lab.
// The LabShell wrapper (tabs, context bar, inspector, diagnostics) is
// provided by layout.tsx; this page only returns the tab content.
//
// The Auth ↔ Guest split is decided by the presence of a workspaceId in
// localStorage. The WorkspaceGate HOC defers that read into a mount-time
// effect so SSR and the first client render emit the same DOM (avoids
// React error #418 — see lib/workspace.tsx).
export default function LabPage() {
  return (
    <WorkspaceGate
      authed={<AuthLabClassicMode />}
      guest={<GuestLabClassicMode />}
    />
  );
}
