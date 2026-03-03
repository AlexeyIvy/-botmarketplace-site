"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, apiFetchNoWorkspace, getToken } from "@/lib/api";
import { ActionPlanCard } from "./ActionPlanCard";
import type { ActionPlan } from "./ActionPlanCard";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// A chat entry is either a regular text message or a plan response
type ChatEntry =
  | { kind: "chat"; role: "user" | "assistant"; content: string }
  | { kind: "plan"; plan: ActionPlan };

type ChatMode = "explain" | "plan";

interface AIStatus {
  available: boolean;
  provider?: string;
  model?: string;
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const Z_CHAT = 1000;

const btnStyle: React.CSSProperties = {
  position: "fixed",
  bottom: "24px",
  right: "24px",
  zIndex: Z_CHAT,
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: "24px",
  padding: "10px 18px",
  fontSize: "14px",
  fontWeight: 600,
  cursor: "pointer",
  boxShadow: "0 2px 12px rgba(0,0,0,0.4)",
  display: "flex",
  alignItems: "center",
  gap: "6px",
};

const drawerStyle: React.CSSProperties = {
  position: "fixed",
  bottom: "80px",
  right: "24px",
  width: "380px",
  maxHeight: "560px",
  zIndex: Z_CHAT,
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: "12px",
  display: "flex",
  flexDirection: "column",
  boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
  overflow: "hidden",
};

const drawerHeaderStyle: React.CSSProperties = {
  padding: "10px 16px",
  borderBottom: "1px solid var(--border)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  background: "var(--bg-secondary)",
  flexShrink: 0,
};

const modeTabsStyle: React.CSSProperties = {
  display: "flex",
  gap: "4px",
};

const modeTabStyle = (active: boolean): React.CSSProperties => ({
  background: active ? "var(--accent)" : "transparent",
  color: active ? "#fff" : "var(--text-secondary)",
  border: active ? "none" : "1px solid var(--border)",
  borderRadius: "6px",
  padding: "4px 10px",
  fontSize: "12px",
  fontWeight: 600,
  cursor: "pointer",
});

const messagesStyle: React.CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "12px",
  display: "flex",
  flexDirection: "column",
  gap: "8px",
  minHeight: "200px",
};

function messageBubbleStyle(role: "user" | "assistant"): React.CSSProperties {
  return {
    maxWidth: "88%",
    padding: "8px 12px",
    borderRadius: "12px",
    fontSize: "13px",
    lineHeight: "1.5",
    wordBreak: "break-word",
    whiteSpace: "pre-wrap",
    alignSelf: role === "user" ? "flex-end" : "flex-start",
    background: role === "user" ? "var(--accent)" : "var(--bg-secondary)",
    color: role === "user" ? "#fff" : "var(--text-primary)",
    border: role === "user" ? "none" : "1px solid var(--border)",
  };
}

const inputAreaStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderTop: "1px solid var(--border)",
  display: "flex",
  gap: "8px",
  alignItems: "flex-end",
  flexShrink: 0,
};

const textareaStyle: React.CSSProperties = {
  flex: 1,
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  color: "var(--text-primary)",
  fontSize: "13px",
  padding: "8px 10px",
  resize: "none",
  fontFamily: "inherit",
  minHeight: "38px",
  maxHeight: "96px",
  overflowY: "auto",
  outline: "none",
};

const sendBtnStyle = (disabled: boolean): React.CSSProperties => ({
  background: disabled ? "var(--border)" : "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: "8px",
  padding: "8px 14px",
  fontSize: "13px",
  fontWeight: 600,
  cursor: disabled ? "not-allowed" : "pointer",
  flexShrink: 0,
  alignSelf: "flex-end",
});

const errorBannerStyle: React.CSSProperties = {
  padding: "8px 12px",
  background: "rgba(248,81,73,0.15)",
  borderTop: "1px solid rgba(248,81,73,0.3)",
  fontSize: "12px",
  color: "#f85149",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "8px",
  flexShrink: 0,
};

