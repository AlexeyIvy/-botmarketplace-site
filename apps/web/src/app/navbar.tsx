"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, clearAuth } from "./factory/api";

const NAV_ITEMS = [
  { href: "/terminal", label: "Terminal" },
  { href: "/lab", label: "Lab" },
  { href: "/factory", label: "Factory" },
] as const;

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuth, setIsAuth] = useState(false);

  useEffect(() => {
    setIsAuth(!!getToken());
  }, [pathname]);

  function handleLogout() {
    clearAuth();
    setIsAuth(false);
    router.push("/login");
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
          <button
            onClick={handleLogout}
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: "6px",
              color: "var(--text-secondary)",
              cursor: "pointer",
              fontSize: "13px",
              padding: "6px 14px",
            }}
          >
            Sign out
          </button>
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
