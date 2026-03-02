"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, apiFetchNoWorkspace, getToken } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

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
  width: "360px",
  maxHeight: "520px",
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
  padding: "12px 16px",
  borderBottom: "1px solid var(--border)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  background: "var(--bg-secondary)",
  fontSize: "14px",
  fontWeight: 600,
  color: "var(--text-primary)",
};

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
    maxWidth: "85%",
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
  const [aiAvailable, setAiAvailable] = useState<boolean | null>(null); // null = checking
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check AI availability on mount (no auth needed)
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setAiAvailable(false);
      return;
    }
    apiFetchNoWorkspace<AIStatus>("/ai/status").then((res) => {
      if (res.ok) {
        setAiAvailable(res.data.available);
      } else {
        setAiAvailable(false);
      }
    });
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setError(null);
    setLoading(true);

    const res = await apiFetch<{ reply: string }>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ messages: updated }),
    });

    setLoading(false);

    if (res.ok) {
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
    } else {
      if (res.problem.status === 401) {
        setSessionExpired(true);
        return;
      }
      if (res.problem.status === 429) {
        setError("Rate limit reached. Please wait a moment before sending another message.");
      } else if (res.problem.status === 503) {
        setError("AI is temporarily unavailable.");
      } else if (res.problem.status === 504) {
        setError("AI request timed out. Please try again.");
      } else {
        setError(res.problem.detail || "Something went wrong. Please try again.");
      }
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  }

  // Don't render if AI is unavailable or not yet checked
  if (!aiAvailable) return null;

  return (
    <>
      {/* Floating button */}
      <button
        style={btnStyle}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close AI chat" : "Open AI chat"}
      >
        <span>💬</span>
        <span>Chat</span>
      </button>

      {/* Drawer */}
      {open && (
        <div style={drawerStyle} role="dialog" aria-label="AI Assistant">
          {/* Header */}
          <div style={drawerHeaderStyle}>
            <span>AI Assistant</span>
            <button
              onClick={() => setOpen(false)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", fontSize: "18px", lineHeight: 1 }}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          {/* Session expired state */}
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
              {/* Messages */}
              <div style={messagesStyle}>
                {messages.length === 0 && (
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", textAlign: "center", marginTop: "24px" }}>
                    Ask me about your runs, strategies, backtests, or errors.
                  </p>
                )}
                {messages.map((msg, i) => (
                  <div key={i} style={messageBubbleStyle(msg.role)}>
                    {msg.content}
                  </div>
                ))}
                {loading && (
                  <div style={{ ...messageBubbleStyle("assistant"), color: "var(--text-secondary)" }}>
                    Thinking…
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Error */}
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
                  placeholder="Ask a question… (Enter to send)"
                  rows={1}
                  maxLength={4096}
                  disabled={loading}
                />
                <button
                  style={sendBtnStyle(loading || !input.trim())}
                  onClick={() => void sendMessage()}
                  disabled={loading || !input.trim()}
                >
                  Send
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
