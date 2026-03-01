"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetchNoWorkspace, clearAuth, getToken } from "../../lib/api";

interface Me {
  id: string;
  email: string;
}

type Theme = "system" | "dark" | "light";

export default function SettingsPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    const stored = localStorage.getItem("theme") as Theme | null;
    if (stored === "system" || stored === "dark" || stored === "light") {
      setTheme(stored);
    }
    apiFetchNoWorkspace<Me>("/auth/me").then((res) => {
      setLoading(false);
      if (res.ok) {
        setMe(res.data);
      } else if (res.problem.status === 401) {
        setSessionExpired(true);
      } else {
        setError(`${res.problem.title}: ${res.problem.detail}`);
      }
    });
  }, [router]);

  function handleLogout() {
    clearAuth();
    router.push("/login");
  }

  function applyTheme(t: Theme) {
    localStorage.setItem("theme", t);
    setTheme(t);
    if (t === "light") {
      document.documentElement.classList.add("theme-light");
    } else if (t === "dark") {
      document.documentElement.classList.remove("theme-light");
    } else {
      // system: read matchMedia once, no subscription
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (prefersDark) {
        document.documentElement.classList.remove("theme-light");
      } else {
        document.documentElement.classList.add("theme-light");
      }
    }
  }

  if (loading && !sessionExpired) {
    return <div style={wrap}><p style={hint}>Loading...</p></div>;
  }

  if (sessionExpired) {
    return (
      <div style={wrap}>
        <div style={expiredBanner}>
          <span>Session expired. Please log in again.</span>
          <button onClick={() => router.push("/login")} style={expiredBtn}>Log in</button>
        </div>
      </div>
    );
  }

  return (
    <div style={wrap}>
      <h1 style={{ fontSize: 26, marginBottom: 24, fontWeight: 700 }}>Settings</h1>

      {/* Account block */}
      <section style={card}>
        <h2 style={sectionTitle}>Account</h2>

        {error && <p style={{ color: "#f85149", fontSize: 13, marginBottom: 12 }}>{error}</p>}

        <div style={field}>
          <span style={fieldLabel}>Email</span>
          <span style={fieldValue}>{me?.email ?? "—"}</span>
        </div>

        <div style={{ marginTop: 20 }}>
          <button onClick={handleLogout} style={logoutBtn}>
            Log out
          </button>
        </div>
      </section>

      {/* Appearance block */}
      <section style={card}>
        <h2 style={sectionTitle}>Appearance</h2>
        <div style={field}>
          <span style={fieldLabel}>Theme</span>
          <select
            value={theme}
            onChange={(e) => applyTheme(e.target.value as Theme)}
            style={themeSelect}
          >
            <option value="system">System</option>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const wrap: React.CSSProperties = {
  maxWidth: 600,
  margin: "0 auto",
  padding: "48px 24px",
};

const card: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: "20px 24px",
  marginBottom: 24,
};

const sectionTitle: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 600,
  marginBottom: 16,
  color: "var(--text-primary)",
};

const field: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  fontSize: 14,
};

const fieldLabel: React.CSSProperties = {
  color: "var(--text-secondary)",
  minWidth: 60,
};

const fieldValue: React.CSSProperties = {
  color: "var(--text-primary)",
  fontWeight: 500,
};

const logoutBtn: React.CSSProperties = {
  padding: "8px 20px",
  background: "transparent",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontSize: 13,
};

const themeSelect: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 13,
  padding: "6px 10px",
  cursor: "pointer",
};

const hint: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 13,
};

const expiredBanner: React.CSSProperties = {
  background: "#f85149",
  color: "#fff",
  padding: "14px 18px",
  borderRadius: 8,
  display: "flex",
  alignItems: "center",
  gap: 14,
  fontSize: 14,
};

const expiredBtn: React.CSSProperties = {
  background: "rgba(255,255,255,0.2)",
  border: "1px solid rgba(255,255,255,0.4)",
  borderRadius: 4,
  color: "#fff",
  cursor: "pointer",
  fontSize: 13,
  padding: "4px 12px",
};
