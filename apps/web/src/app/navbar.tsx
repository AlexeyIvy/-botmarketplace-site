"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { getToken, clearAuth, apiFetchNoWorkspace } from "../lib/api";

const NAV_ITEMS = [
  { href: "/terminal", label: "Terminal" },
  { href: "/terminal/funding", label: "Funding" },
  { href: "/lab", label: "Lab" },
  { href: "/factory", label: "Factory" },
] as const;

interface MeResponse {
  user: { id: string; email: string; avatarUrl?: string | null };
  workspaceId: string | null;
}

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuth, setIsAuth] = useState(false);
  const [userInfo, setUserInfo] = useState<{ email: string; avatarUrl?: string | null } | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = getToken();
    setIsAuth(!!token);
    if (token) {
      apiFetchNoWorkspace<MeResponse>("/auth/me").then((res) => {
        if (res.ok) setUserInfo(res.data.user);
        else setUserInfo(null);
      });
    } else {
      setUserInfo(null);
    }
    setDropdownOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!dropdownOpen) return;
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownOpen]);

  function handleLogout() {
    clearAuth();
    setIsAuth(false);
    setUserInfo(null);
    setDropdownOpen(false);
    router.push("/login");
  }

  function getInitials(email: string): string {
    return email.slice(0, 2).toUpperCase();
  }

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "var(--nav-height)",
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        padding: "0 24px",
        zIndex: 100,
        gap: "8px",
      }}
    >
      <span
        style={{
          fontWeight: 700,
          fontSize: "18px",
          marginRight: "32px",
          color: "var(--text-primary)",
        }}
      >
        BotMarketplace
      </span>

      {NAV_ITEMS.map(({ href, label }) => {
        const isActive = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: 500,
              color: isActive ? "var(--accent)" : "var(--text-secondary)",
              background: isActive ? "var(--bg-card)" : "transparent",
              transition: "all 0.15s",
            }}
          >
            {label}
          </Link>
        );
      })}

      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "8px" }}>
        {isAuth ? (
          <div ref={dropdownRef} style={{ position: "relative" }}>
            {/* Profile trigger */}
            <button
              onClick={() => setDropdownOpen((o) => !o)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: "transparent",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-primary)",
                cursor: "pointer",
                fontSize: "13px",
                padding: "5px 10px",
              }}
            >
              {/* Avatar circle */}
              <span style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                overflow: "hidden",
                background: "var(--accent)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                fontSize: "11px",
                fontWeight: 700,
                color: "#fff",
              }}>
                {userInfo?.avatarUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={userInfo.avatarUrl}
                    alt="avatar"
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                ) : (
                  <span>{userInfo ? getInitials(userInfo.email) : "…"}</span>
                )}
              </span>
              {userInfo?.email && (
                <span style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {userInfo.email}
                </span>
              )}
              <span style={{ fontSize: "10px", opacity: 0.6 }}>▾</span>
            </button>

            {/* Dropdown */}
            {dropdownOpen && (
              <div style={{
                position: "absolute",
                top: "calc(100% + 6px)",
                right: 0,
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                minWidth: 160,
                zIndex: 200,
                boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
                overflow: "hidden",
              }}>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  style={{
                    display: "block",
                    padding: "10px 16px",
                    fontSize: "13px",
                    color: "var(--text-primary)",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  ⚙ Settings
                </Link>
                <button
                  onClick={handleLogout}
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: "10px 16px",
                    fontSize: "13px",
                    color: "var(--text-secondary)",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            <Link
              href="/login"
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                color: "var(--text-secondary)",
                border: "1px solid var(--border)",
              }}
            >
              Sign in
            </Link>
            <Link
              href="/register"
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                color: "#fff",
                background: "var(--accent)",
                fontWeight: 600,
              }}
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
