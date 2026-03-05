"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const ONBOARDING_KEY = "onboardingSeen";

export function OnboardingModal() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem(ONBOARDING_KEY) !== "1") {
      setVisible(true);
    }
  }, []);

  function dismiss() {
    localStorage.setItem(ONBOARDING_KEY, "1");
    setVisible(false);
  }

  function handleSignIn() {
    dismiss();
    router.push("/login");
  }

  function handleGuest() {
    dismiss();
  }

  if (!visible) return null;

  return (
    <div style={overlay}>
      <div style={modal}>
        <h2 style={{ margin: "0 0 8px", fontSize: 22 }}>Welcome to BotMarketplace</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "0 0 24px", lineHeight: 1.5 }}>
          Explore live market data without registration, or sign in to trade and save your preferences.
        </p>
        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          <button style={primaryBtn} onClick={handleSignIn}>
            Sign in
          </button>
          <button style={secondaryBtn} onClick={handleGuest}>
            Continue as guest
          </button>
        </div>
      </div>
    </div>
  );
}

const overlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.55)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 9999,
};

const modal: React.CSSProperties = {
  background: "var(--bg-card, #1c1c1e)",
  border: "1px solid var(--border, #30363d)",
  borderRadius: 12,
  padding: "32px 28px",
  maxWidth: 420,
  width: "90%",
  textAlign: "center",
  boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
};

const primaryBtn: React.CSSProperties = {
  padding: "11px 28px",
  background: "var(--accent, #0969da)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 15,
  fontWeight: 600,
};

const secondaryBtn: React.CSSProperties = {
  padding: "11px 28px",
  background: "transparent",
  color: "var(--text-primary)",
  border: "1px solid var(--border, #30363d)",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 15,
  fontWeight: 500,
};
