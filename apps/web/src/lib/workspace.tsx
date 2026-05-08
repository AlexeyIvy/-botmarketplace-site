"use client";

import { useEffect, useState, type ReactNode } from "react";
import { getWorkspaceId } from "./api";

// ---------------------------------------------------------------------------
// Workspace mount-gate primitives
// ---------------------------------------------------------------------------
//
// `getWorkspaceId()` reads from `localStorage`, which is undefined on the
// server. Components that gate render output on its result therefore produce
// two completely different DOM trees on SSR (no workspace) and the first
// client render (workspace present), which trips React error #418
// hydration mismatch. PRs #371, #374, #375 each landed point-fixes for this
// exact bug class on individual pages.
//
// This module centralises the fix:
//   - `useWorkspaceMount()` returns `{ mounted, workspaceId }`. During SSR
//     and the first client render `mounted` is `false` and `workspaceId` is
//     `null`, so any UI gated on these values renders the same DOM as the
//     server. The mount-time `useEffect` then flips `mounted: true` and
//     loads the actual workspaceId from localStorage.
//   - `<WorkspaceGate authed={...} guest={...} />` builds on the hook for
//     the case where the entire page tree differs between authed and guest
//     visitors (pattern used by `/lab/page.tsx`).
//
// Use `useWorkspaceMount()` directly when the page renders a single tree
// with a conditional warning banner (pattern used by `/lab/library` and
// `/lab/funding`). Use `<WorkspaceGate>` when you need an authed/guest
// branch.
//
// Callers must NOT read `getWorkspaceId()` at render time. It remains safe
// inside event handlers and `useEffect` bodies (no SSR concern there).

export interface WorkspaceMountState {
  /**
   * `true` once the mount-time effect has run on the client. Stays `false`
   * during SSR and the first client render so SSR + hydration emit the same
   * DOM.
   */
  mounted: boolean;
  /** Active workspaceId from localStorage, or `null` if none / pre-mount. */
  workspaceId: string | null;
}

const INITIAL: WorkspaceMountState = { mounted: false, workspaceId: null };

export function useWorkspaceMount(): WorkspaceMountState {
  const [state, setState] = useState<WorkspaceMountState>(INITIAL);
  useEffect(() => {
    setState({ mounted: true, workspaceId: getWorkspaceId() });
  }, []);
  return state;
}

export interface WorkspaceGateProps {
  /** Subtree shown when a workspaceId is present (post-mount). */
  authed: ReactNode;
  /** Subtree shown when no workspaceId is set (post-mount). */
  guest: ReactNode;
  /**
   * Optional placeholder rendered during the pre-mount window. Defaults to
   * a 1px aria-hidden div — same DOM on SSR and the first client render so
   * hydration is byte-identical, and the operator never sees a flicker.
   */
  fallback?: ReactNode;
}

const DEFAULT_FALLBACK: ReactNode = (
  <div aria-hidden="true" style={{ minHeight: 1 }} />
);

export function WorkspaceGate({
  authed,
  guest,
  fallback = DEFAULT_FALLBACK,
}: WorkspaceGateProps) {
  const { mounted, workspaceId } = useWorkspaceMount();
  if (!mounted) return <>{fallback}</>;
  return <>{workspaceId ? authed : guest}</>;
}
