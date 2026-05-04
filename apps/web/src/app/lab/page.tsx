"use client";

import { useEffect, useState } from "react";
import { getWorkspaceId } from "../../lib/api";
import { AuthLabClassicMode, GuestLabClassicMode } from "./ClassicMode";

// Classic mode — default tab for /lab.
// The LabShell wrapper (tabs, context bar, inspector, diagnostics) is
// provided by layout.tsx; this page only returns the tab content.
//
// The Auth ↔ Guest split is decided by the presence of a workspaceId in
// localStorage, which is undefined on the server. Reading it directly at
// render time produced two completely different component trees on SSR
// (Guest, no workspace) vs hydration (Auth, workspace present) — a much
// larger DOM diff than a single conditional warning box, guaranteed to
// trigger React error #418 for any logged-in operator. Defer the read
// to a mount-time effect and render a tiny placeholder during the
// pre-mount window so SSR + first client render agree.
export default function LabPage() {
  const [mounted, setMounted] = useState(false);
  const [hasWorkspace, setHasWorkspace] = useState(false);

  useEffect(() => {
    setHasWorkspace(!!getWorkspaceId());
    setMounted(true);
  }, []);

  if (!mounted) {
    // Tiny non-committal placeholder. Same DOM on SSR and the first
    // client render, no localStorage read. The flicker is sub-frame on
    // hydration so operators don't see it; the React tree just resolves.
    return <div aria-hidden="true" style={{ minHeight: 1 }} />;
  }
  return hasWorkspace ? <AuthLabClassicMode /> : <GuestLabClassicMode />;
}
