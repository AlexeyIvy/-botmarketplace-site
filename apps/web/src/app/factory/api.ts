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

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<{ ok: true; data: T } | { ok: false; problem: ProblemDetails }> {
  const workspaceId = getWorkspaceId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (workspaceId) {
    headers["X-Workspace-Id"] = workspaceId;
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