const sessionBannerStyle: React.CSSProperties = {
  padding: "16px",
  textAlign: "center",
  fontSize: "13px",
  color: "var(--text-secondary)",
  display: "flex",
  flexDirection: "column",
  gap: "10px",
  alignItems: "center",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ChatWidget() {
  const router = useRouter();
  const [aiAvailable, setAiAvailable] = useState<boolean | null>(null);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<ChatMode>("explain");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check AI availability on mount
  useEffect(() => {
    const token = getToken();
    if (!token) { setAiAvailable(false); return; }
    apiFetchNoWorkspace<AIStatus>("/ai/status").then((res) => {
      setAiAvailable(res.ok ? res.data.available : false);
    });
  }, []);

  // Scroll to bottom on new entries
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries, loading]);

  // Build plain ChatMessage[] for /ai/chat context (exclude plan entries)
  function chatHistory(): ChatMessage[] {
    return entries
      .filter((e): e is Extract<ChatEntry, { kind: "chat" }> => e.kind === "chat")
      .map((e) => ({ role: e.role, content: e.content }));
  }

  function handleError(status: number, detail?: string) {
    if (status === 401) { setSessionExpired(true); return; }
    if (status === 429) setError("Rate limit reached. Please wait before sending another message.");
    else if (status === 503) setError("AI is temporarily unavailable.");
    else if (status === 504) setError("AI request timed out. Please try again.");
    else setError(detail || "Something went wrong. Please try again.");
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    setEntries((prev) => [...prev, { kind: "chat", role: "user", content: text }]);
    setInput("");
    setError(null);
    setLoading(true);

    if (mode === "explain") {
      // Explain mode: /ai/chat — pass full chat history for context
      const history: ChatMessage[] = [...chatHistory(), { role: "user", content: text }];
      const res = await apiFetch<{ reply: string }>("/ai/chat", {
        method: "POST",
        body: JSON.stringify({ messages: history }),
      });
      setLoading(false);
      if (res.ok) {
        setEntries((prev) => [...prev, { kind: "chat", role: "assistant", content: res.data.reply }]);
      } else {
        handleError(res.problem.status, res.problem.detail);
      }
    } else {
      // Plan mode: /ai/plan — single message, returns ActionPlan
      const res = await apiFetch<ActionPlan>("/ai/plan", {
        method: "POST",
        body: JSON.stringify({ message: text }),
      });
      setLoading(false);
      if (res.ok) {
        setEntries((prev) => [...prev, { kind: "plan", plan: res.data }]);
      } else {
        handleError(res.problem.status, res.problem.detail);
      }
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  }

  if (!aiAvailable) return null;

  const placeholder = mode === "explain"
    ? "Ask about your runs, strategies, errors… (Enter)"
    : "Describe what you want to do… e.g. \"Create bot and start run\" (Enter)";

  return (
    <>
      {/* Floating button */}
      <button
        style={btnStyle}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close AI chat" : "Open AI chat"}
      >
        <span>⚡</span>
        <span>AI</span>
      </button>

      {/* Drawer */}
      {open && (
        <div style={drawerStyle} role="dialog" aria-label="AI Assistant">
          {/* Header with mode tabs */}
          <div style={drawerHeaderStyle}>
            <div style={modeTabsStyle}>
              <button
                style={modeTabStyle(mode === "explain")}
                onClick={() => setMode("explain")}
                title="Ask questions, get explanations"
              >
                Explain
              </button>
              <button
                style={modeTabStyle(mode === "plan")}
                onClick={() => setMode("plan")}
                title="Propose and confirm actions"
              >
                ⚡ Do
              </button>
            </div>
            <button
              onClick={() => setOpen(false)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", fontSize: "18px", lineHeight: 1 }}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          {/* Body */}
          {sessionExpired ? (
            <div style={sessionBannerStyle}>
              <span>Session expired. Please log in again.</span>
              <button
                onClick={() => router.push("/login")}
                style={{ ...sendBtnStyle(false), padding: "8px 20px" }}
              >
                Log in
              </button>
            </div>
          ) : (
            <>
              {/* Messages / Plan cards */}
              <div style={messagesStyle}>
                {entries.length === 0 && (
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", textAlign: "center", marginTop: "24px" }}>
                    {mode === "explain"
                      ? "Ask me about your runs, strategies, backtests, or errors."
                      : "Tell me what you\u2019d like to do and I\u2019ll propose an action plan."}
                  </p>
                )}
                {entries.map((entry, i) => {
                  if (entry.kind === "chat") {
                    return (
                      <div key={i} style={messageBubbleStyle(entry.role)}>
                        {entry.content}
                      </div>
                    );
                  }
                  // Plan entry — rendered as ActionPlanCard
                  return (
                    <div key={i} style={{ alignSelf: "stretch" }}>
                      <ActionPlanCard plan={entry.plan} />
                    </div>
                  );
                })}
                {loading && (
                  <div style={{ ...messageBubbleStyle("assistant"), color: "var(--text-secondary)" }}>
                    {mode === "plan" ? "Planning\u2026" : "Thinking\u2026"}
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Error banner */}
              {error && (
                <div style={errorBannerStyle}>
                  <span>{error}</span>
                  <button
                    onClick={() => setError(null)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "#f85149", fontSize: "16px" }}
                  >
                    ×
                  </button>
                </div>
              )}

              {/* Input */}
              <div style={inputAreaStyle}>
                <textarea
                  style={textareaStyle}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={placeholder}
                  rows={1}
                  maxLength={2000}
                  disabled={loading}
                />
                <button
                  style={sendBtnStyle(loading || !input.trim())}
                  onClick={() => void sendMessage()}
                  disabled={loading || !input.trim()}
                >
                  {mode === "plan" ? "Plan" : "Send"}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
