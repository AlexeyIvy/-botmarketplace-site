"use client";

import { useEffect } from "react";

/**
 * Global error boundary (Next.js App Router).
 * Catches unhandled errors from any page and displays a recovery UI.
 * Reports errors to the backend for monitoring (Task #23).
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Report to backend (best-effort, never throw)
    reportError(error).catch(() => {});
  }, [error]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "60vh",
        padding: "2rem",
        textAlign: "center",
        color: "var(--text-primary)",
      }}
    >
      <h2 style={{ fontSize: "1.5rem", marginBottom: "0.75rem" }}>
        Something went wrong
      </h2>
      <p
        style={{
          color: "var(--text-secondary)",
          marginBottom: "1.5rem",
          maxWidth: "480px",
        }}
      >
        An unexpected error occurred. You can try again, or go back to the
        dashboard.
      </p>
      {process.env.NODE_ENV !== "production" && (
        <pre
          style={{
            background: "var(--bg-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            padding: "1rem",
            marginBottom: "1.5rem",
            maxWidth: "600px",
            overflow: "auto",
            fontSize: "0.8rem",
            textAlign: "left",
            color: "var(--text-secondary)",
          }}
        >
          {error.message}
          {error.digest && `\nDigest: ${error.digest}`}
        </pre>
      )}
      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button
          onClick={reset}
          style={{
            padding: "0.5rem 1.25rem",
            background: "var(--accent)",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "0.9rem",
          }}
        >
          Try again
        </button>
        <a
          href="/"
          style={{
            padding: "0.5rem 1.25rem",
            background: "var(--bg-secondary)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            textDecoration: "none",
            fontSize: "0.9rem",
          }}
        >
          Go to dashboard
        </a>
      </div>
    </div>
  );
}

async function reportError(error: Error & { digest?: string }) {
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
    await fetch(`${apiBase}/api/v1/client-errors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack?.slice(0, 2000),
        digest: error.digest,
        url: typeof window !== "undefined" ? window.location.href : undefined,
        userAgent:
          typeof navigator !== "undefined" ? navigator.userAgent : undefined,
        timestamp: new Date().toISOString(),
      }),
    });
  } catch {
    // Swallow — error reporting itself must never crash
  }
}
