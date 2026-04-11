"use client";

// ---------------------------------------------------------------------------
// Phase 3B — Inspector panel (right side)
// Per §6.4: "When a node is selected, Inspector shows: node name/type,
//   input ports (name + type + connected source or 'unconnected'),
//   output ports, params, validation errors, stale status badge"
// Per §6.3.1: Inspector shows edge details when an edge is selected.
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useState } from "react";
import type { LabNode, LabEdge } from "../useLabGraphStore";
import {
  BLOCK_DEF_MAP,
  CATEGORY_COLOR,
  PORT_TYPE_COLOR,
  type LabNodeData,
  type PortDataType,
} from "./blockDefs";
import { apiFetch } from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function TypeBadge({ dataType }: { dataType: PortDataType }) {
  const color = PORT_TYPE_COLOR[dataType];
  return (
    <span
      style={{
        display: "inline-block",
        background: `${color}22`,
        border: `1px solid ${color}60`,
        color,
        borderRadius: 3,
        padding: "1px 5px",
        fontSize: 9,
        fontFamily: "'SF Mono', 'Fira Code', monospace",
        whiteSpace: "nowrap",
      }}
    >
      {dataType}
    </span>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div
      style={{
        fontSize: 9,
        color: "rgba(255,255,255,0.35)",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        fontWeight: 600,
        marginTop: 12,
        marginBottom: 5,
        paddingBottom: 4,
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {title}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Node inspector view
// ---------------------------------------------------------------------------

interface NodeInspectorProps {
  node: LabNode;
  allEdges: LabEdge[];
  allNodes: LabNode[];
  onParamChange: (nodeId: string, paramId: string, value: unknown) => void;
}

function NodeInspector({ node, allEdges, allNodes, onParamChange }: NodeInspectorProps) {
  const data = node.data;
  const blockDef = BLOCK_DEF_MAP[data.blockType];

  if (!blockDef) {
    return (
      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, padding: 12 }}>
        Unknown block type: {data.blockType}
      </div>
    );
  }

  const categoryColor = CATEGORY_COLOR[blockDef.category];

  // Map input port → connected source node label
  const incomingEdgeMap: Record<string, { sourceNodeId: string; sourceNodeLabel: string }> = {};
  for (const edge of allEdges) {
    if (edge.target === node.id && edge.targetHandle) {
      const sourceNode = allNodes.find((n) => n.id === edge.source);
      const sourceLabel = sourceNode?.data?.blockType ?? edge.source;
      incomingEdgeMap[edge.targetHandle] = {
        sourceNodeId: edge.source,
        sourceNodeLabel: sourceLabel,
      };
    }
  }

  const handleParamChange = useCallback(
    (paramId: string, value: unknown) => {
      onParamChange(node.id, paramId, value);
    },
    [node.id, onParamChange]
  );

  return (
    <div style={{ padding: "10px 12px" }}>
      {/* Node header */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
        <span
          style={{
            fontWeight: 700,
            fontSize: 13,
            color: categoryColor,
            letterSpacing: "0.02em",
          }}
        >
          {blockDef.label}
        </span>
        {data.isStale && (
          <span
            style={{
              fontSize: 9,
              background: "rgba(251,191,36,0.15)",
              color: "#FBBF24",
              borderRadius: 3,
              padding: "1px 5px",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              fontWeight: 700,
            }}
          >
            stale
          </span>
        )}
      </div>
      <div
        style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", marginBottom: 4 }}
      >
        {blockDef.category} · id: {node.id}
      </div>
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", lineHeight: 1.5 }}>
        {blockDef.description}
      </div>

      {/* Input ports */}
      {blockDef.inputs.length > 0 && (
        <>
          <SectionHeader title="Inputs" />
          {blockDef.inputs.map((port) => {
            const connection = incomingEdgeMap[port.id];
            return (
              <div
                key={port.id}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                  marginBottom: 6,
                  flexWrap: "wrap",
                }}
              >
                <span
                  style={{
                    fontSize: 10,
                    color: "rgba(255,255,255,0.6)",
                    fontFamily: "'SF Mono', 'Fira Code', monospace",
                    minWidth: 60,
                  }}
                >
                  {port.label}
                  {port.required && (
                    <span style={{ color: "#D44C4C", marginLeft: 2 }}>*</span>
                  )}
                </span>
                <TypeBadge dataType={port.dataType} />
                <span
                  style={{
                    fontSize: 10,
                    color: connection
                      ? "rgba(255,255,255,0.5)"
                      : port.required
                      ? "rgba(212,76,76,0.8)"
                      : "rgba(255,255,255,0.25)",
                    fontStyle: connection ? "normal" : "italic",
                    marginLeft: 2,
                  }}
                >
                  {connection ? `← ${connection.sourceNodeLabel}` : "unconnected"}
                </span>
              </div>
            );
          })}
        </>
      )}

      {/* Output ports */}
      {blockDef.outputs.length > 0 && (
        <>
          <SectionHeader title="Outputs" />
          {blockDef.outputs.map((port) => (
            <div
              key={port.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 6,
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  color: "rgba(255,255,255,0.6)",
                  fontFamily: "'SF Mono', 'Fira Code', monospace",
                  minWidth: 60,
                }}
              >
                {port.label}
              </span>
              <TypeBadge dataType={port.dataType} />
            </div>
          ))}
        </>
      )}

      {/* Parameters */}
      {blockDef.params.length > 0 && (
        <>
          <SectionHeader title="Parameters" />
          {blockDef.params.map((param) => {
            const currentValue =
              param.id in data.params
                ? data.params[param.id]
                : param.defaultValue;

            return (
              <div key={param.id} style={{ marginBottom: 8 }}>
                <label
                  style={{
                    display: "block",
                    fontSize: 10,
                    color: "rgba(255,255,255,0.5)",
                    marginBottom: 3,
                  }}
                >
                  {param.label}
                </label>
                {param.type === "select" ? (
                  <select
                    value={String(currentValue)}
                    onChange={(e) => handleParamChange(param.id, e.target.value)}
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 4,
                      color: "rgba(255,255,255,0.8)",
                      fontSize: 11,
                      padding: "3px 6px",
                      width: "100%",
                      fontFamily: "inherit",
                      cursor: "pointer",
                    }}
                  >
                    {param.options?.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    value={String(currentValue)}
                    min={param.min}
                    max={param.max}
                    onChange={(e) =>
                      handleParamChange(param.id, Number(e.target.value))
                    }
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 4,
                      color: "rgba(255,255,255,0.8)",
                      fontSize: 11,
                      padding: "3px 6px",
                      width: "100%",
                      boxSizing: "border-box",
                      fontFamily: "inherit",
                    }}
                  />
                )}
              </div>
            );
          })}
        </>
      )}

      {/* Task 29: Risk config warning for stop_loss / take_profit blocks */}
      {(blockDef.category === "risk") && (
        <RiskWarningBanner params={data.params} blockType={data.blockType} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Task 29 — Risk Warning Banner (AI-powered, graceful degradation)
// ---------------------------------------------------------------------------

const RISK_BLOCK_TYPES = new Set(["stop_loss", "take_profit"]);

function RiskWarningBanner({ params, blockType }: { params: Record<string, unknown>; blockType: string }) {
  const [warning, setWarning] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiAvailable, setAiAvailable] = useState<boolean | null>(null);

  // Check AI availability once
  useEffect(() => {
    apiFetch<{ available: boolean }>("/ai/status")
      .then((res) => { if (res.ok) setAiAvailable(res.data.available); else setAiAvailable(false); })
      .catch(() => setAiAvailable(false));
  }, []);

  // Fetch risk suggestion when params change (debounced)
  useEffect(() => {
    if (!aiAvailable || !RISK_BLOCK_TYPES.has(blockType)) return;

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await apiFetch<{ warning: string | null; suggestions: string[] }>("/lab/explain/risk", {
          method: "POST",
          body: JSON.stringify({ riskParams: { blockType, ...params } }),
        });
        if (res.ok) {
          setWarning(res.data.warning);
          setSuggestions(res.data.suggestions);
        } else {
          setWarning(null);
          setSuggestions([]);
        }
      } catch {
        setWarning(null);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 1500);

    return () => clearTimeout(timer);
  }, [aiAvailable, blockType, params]);

  if (!aiAvailable || !RISK_BLOCK_TYPES.has(blockType)) return null;
  if (loading) return (
    <div style={{ marginTop: 10, fontSize: 10, color: "rgba(255,255,255,0.25)" }}>
      Checking risk config...
    </div>
  );
  if (!warning) return null;

  return (
    <div style={{
      marginTop: 12,
      padding: "8px 10px",
      background: "rgba(251,191,36,0.08)",
      border: "1px solid rgba(251,191,36,0.25)",
      borderRadius: 6,
      fontSize: 11,
      lineHeight: 1.5,
    }}>
      <div style={{ color: "#FBBF24", fontWeight: 700, fontSize: 10, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
        AI Risk Warning
      </div>
      <div style={{ color: "rgba(255,255,255,0.7)" }}>{warning}</div>
      {suggestions.length > 0 && (
        <ul style={{ margin: "6px 0 0", paddingLeft: 16, color: "rgba(255,255,255,0.55)" }}>
          {suggestions.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      )}
      <div style={{ fontSize: 9, color: "rgba(255,255,255,0.25)", marginTop: 6 }}>
        Advisory only — apply changes through the graph editor
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Edge inspector view
// ---------------------------------------------------------------------------

interface EdgeInspectorProps {
  edge: LabEdge;
  allNodes: LabNode[];
}

// A1-4: edge.data is now typed as StrategyEdgeData — no cast needed
function EdgeInspector({ edge, allNodes }: EdgeInspectorProps) {
  const dataType = edge.data?.dataType;

  const sourceNode = allNodes.find((n) => n.id === edge.source);
  const targetNode = allNodes.find((n) => n.id === edge.target);

  const sourceData = sourceNode?.data;
  const targetData = targetNode?.data;

  return (
    <div style={{ padding: "10px 12px" }}>
      <div
        style={{ fontWeight: 700, fontSize: 12, color: "rgba(255,255,255,0.7)", marginBottom: 6 }}
      >
        Edge
      </div>

      <SectionHeader title="Connection" />
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)", marginBottom: 4 }}>
        <span style={{ color: "rgba(255,255,255,0.7)" }}>From:</span>{" "}
        {sourceData?.blockType ?? edge.source}
        {edge.sourceHandle ? ` [${edge.sourceHandle}]` : ""}
      </div>
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)", marginBottom: 4 }}>
        <span style={{ color: "rgba(255,255,255,0.7)" }}>To:</span>{" "}
        {targetData?.blockType ?? edge.target}
        {edge.targetHandle ? ` [${edge.targetHandle}]` : ""}
      </div>
      {dataType && (
        <div style={{ marginTop: 8 }}>
          <SectionHeader title="Data Type" />
          <TypeBadge dataType={dataType} />
        </div>
      )}
      <div style={{ marginTop: 8, fontSize: 10, color: "rgba(255,255,255,0.3)" }}>
        id: {edge.id}
      </div>
      {edge.data?.isStale && (
        <div
          style={{
            marginTop: 8,
            fontSize: 10,
            color: "#FBBF24",
            background: "rgba(251,191,36,0.08)",
            borderRadius: 4,
            padding: "4px 8px",
          }}
        >
          ⚠ Stale — upstream data changed. Re-validate the graph.
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Multi-node summary view
// ---------------------------------------------------------------------------

function MultiSelectSummary({ nodes }: { nodes: LabNode[] }) {
  return (
    <div style={{ padding: "10px 12px" }}>
      <div
        style={{ fontWeight: 700, fontSize: 12, color: "rgba(255,255,255,0.7)", marginBottom: 8 }}
      >
        {nodes.length} nodes selected
      </div>
      {nodes.map((n) => {
        const d = n.data;
        const def = BLOCK_DEF_MAP[d.blockType];
        return (
          <div
            key={n.id}
            style={{
              fontSize: 10,
              color: "rgba(255,255,255,0.5)",
              marginBottom: 3,
              borderLeft: `2px solid ${def ? CATEGORY_COLOR[def.category] : "#8090A0"}`,
              paddingLeft: 6,
            }}
          >
            {d.blockType}
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty / idle state
// ---------------------------------------------------------------------------

function InspectorEmpty() {
  return (
    <div
      style={{
        padding: 16,
        color: "rgba(255,255,255,0.2)",
        fontSize: 11,
        textAlign: "center",
        lineHeight: 1.7,
      }}
    >
      <div style={{ marginBottom: 8, fontSize: 18, opacity: 0.4 }}>⬡</div>
      Select a node or edge to inspect
    </div>
  );
}

// ---------------------------------------------------------------------------
// InspectorPanel — exported component
// ---------------------------------------------------------------------------

interface InspectorPanelProps {
  selectedNodes: LabNode[];
  selectedEdges: LabEdge[];
  allNodes: LabNode[];
  allEdges: LabEdge[];
  onParamChange: (nodeId: string, paramId: string, value: unknown) => void;
}

export default function InspectorPanel({
  selectedNodes,
  selectedEdges,
  allNodes,
  allEdges,
  onParamChange,
}: InspectorPanelProps) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: "rgba(255,255,255,0.02)",
        borderLeft: "1px solid rgba(255,255,255,0.08)",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 12px 8px",
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
            fontWeight: 600,
          }}
        >
          Inspector
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {selectedNodes.length === 0 && selectedEdges.length === 0 && (
          <InspectorEmpty />
        )}

        {selectedNodes.length === 1 && selectedEdges.length === 0 && (
          <NodeInspector
            node={selectedNodes[0]}
            allEdges={allEdges}
            allNodes={allNodes}
            onParamChange={onParamChange}
          />
        )}

        {selectedNodes.length > 1 && (
          <MultiSelectSummary nodes={selectedNodes} />
        )}

        {selectedNodes.length === 0 && selectedEdges.length === 1 && (
          <EdgeInspector edge={selectedEdges[0]} allNodes={allNodes} />
        )}
      </div>
    </div>
  );
}
