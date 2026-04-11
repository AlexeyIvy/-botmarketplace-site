// ---------------------------------------------------------------------------
// Phase A2-2 — Centralized lab graph API client
// Replaces all inline fetch("/api/v1/lab/graphs") calls in components.
// Uses apiFetch for automatic X-Workspace-Id injection + 401 handling.
// ---------------------------------------------------------------------------

import { apiFetch } from "@/lib/api";
import type { LabNode, LabEdge } from "./useLabGraphStore";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface GraphJson {
  nodes: LabNode[];
  edges: LabEdge[];
}

export interface PersistedGraph {
  id: string;
  name: string;
  graphJson: GraphJson | null;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** List all workspace graphs (most-recent first). */
export async function listGraphs(): Promise<PersistedGraph[]> {
  const res = await apiFetch<PersistedGraph[]>("/lab/graphs");
  if (!res.ok) throw new Error(res.problem.detail ?? "Failed to load graphs");
  return res.data;
}

/** Create a new graph with given name and initial JSON. */
export async function createGraph(
  name: string,
  graphJson: GraphJson,
): Promise<PersistedGraph> {
  const res = await apiFetch<PersistedGraph>("/lab/graphs", {
    method: "POST",
    body: JSON.stringify({ name, graphJson }),
  });
  if (!res.ok) throw new Error(res.problem.detail ?? "Failed to create graph");
  return res.data;
}

/** Patch an existing graph (name and/or graphJson). */
export async function patchGraph(
  id: string,
  payload: { name?: string; graphJson?: GraphJson },
): Promise<void> {
  const res = await apiFetch(`/lab/graphs/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`${res.problem.status}: ${res.problem.detail ?? "Failed to save graph"}`);
}

/** Fetch a single graph by ID. */
export async function fetchGraph(id: string): Promise<PersistedGraph> {
  const res = await apiFetch<PersistedGraph>(`/lab/graphs/${id}`);
  if (!res.ok) throw new Error(res.problem.detail ?? "Failed to fetch graph");
  return res.data;
}

/** Compile response shape (for internal use by LabShell). */
export type CompileResponse = {
  ok: true;
  data: {
    strategyVersionId: string;
    strategyVersion: number;
    graphVersionId: string;
    compiledDsl: Record<string, unknown>;
    validationIssues: Array<{ severity: "error" | "warning"; message: string; nodeId?: string }>;
  };
} | {
  ok: false;
  status: number;
  validationIssues?: Array<{ severity: "error" | "warning"; message: string; nodeId?: string }>;
};

/** Compile a graph against the backend. */
export async function compileGraph(
  graphId: string,
  graphJson: GraphJson,
  symbol: string,
  timeframe: string,
): Promise<CompileResponse> {
  const res = await apiFetch<{
    strategyVersionId: string;
    strategyVersion: number;
    graphVersionId: string;
    compiledDsl: Record<string, unknown>;
    validationIssues: Array<{ severity: "error" | "warning"; message: string; nodeId?: string }>;
  }>(`/lab/graphs/${graphId}/compile`, {
    method: "POST",
    body: JSON.stringify({ graphJson, symbol, timeframe }),
  });
  if (!res.ok) {
    // 422 means validation issues returned in problem body
    if (res.problem.status === 422) {
      const issues = (res.problem as unknown as Record<string, unknown>).validationIssues as
        Array<{ severity: "error" | "warning"; message: string; nodeId?: string }> | undefined;
      return { ok: false, status: 422, validationIssues: issues };
    }
    return { ok: false, status: res.problem.status };
  }
  return { ok: true, data: res.data };
}

// ---------------------------------------------------------------------------
// Task 26: Graph version governance API
// ---------------------------------------------------------------------------

/** Update label on a compiled graph version. */
export async function patchGraphVersion(
  id: string,
  payload: { label?: string | null },
): Promise<{ id: string; version: number; label: string | null; isBaseline: boolean }> {
  const res = await apiFetch<{ id: string; version: number; label: string | null; isBaseline: boolean }>(`/lab/graph-versions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(res.problem.detail ?? "Failed to update label");
  return res.data;
}

/** Toggle baseline on a compiled graph version. */
export async function setGraphVersionBaseline(
  id: string,
): Promise<{ id: string; version: number; label: string | null; isBaseline: boolean }> {
  const res = await apiFetch<{ id: string; version: number; label: string | null; isBaseline: boolean }>(`/lab/graph-versions/${id}/baseline`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(res.problem.detail ?? "Failed to set baseline");
  return res.data;
}
