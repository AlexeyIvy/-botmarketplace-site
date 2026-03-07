"use client";

import { getWorkspaceId } from "../../lib/api";
import { AuthLabClassicMode, GuestLabClassicMode } from "./ClassicMode";

// Classic mode — default tab for /lab.
// The LabShell wrapper (tabs, context bar, inspector, diagnostics) is
// provided by layout.tsx; this page only returns the tab content.
export default function LabPage() {
  const hasWorkspace = !!getWorkspaceId();
  return hasWorkspace ? <AuthLabClassicMode /> : <GuestLabClassicMode />;
}
