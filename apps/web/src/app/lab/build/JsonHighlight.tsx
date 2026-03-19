"use client";

// ---------------------------------------------------------------------------
// A2-5 — JSON syntax highlighting for DSL Preview
// Token colours (dark theme, per docs/25 §A2-5):
//   json-key    → #7EB8F7 (blue)
//   json-string → #7EC48A (green)
//   json-number → #D4934C (amber)
//   json-bool   → #B57FE0 (violet)
//   json-null   → #B57FE0 (violet)
// Security: dangerouslySetInnerHTML wrapped in DOMPurify.sanitize() per docs/23 §15.1
// ---------------------------------------------------------------------------

import { useMemo } from "react";
import DOMPurify from "dompurify";

const COLORS = {
  key: "#7EB8F7",
  string: "#7EC48A",
  number: "#D4934C",
  bool: "#B57FE0",
  null: "#B57FE0",
} as const;

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function highlightJson(value: unknown): string {
  const raw = JSON.stringify(value, null, 2);
  if (!raw) return "";

  // Tokenise JSON string and wrap tokens in coloured spans.
  // Regex matches: strings (keys or values), numbers, booleans, null.
  return raw.replace(
    /("(?:\\.|[^"\\])*")\s*:/g,
    (match, key: string) =>
      `<span style="color:${COLORS.key}">${escapeHtml(key)}</span>:`,
  ).replace(
    // Match string values (not followed by colon — those are keys handled above)
    /:\s*("(?:\\.|[^"\\])*")/g,
    (match, val: string) =>
      `: <span style="color:${COLORS.string}">${escapeHtml(val)}</span>`,
  ).replace(
    // Standalone strings in arrays
    /(?<=[\[,\n]\s*)("(?:\\.|[^"\\])*")(?=\s*[,\]\n])/g,
    (val: string) =>
      `<span style="color:${COLORS.string}">${escapeHtml(val)}</span>`,
  ).replace(
    /\b(-?\d+\.?\d*(?:[eE][+-]?\d+)?)\b/g,
    (num: string) =>
      `<span style="color:${COLORS.number}">${num}</span>`,
  ).replace(
    /\b(true|false)\b/g,
    (bool: string) =>
      `<span style="color:${COLORS.bool}">${bool}</span>`,
  ).replace(
    /\bnull\b/g,
    `<span style="color:${COLORS.null}">null</span>`,
  );
}

interface JsonHighlightProps {
  data: unknown;
  style?: React.CSSProperties;
}

export default function JsonHighlight({ data, style }: JsonHighlightProps) {
  const html = useMemo(() => {
    const raw = highlightJson(data);
    return DOMPurify.sanitize(raw);
  }, [data]);

  return (
    <pre
      style={{
        margin: 0,
        fontSize: 12,
        lineHeight: 1.6,
        color: "rgba(255,255,255,0.82)",
        fontFamily: "monospace",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        ...style,
      }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
