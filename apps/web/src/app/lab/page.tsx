"use client";

import { getWorkspaceId } from "../../lib/api";
import { LabShell } from "./LabShell";
import { AuthLabClassicMode, GuestLabClassicMode } from "./ClassicMode";

export default function LabPage() {
  const hasWorkspace = !!getWorkspaceId();

  if (!hasWorkspace) {
    // Guest mode: simple centred layout (no shell needed)
    return <GuestLabClassicMode />;
  }

  // Authenticated: full Lab v2 shell with Classic mode as default tab
  return (
    <LabShell classicContent={<AuthLabClassicMode />} />
  );
}
