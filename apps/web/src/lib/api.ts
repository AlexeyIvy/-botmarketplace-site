const API_PREFIX = "/api/v1";

export function getWorkspaceId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("workspaceId");
}

export function setWorkspaceId(id: string) {
  localStorage.setItem("workspaceId", id);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("accessToken");
}

export function setToken(token: string) {
  localStorage.setItem("accessToken", token);
}

export function clearAuth() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("workspaceId");
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

// ---------------------------------------------------------------------------
// Token refresh — single in-flight request to avoid thundering herd
// ---------------------------------------------------------------------------

let refreshPromise: Promise<boolean> | null = null;

/** Attempt to refresh the access token using the httpOnly refresh cookie. */
async function tryRefreshToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_PREFIX}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (data.accessToken) {
        setToken(data.accessToken);
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function doFetch<T>(
  path: string,
  options: RequestInit,
  injectWorkspace: boolean,
): Promise<{ ok: true; data: T } | { ok: false; problem: ProblemDetails }> {
  const res = await rawFetch(path, options, injectWorkspace);

  // On 401, try to refresh the token and retry once
  if (res.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const retry = await rawFetch(path, options, injectWorkspace);
      return parseResponse<T>(retry);
    }
    // Refresh failed — session is truly expired
    clearAuth();
    return {
      ok: false,
      problem: {
        type: "session-expired",
        title: "Session expired",
        status: 401,
        detail: "Please log in again.",
      },
    };
  }

  return parseResponse<T>(res);
}

/** Execute a fetch with auth headers. */
async function rawFetch(
  path: string,
  options: RequestInit,
  injectWorkspace: boolean,
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body != null ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };
  if (injectWorkspace) {
    const workspaceId = getWorkspaceId();
    if (workspaceId) headers["X-Workspace-Id"] = workspaceId;
  }

  return fetch(`${API_PREFIX}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
}

/** Parse a non-401 response into our standard result type. */
async function parseResponse<T>(
  res: Response,
): Promise<{ ok: true; data: T } | { ok: false; problem: ProblemDetails }> {
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

  const text = await res.text();
  const data = text.length > 0 ? (JSON.parse(text) as T) : (undefined as T);
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
