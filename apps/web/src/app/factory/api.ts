const API_PREFIX = "/api/v1";

export function getWorkspaceId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("workspaceId");
}

export function setWorkspaceId(id: string) {
  localStorage.setItem("workspaceId", id);
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

async function doFetch<T>(
  path: string,
  options: RequestInit,
  injectWorkspace: boolean,
): Promise<{ ok: true; data: T } | { ok: false; problem: ProblemDetails }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (injectWorkspace) {
    const workspaceId = getWorkspaceId();
    if (workspaceId) headers["X-Workspace-Id"] = workspaceId;
  }

  const res = await fetch(`${API_PREFIX}${path}`, { ...options, headers });

  if (!res.ok) {
    const contentType = res.headers.get("content-type") ?? "";
    if (contentType.includes("application/problem+json") || contentType.includes("application/json")) {
      const problem = (await res.json()) as ProblemDetails;
      return { ok: false, problem };
    }
    return {
      ok: false,
      problem: { type: "about:blank", title: "Error", status: res.status, detail: res.statusText },
    };
  }

  const data = (await res.json()) as T;
  return { ok: true, data };
}

/** Fetch with X-Workspace-Id header injected. */
export function apiFetch<T = unknown>(path: string, options: RequestInit = {}) {
  return doFetch<T>(path, options, true);
}

/** Fetch without X-Workspace-Id header (e.g. workspace creation). */
export function apiFetchNoWorkspace<T = unknown>(path: string, options: RequestInit = {}) {
  return doFetch<T>(path, options, false);
}
