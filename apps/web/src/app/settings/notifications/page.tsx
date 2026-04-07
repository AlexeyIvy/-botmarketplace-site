"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getToken, clearAuth } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NotifyJson {
  telegram?: {
    botToken: string;
    chatId: string;
    enabled: boolean;
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function NotificationSettingsPage() {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [enabled, setEnabled] = useState(true);
  const [botToken, setBotToken] = useState("");
  const [chatId, setChatId] = useState("");
  const [hasExisting, setHasExisting] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadSettings();
  }, [router]);

  async function loadSettings() {
    setLoading(true);
    const res = await apiFetch<{ notifyJson: NotifyJson | null }>("/user/notifications");
    setLoading(false);

    if (res.ok && res.data.notifyJson?.telegram) {
      const tg = res.data.notifyJson.telegram;
      setBotToken(tg.botToken);
      setChatId(tg.chatId);
      setEnabled(tg.enabled);
      setHasExisting(true);
    } else if (!res.ok && res.problem.status === 401) {
      clearAuth();
      router.push("/login");
    }
  }

  async function handleSave() {
    setError(null);
    setSuccess(null);
    setSaving(true);

    const res = await apiFetch<{ notifyJson: NotifyJson }>("/user/notifications", {
      method: "PUT",
      body: JSON.stringify({
        notifyJson: {
          telegram: {
            botToken,
            chatId,
            enabled,
          },
        },
      }),
    });

    setSaving(false);

    if (res.ok) {
      setSuccess("Settings saved");
      setHasExisting(true);
      // Update displayed token with redacted version
      if (res.data.notifyJson?.telegram?.botToken) {
        setBotToken(res.data.notifyJson.telegram.botToken);
      }
    } else {
      setError(res.problem.detail);
    }
  }

  async function handleTest() {
    setError(null);
    setSuccess(null);
    setTesting(true);

    const res = await apiFetch<{ success: boolean; message: string }>(
      "/user/notifications/test",
      { method: "POST" },
    );

    setTesting(false);

    if (res.ok) {
      setSuccess("Test message sent! Check your Telegram.");
    } else {
      setError(res.problem.detail);
    }
  }

  if (loading) {
    return (
      <div style={wrap}>
        <p style={loadingText}>Loading...</p>
      </div>
    );
  }

  return (
    <div style={wrap}>
      <h1 style={heading}>Notification Settings</h1>
      <p style={subtitle}>
        Configure Telegram notifications for bot events (failures, circuit breakers, timeouts).
        {" "}
        <button onClick={() => router.push("/settings")} style={linkBtn}>
          Back to Settings
        </button>
      </p>

      <div style={card}>
        <h2 style={cardTitle}>Telegram Bot</h2>
        <p style={helpText}>
          1. Create a bot via @BotFather on Telegram and get the bot token.
          <br />
          2. Start a chat with your bot, then use @userinfobot to get your chat ID.
        </p>

        <div style={formGroup}>
          <label style={label}>
            Bot Token
            <input
              type="text"
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              style={input}
              placeholder="123456:ABC-DEF..."
            />
          </label>
        </div>

        <div style={formGroup}>
          <label style={label}>
            Chat ID
            <input
              type="text"
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              style={input}
              placeholder="123456789"
            />
          </label>
        </div>

        <div style={formGroup}>
          <label style={checkboxLabel}>
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              style={checkbox}
            />
            Notifications enabled
          </label>
        </div>

        {error && <p style={errorText}>{error}</p>}
        {success && <p style={successText}>{success}</p>}

        <div style={actions}>
          <button
            onClick={handleSave}
            disabled={saving || !botToken || !chatId}
            style={{
              ...saveBtn,
              opacity: saving || !botToken || !chatId ? 0.6 : 1,
            }}
          >
            {saving ? "Saving..." : "Save"}
          </button>

          {hasExisting && (
            <button
              onClick={handleTest}
              disabled={testing}
              style={{
                ...testBtn,
                opacity: testing ? 0.6 : 1,
              }}
            >
              {testing ? "Sending..." : "Send Test"}
            </button>
          )}
        </div>
      </div>

      <div style={card}>
        <h2 style={cardTitle}>Events that trigger notifications</h2>
        <ul style={eventList}>
          <li>RUN_FAILED — Bot run crashed or failed to activate</li>
          <li>RUN_TIMED_OUT — Bot exceeded maximum run duration</li>
          <li>RUN_STOPPING — Circuit breaker triggered (consecutive failures or daily loss limit)</li>
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const wrap: React.CSSProperties = {
  maxWidth: 640,
  margin: "0 auto",
  padding: "48px 24px",
};

const heading: React.CSSProperties = {
  fontSize: 26,
  fontWeight: 700,
  marginBottom: 4,
  color: "var(--text-primary)",
};

const subtitle: React.CSSProperties = {
  fontSize: 14,
  color: "var(--text-secondary)",
  marginBottom: 24,
};

const loadingText: React.CSSProperties = {
  color: "var(--text-secondary)",
  textAlign: "center",
  padding: "40px 0",
};

const card: React.CSSProperties = {
  background: "var(--bg-card, #1c1c1e)",
  borderRadius: 12,
  border: "1px solid var(--border)",
  padding: "24px",
  marginBottom: 20,
};

const cardTitle: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: 12,
};

const helpText: React.CSSProperties = {
  fontSize: 13,
  color: "var(--text-secondary)",
  marginBottom: 20,
  lineHeight: 1.6,
};

const formGroup: React.CSSProperties = {
  marginBottom: 16,
};

const label: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  fontSize: 13,
  color: "var(--text-secondary)",
};

const input: React.CSSProperties = {
  padding: "8px 10px",
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "var(--bg-secondary, #2c2c2e)",
  color: "var(--text-primary)",
  fontSize: 14,
  width: "100%",
};

const checkboxLabel: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 14,
  color: "var(--text-primary)",
  cursor: "pointer",
};

const checkbox: React.CSSProperties = {
  width: 16,
  height: 16,
};

const errorText: React.CSSProperties = {
  color: "#f85149",
  fontSize: 14,
  marginBottom: 12,
};

const successText: React.CSSProperties = {
  color: "#3fb950",
  fontSize: 14,
  marginBottom: 12,
};

const actions: React.CSSProperties = {
  display: "flex",
  gap: 12,
};

const saveBtn: React.CSSProperties = {
  padding: "8px 20px",
  borderRadius: 6,
  border: "1px solid var(--accent)",
  background: "var(--accent)",
  color: "#fff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};

const testBtn: React.CSSProperties = {
  padding: "8px 20px",
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "transparent",
  color: "var(--text-primary)",
  fontSize: 14,
  cursor: "pointer",
};

const linkBtn: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--accent)",
  cursor: "pointer",
  textDecoration: "underline",
  fontSize: 14,
};

const eventList: React.CSSProperties = {
  margin: 0,
  padding: "0 0 0 20px",
  fontSize: 13,
  color: "var(--text-secondary)",
  lineHeight: 2,
};
