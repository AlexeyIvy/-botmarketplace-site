"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/terminal", label: "Terminal" },
  { href: "/lab", label: "Lab" },
  { href: "/factory", label: "Factory" },
] as const;

export function Navbar() {
  const pathname = usePathname();

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
    </nav>
  );
}
