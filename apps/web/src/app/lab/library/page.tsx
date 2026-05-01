"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listPresets, type PresetSummary } from "../../../lib/api/presets";
import type { ProblemDetails } from "../../../lib/api";
import { getWorkspaceId } from "../../../lib/api";
import { PresetCard } from "./PresetCard";
import { InstantiateDialog } from "./InstantiateDialog";

const ADMIN_TOKEN_STORAGE_KEY = "labLibraryAdminToken";

function readStoredAdminToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? "";
}

export default function LabLibraryPage() {
  const router = useRouter();

  const [presets, setPresets] = useState<PresetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  // Admin lane: optional shared secret entered locally so PRIVATE presets
  // can be browsed before public release. Persisted in localStorage so the
  // operator does not have to re-enter on every navigation.
  const [adminToken, setAdminToken] = useState<string>("");
  const [adminMode, setAdminMode] = useState<boolean>(false);

  useEffect(() => {
    const stored = readStoredAdminToken();
    if (stored) {
      setAdminToken(stored);
      setAdminMode(true);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const tokenToUse = adminMode && adminToken ? adminToken : undefined;
    const res = await listPresets({ adminToken: tokenToUse });
    setLoading(false);
    if (!res.ok) {
      setError(res.problem);
      setPresets([]);
      return;
    }
    setPresets(res.data);
  }, [adminMode, adminToken]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleAdminToggle(next: boolean) {
    setAdminMode(next);
    if (!next && typeof window !== "undefined") {
      localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    }
  }

  function handleAdminTokenChange(value: string) {
    setAdminToken(value);
    if (typeof window !== "undefined") {
      if (value) localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, value);
      else localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    }
  }

  const selected = selectedSlug ? presets.find((p) => p.slug === selectedSlug) ?? null : null;
  const workspaceId = getWorkspaceId();

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <div>
          <h1 style={titleStyle}>Strategy Library</h1>
          <p style={subtitleStyle}>
            Curated, ready-to-run strategy presets. One click materialises a
            DRAFT bot in the active workspace.
          </p>
        </div>
        <AdminControls
          enabled={adminMode}
          token={adminToken}
          onEnabledChange={handleAdminToggle}
          onTokenChange={handleAdminTokenChange}
        />
      </header>

      {!workspaceId && (
        <div style={warnBoxStyle}>
          No active workspace. Set one on the Factory page before instantiating
          a preset.
        </div>
      )}

      {error && (
        <div style={errorBoxStyle}>
          <strong>{error.title}:</strong> {error.detail}
        </div>
      )}

      {loading ? (
        <p style={emptyStyle}>Loading presets…</p>
      ) : presets.length === 0 ? (
        <EmptyState adminMode={adminMode} />
      ) : (
        <div style={gridStyle}>
          {presets.map((preset) => (
            <PresetCard key={preset.slug} preset={preset} onUse={setSelectedSlug} />
          ))}
        </div>
      )}

      {selected && (
        <InstantiateDialog
          preset={selected}
          adminToken={adminMode && adminToken ? adminToken : undefined}
          onClose={() => setSelectedSlug(null)}
          onCreated={(botId) => {
            setSelectedSlug(null);
            router.push(`/factory/bots/${botId}`);
          }}
        />
      )}
    </div>
  );
}

function EmptyState({ adminMode }: { adminMode: boolean }) {
  return (
    <div style={emptyBoxStyle}>
      <p style={{ margin: 0, fontSize: 14, color: "var(--text-primary)" }}>
        {adminMode
          ? "No presets in the catalog yet."
          : "No public presets yet."}
      </p>
      <p style={{ margin: "6px 0 0", fontSize: 13, color: "var(--text-secondary)" }}>
        Build your own via Lab → Build, or ask an admin to publish a preset.
      </p>
    </div>
  );
}

function AdminControls({
  enabled,
  token,
  onEnabledChange,
  onTokenChange,
}: {
  enabled: boolean;
  token: string;
  onEnabledChange: (v: boolean) => void;
  onTokenChange: (v: string) => void;
}) {
  return (
    <div style={adminControlsStyle}>
      <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => onEnabledChange(e.target.checked)}
        />
        I'm an admin
      </label>
      {enabled && (
        <input
          type="password"
          placeholder="X-Admin-Token"
          value={token}
          onChange={(e) => onTokenChange(e.target.value)}
          style={tokenInputStyle}
          aria-label="Admin token"
        />
      )}
    </div>
  );
}

const pageStyle: React.CSSProperties = {
  padding: "32px 24px 64px",
  maxWidth: 1200,
  margin: "0 auto",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 16,
  marginBottom: 20,
  flexWrap: "wrap",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 22,
  fontWeight: 600,
  color: "var(--text-primary)",
};

const subtitleStyle: React.CSSProperties = {
  margin: "4px 0 0",
  color: "var(--text-secondary)",
  fontSize: 13,
};

const adminControlsStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const tokenInputStyle: React.CSSProperties = {
  padding: "5px 8px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 4,
  color: "var(--text-primary)",
  fontSize: 12,
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  minWidth: 200,
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
  gap: 16,
};

const emptyStyle: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 14,
};

const emptyBoxStyle: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: 24,
  textAlign: "center",
};

const errorBoxStyle: React.CSSProperties = {
  background: "rgba(248,113,113,0.08)",
  border: "1px solid rgba(248,113,113,0.4)",
  borderRadius: 6,
  padding: "8px 12px",
  marginBottom: 16,
  fontSize: 13,
  color: "#fca5a5",
};

const warnBoxStyle: React.CSSProperties = {
  background: "rgba(251,191,36,0.08)",
  border: "1px solid rgba(251,191,36,0.4)",
  borderRadius: 6,
  padding: "8px 12px",
  marginBottom: 16,
  fontSize: 13,
  color: "#fbbf24",
};
