"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setToken, setWorkspaceId } from "../factory/api";

const cardStyle: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "12px",
  padding: "40px",
  width: "100%",
  maxWidth: "400px",
};

const inputStyle: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  color: "var(--text-primary)",
  fontSize: "14px",
  padding: "10px 12px",
  width: "100%",
  outline: "none",
};

const btnStyle: React.CSSProperties = {
  background: "var(--accent)",
  border: "none",
  borderRadius: "6px",
  color: "#fff",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600,
  padding: "11px",
  width: "100%",
};

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? "Registration failed");
        return;
      }
      setToken(data.accessToken);
      if (data.workspaceId) setWorkspaceId(data.workspaceId);
      router.push("/factory");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "calc(100vh - var(--nav-height))",
        padding: "24px",
      }}
    >
      <div style={cardStyle}>
        <h1 style={{ fontSize: "22px", fontWeight: 700, marginBottom: "8px" }}>Create account</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "28px" }}>
          Get started with BotMarketplace
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "13px", color: "var(--text-secondary)", marginBottom: "6px" }}>
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={inputStyle}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", color: "var(--text-secondary)", marginBottom: "6px" }}>
              Password
              <span style={{ color: "var(--text-secondary)", fontWeight: 400, marginLeft: "8px" }}>
                (min. 8 characters)
              </span>
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={inputStyle}
            />
          </div>

          {error && (
            <p style={{ color: "#f85149", fontSize: "13px", background: "rgba(248,81,73,0.1)", padding: "10px 12px", borderRadius: "6px" }}>
              {error}
            </p>
          )}

          <button type="submit" disabled={loading} style={{ ...btnStyle, opacity: loading ? 0.6 : 1 }}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p style={{ marginTop: "20px", fontSize: "13px", color: "var(--text-secondary)", textAlign: "center" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--accent)" }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
