"use client";

import type { PresetSummary } from "../../../lib/api/presets";

const CATEGORY_COLOR: Record<string, string> = {
  trend: "#3B82F6",
  dca: "#10B981",
  scalping: "#F59E0B",
  smc: "#8B5CF6",
  arb: "#EC4899",
};

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trimEnd()}…`;
}

export function PresetCard({
  preset,
  onUse,
}: {
  preset: PresetSummary;
  onUse: (slug: string) => void;
}) {
  const isPrivate = preset.visibility === "PRIVATE";
  const isBeta = preset.visibility === "BETA";
  const categoryColor = CATEGORY_COLOR[preset.category] ?? "#6B7280";

  return (
    <div style={cardStyle}>
      <div style={headerStyle}>
        <div style={categoryBadgeStyle(categoryColor)}>{preset.category}</div>
        {isPrivate && <div style={privateBadgeStyle}>Private</div>}
        {isBeta && (
          <div
            style={betaBadgeStyle}
            title="BETA — multi-leg execution, monitor closely"
          >
            Beta
          </div>
        )}
      </div>

      <h3 style={titleStyle}>{preset.name}</h3>
      <p style={descStyle}>{truncate(preset.description, 200)}</p>

      <div style={metaStyle}>
        <span>
          <strong>{preset.defaultBotConfigJson.symbol}</strong>
          <span style={metaSepStyle}> · </span>
          {preset.defaultBotConfigJson.timeframe}
        </span>
        <span style={metaQuoteStyle}>
          {preset.defaultBotConfigJson.quoteAmount} USDT
        </span>
      </div>

      <button
        onClick={() => onUse(preset.slug)}
        style={useButtonStyle}
        type="button"
      >
        Use preset
      </button>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: 16,
  display: "flex",
  flexDirection: "column",
  gap: 10,
  minHeight: 220,
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const categoryBadgeStyle = (color: string): React.CSSProperties => ({
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  padding: "2px 8px",
  borderRadius: 4,
  color,
  background: `${color}1F`,
  border: `1px solid ${color}66`,
});

const privateBadgeStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  padding: "2px 8px",
  borderRadius: 4,
  color: "rgba(255,255,255,0.55)",
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.18)",
};

// Yellow/amber accent — same shade family as the `scalping` category badge
// (#F59E0B) so the visual vocabulary stays consistent. Tooltip carries the
// operator-facing rationale; on hover the user sees the full advisory.
const betaBadgeStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  padding: "2px 8px",
  borderRadius: 4,
  color: "#F59E0B",
  background: "rgba(245, 158, 11, 0.12)",
  border: "1px solid rgba(245, 158, 11, 0.45)",
  cursor: "help",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 15,
  fontWeight: 600,
  color: "var(--text-primary)",
};

const descStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 13,
  color: "var(--text-secondary)",
  lineHeight: 1.5,
  flex: 1,
};

const metaStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  fontSize: 12,
  color: "var(--text-secondary)",
  paddingTop: 8,
  borderTop: "1px solid var(--border)",
};

const metaSepStyle: React.CSSProperties = {
  color: "rgba(255,255,255,0.25)",
};

const metaQuoteStyle: React.CSSProperties = {
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  fontSize: 11,
};

const useButtonStyle: React.CSSProperties = {
  marginTop: 4,
  padding: "8px 14px",
  fontSize: 13,
  fontWeight: 600,
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontFamily: "inherit",
};
