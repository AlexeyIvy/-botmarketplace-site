"use client";

// ---------------------------------------------------------------------------
// Phase 3B — Searchable block palette (left panel)
// Per §6.3: "left: block palette (categorized, searchable)"
// Per §15: "Searchable block palette (left panel) with all block categories"
// ---------------------------------------------------------------------------

import { useState, useCallback } from "react";
import {
  BLOCK_DEFS,
  CATEGORY_COLOR,
  CATEGORY_LABEL,
  type BlockCategory,
  type BlockDef,
} from "./blockDefs";

const CATEGORIES: BlockCategory[] = ["input", "indicator", "logic", "execution", "risk"];

interface BlockPaletteProps {
  /** Called when user clicks "Add" or double-clicks a block item */
  onAddBlock: (blockType: string) => void;
}

// Each block in the palette is draggable — drag data is the block type.
// React Flow's onDrop + onDragOver in the canvas will consume this.
function PaletteItem({
  block,
  onAdd,
}: {
  block: BlockDef;
  onAdd: (type: string) => void;
}) {
  const accentColor = CATEGORY_COLOR[block.category];

  const handleDragStart = useCallback(
    (e: React.DragEvent) => {
      e.dataTransfer.setData("application/lab-block-type", block.type);
      e.dataTransfer.effectAllowed = "copy";
    },
    [block.type]
  );

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDoubleClick={() => onAdd(block.type)}
      title={block.description}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "5px 8px",
        borderRadius: 4,
        cursor: "grab",
        userSelect: "none",
        transition: "background 0.1s",
        borderLeft: `2px solid ${accentColor}`,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.background =
          "rgba(255,255,255,0.06)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.background = "transparent";
      }}
    >
      <span
        style={{
          fontSize: 10,
          color: "rgba(255,255,255,0.75)",
          fontFamily: "'SF Mono', 'Fira Code', monospace",
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {block.label}
      </span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onAdd(block.type);
        }}
        title={`Add ${block.label} to canvas`}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          color: accentColor,
          fontSize: 14,
          lineHeight: 1,
          padding: "0 2px",
          opacity: 0.6,
          display: "flex",
          alignItems: "center",
        }}
        onMouseEnter={(e) =>
          ((e.currentTarget as HTMLButtonElement).style.opacity = "1")
        }
        onMouseLeave={(e) =>
          ((e.currentTarget as HTMLButtonElement).style.opacity = "0.6")
        }
      >
        +
      </button>
    </div>
  );
}

export default function BlockPalette({ onAddBlock }: BlockPaletteProps) {
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<Set<BlockCategory>>(new Set());

  const normalizedSearch = search.toLowerCase().trim();

  const toggleCategory = useCallback((cat: BlockCategory) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }, []);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: "rgba(255,255,255,0.02)",
        borderRight: "1px solid rgba(255,255,255,0.08)",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 10px 8px",
          borderBottom: "1px solid rgba(255,255,255,0.07)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontSize: 10,
            color: "rgba(255,255,255,0.4)",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: 7,
            fontFamily: "inherit",
          }}
        >
          Blocks
        </div>

        {/* Search input — Cmd+Shift+F focuses this per §6.3 keyboard shortcuts */}
        <input
          id="block-palette-search"
          type="text"
          placeholder="Search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "100%",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 4,
            color: "rgba(255,255,255,0.8)",
            fontSize: 11,
            padding: "4px 8px",
            outline: "none",
            fontFamily: "inherit",
            boxSizing: "border-box",
          }}
          onFocus={(e) =>
            ((e.currentTarget as HTMLInputElement).style.borderColor =
              "rgba(255,255,255,0.25)")
          }
          onBlur={(e) =>
            ((e.currentTarget as HTMLInputElement).style.borderColor =
              "rgba(255,255,255,0.1)")
          }
        />
      </div>

      {/* Category list */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "6px 0",
        }}
      >
        {CATEGORIES.map((cat) => {
          const blocks = BLOCK_DEFS.filter(
            (b) =>
              b.category === cat &&
              (normalizedSearch === "" ||
                b.label.toLowerCase().includes(normalizedSearch) ||
                b.type.toLowerCase().includes(normalizedSearch))
          );

          if (blocks.length === 0) return null;

          const isCollapsed = collapsed.has(cat) && normalizedSearch === "";
          const accentColor = CATEGORY_COLOR[cat];

          return (
            <div key={cat}>
              {/* Category header */}
              <button
                onClick={() => toggleCategory(cat)}
                style={{
                  width: "100%",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  padding: "3px 10px",
                  color: accentColor,
                  fontSize: 10,
                  fontFamily: "inherit",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  fontWeight: 600,
                }}
              >
                <span
                  style={{
                    fontSize: 9,
                    opacity: 0.7,
                    display: "inline-block",
                    transform: isCollapsed ? "rotate(-90deg)" : "rotate(0deg)",
                    transition: "transform 0.15s",
                  }}
                >
                  ▼
                </span>
                {CATEGORY_LABEL[cat]}
                <span
                  style={{
                    marginLeft: "auto",
                    fontSize: 9,
                    opacity: 0.5,
                    color: "rgba(255,255,255,0.4)",
                  }}
                >
                  {blocks.length}
                </span>
              </button>

              {/* Blocks in category */}
              {!isCollapsed && (
                <div style={{ paddingLeft: 8, paddingRight: 4 }}>
                  {blocks.map((block) => (
                    <PaletteItem
                      key={block.type}
                      block={block}
                      onAdd={onAddBlock}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer hint */}
      <div
        style={{
          padding: "6px 10px",
          borderTop: "1px solid rgba(255,255,255,0.07)",
          fontSize: 9,
          color: "rgba(255,255,255,0.25)",
          lineHeight: 1.5,
          flexShrink: 0,
        }}
      >
        Drag to canvas · Double-click to add
      </div>
    </div>
  );
}
