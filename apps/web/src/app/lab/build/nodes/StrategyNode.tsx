"use client";

// ---------------------------------------------------------------------------
// Phase 3B — Custom node renderer for Strategy Graph blocks
// Phase 3C — Error badge on header + red port ring for unconnected required ports
// Per §6.3.1 and §9.1, §28 Level 3/5
// ---------------------------------------------------------------------------

import { memo, useCallback } from "react";
import { Handle, Position, useStore as useRFStore } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import {
  BLOCK_DEF_MAP,
  CATEGORY_COLOR,
  PORT_TYPE_COLOR,
  type PortDataType,
  type LabNodeData,
} from "../blockDefs";
import { useConnectionContext } from "../ConnectionContext";
import { useLabGraphStore } from "../../useLabGraphStore";

// ---------------------------------------------------------------------------
// Port handle component (per §6.3.1 port appearance)
// ---------------------------------------------------------------------------

interface PortHandleProps {
  id: string;
  label: string;
  dataType: PortDataType;
  required: boolean;
  side: "input" | "output";
  /** Whether a connection drag is in progress and this port is a compatible target */
  compatibleTarget: boolean;
  /** Whether a connection drag is in progress and this port is an incompatible target */
  incompatibleTarget: boolean;
  /** Whether this port already has an incoming connection (inputs only) */
  connected: boolean;
  /** Phase 3C: whether this port has a validation error (unconnected required) */
  hasValidationError: boolean;
}

function PortHandle({
  id,
  label,
  dataType,
  required,
  side,
  compatibleTarget,
  incompatibleTarget,
  connected,
  hasValidationError,
}: PortHandleProps) {
  const color = PORT_TYPE_COLOR[dataType];
  const position = side === "input" ? Position.Left : Position.Right;

  // Build the handle style per §6.3.1 port state table
  // A2-7: transition for smooth drag feedback
  const handleStyle: React.CSSProperties = {
    width: 10,
    height: 10,
    borderRadius: "50%",
    border: "none",
    cursor: "crosshair",
    position: "relative",
    transition: "all 0.12s ease",
    // Hit area is handled by React Flow's default invisible wrapper
  };

  if (incompatibleTarget) {
    // A2-7: Incompatible: red ring, scale 0.85, opacity 25%, borderColor #D44C4C
    handleStyle.background = "transparent";
    handleStyle.boxShadow = `0 0 0 2px #D44C4C`;
    handleStyle.borderColor = "#D44C4C";
    handleStyle.transform = "scale(0.85)";
    handleStyle.opacity = 0.25;
  } else if (compatibleTarget) {
    // Compatible target during drag: pulse ring (CSS handles animation), solid color
    handleStyle.background = color;
    handleStyle.boxShadow = `0 0 0 2px ${color}, 0 0 6px ${color}80`;
    handleStyle.transform = "scale(1.4)";
  } else if (connected) {
    // Connected: solid fill + inner dot
    handleStyle.background = color;
    handleStyle.boxShadow = `0 0 0 1.5px ${color}`;
  } else if (hasValidationError) {
    // Phase 3C: unconnected required port with validation error → red ring
    handleStyle.background = "transparent";
    handleStyle.boxShadow = `0 0 0 2px #D44C4C, 0 0 5px #D44C4C66`;
    handleStyle.animation = "portErrorPulse 1.5s ease-in-out infinite";
  } else if (required) {
    // Unconnected required: outline ring with pulse (animation via className)
    handleStyle.background = "transparent";
    handleStyle.boxShadow = `0 0 0 2px ${color}`;
    handleStyle.animation = "portPulse 2s ease-in-out infinite";
  } else {
    // Unconnected optional: faint outline ring
    handleStyle.background = "transparent";
    handleStyle.boxShadow = `0 0 0 1px ${color}80`;
  }

  const ariaLabel =
    side === "output"
      ? `${label} output: ${dataType}`
      : `${label} input: ${dataType}${required ? ", required" : ""}${hasValidationError ? ", error: unconnected" : ""}`;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        flexDirection: side === "input" ? "row" : "row-reverse",
        position: "relative",
        padding: "2px 0",
      }}
    >
      <Handle
        type={side === "input" ? "target" : "source"}
        position={position}
        id={id}
        style={{
          ...handleStyle,
          // Override React Flow defaults
          top: "auto",
          left: "auto",
          right: "auto",
          bottom: "auto",
          transform: handleStyle.transform,
        }}
        aria-label={ariaLabel}
      />
      <span
        style={{
          fontSize: 10,
          color: hasValidationError
            ? "rgba(212,76,76,0.9)"
            : "rgba(255,255,255,0.45)",
          userSelect: "none",
          fontFamily: "inherit",
          lineHeight: 1,
        }}
      >
        {label}
        {hasValidationError && (
          <span style={{ marginLeft: 3, fontSize: 9 }}>⚠</span>
        )}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// StrategyNode — main custom node component
// ---------------------------------------------------------------------------

function StrategyNode({ id, data, selected }: NodeProps) {
  const nodeData = data as LabNodeData;
  const { blockType, isStale } = nodeData;

  const blockDef = BLOCK_DEF_MAP[blockType];
  if (!blockDef) return null;

  const { sourceType } = useConnectionContext();

  // Get all edges from RF store to know which input ports are occupied
  const edges = useRFStore((s) => s.edges);
  const connectedInputIds = new Set(
    edges.filter((e) => e.target === id).map((e) => e.targetHandle)
  );

  // Phase 3C: get validation issues for this node from Zustand store
  const validationIssues = useLabGraphStore((s) => s.validationIssues);
  const nodeIssues = validationIssues.filter((issue) => issue.nodeId === id);
  const hasNodeError = nodeIssues.some((i) => i.severity === "error");
  const hasNodeWarning = nodeIssues.some((i) => i.severity === "warning");

  // Build set of port IDs that have validation errors
  const errorPortIds = new Set(
    nodeIssues
      .filter((i) => i.portId !== undefined)
      .map((i) => i.portId as string)
  );

  const categoryColor = CATEGORY_COLOR[blockDef.category];

  // Determine per-port drag state for visual feedback
  const isDragging = sourceType !== null;

  const getPortDragState = useCallback(
    (portDataType: PortDataType, side: "input" | "output") => {
      if (!isDragging || side === "output") {
        return { compatibleTarget: false, incompatibleTarget: false };
      }
      const compatible = portDataType === sourceType;
      return {
        compatibleTarget: compatible,
        incompatibleTarget: !compatible,
      };
    },
    [isDragging, sourceType]
  );

  // Node opacity during drag: 60% if this node has NO compatible inputs
  const nodeHasCompatibleInput =
    isDragging &&
    blockDef.inputs.some((p) => p.dataType === sourceType && !connectedInputIds.has(p.id));

  const nodeOpacity =
    isDragging && blockDef.inputs.length > 0 && !nodeHasCompatibleInput ? 0.6 : 1;

  // Error badge color: red for errors, amber for warnings only
  const errorBadgeColor = hasNodeError ? "#D44C4C" : "#FBBF24";
  const showErrorBadge = hasNodeError || hasNodeWarning;

  return (
    <>
      {/* Keyframe for port pulse animations */}
      <style>{`
        @keyframes portPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        @keyframes portErrorPulse {
          0%, 100% { transform: scale(1); box-shadow: 0 0 0 2px #D44C4C, 0 0 5px #D44C4C66; }
          50% { transform: scale(1.15); box-shadow: 0 0 0 2px #D44C4C, 0 0 8px #D44C4CAA; }
        }
      `}</style>

      <div
        style={{
          minWidth: 140,
          background: selected
            ? "rgba(255,255,255,0.08)"
            : "rgba(255,255,255,0.04)",
          border: selected
            ? `1px solid ${categoryColor}80`
            : hasNodeError
            ? "1px solid rgba(212,76,76,0.4)"
            : "1px solid rgba(255,255,255,0.1)",
          borderLeft: `3px solid ${categoryColor}`,
          borderRadius: 6,
          fontFamily:
            "'SF Mono', 'Fira Code', 'Consolas', 'Menlo', monospace",
          fontSize: 11,
          color: "rgba(255,255,255,0.85)",
          boxShadow: isStale
            ? "0 0 0 1px rgba(251,191,36,0.4)"
            : hasNodeError
            ? "0 0 0 1px rgba(212,76,76,0.25)"
            : selected
            ? `0 0 8px ${categoryColor}40`
            : "none",
          opacity: nodeOpacity,
          transition: "opacity 0.15s ease",
          cursor: "grab",
          position: "relative",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "5px 10px 4px",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span
            style={{
              fontWeight: 600,
              fontSize: 11,
              color: categoryColor,
              letterSpacing: "0.03em",
              textTransform: "uppercase",
              flex: 1,
            }}
          >
            {blockDef.label}
          </span>
          {isStale && (
            <span
              style={{
                fontSize: 9,
                background: "rgba(251,191,36,0.2)",
                color: "#FBBF24",
                borderRadius: 3,
                padding: "1px 4px",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                fontWeight: 700,
              }}
            >
              stale
            </span>
          )}
          {/* Phase 3C: Error/warning badge on node header (§28 Level 3) */}
          {showErrorBadge && (
            <span
              style={{
                fontSize: 11,
                color: errorBadgeColor,
                lineHeight: 1,
                flexShrink: 0,
              }}
              title={
                hasNodeError
                  ? `${nodeIssues.filter((i) => i.severity === "error").length} validation error(s)`
                  : `${nodeIssues.filter((i) => i.severity === "warning").length} validation warning(s)`
              }
              aria-label={hasNodeError ? "Node has validation errors" : "Node has validation warnings"}
            >
              ⚠
            </span>
          )}
        </div>

        {/* Body — ports */}
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            padding: "6px 0",
            gap: 8,
          }}
        >
          {/* Input ports — left side */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              gap: 4,
              paddingLeft: 2,
              alignItems: "flex-start",
            }}
          >
            {blockDef.inputs.map((port) => {
              const { compatibleTarget, incompatibleTarget } = getPortDragState(
                port.dataType,
                "input"
              );
              const connected = connectedInputIds.has(port.id);
              // Phase 3C: port has error if it's in the errorPortIds set
              const hasValidationError = errorPortIds.has(port.id);
              return (
                <PortHandle
                  key={port.id}
                  id={port.id}
                  label={port.label}
                  dataType={port.dataType}
                  required={port.required}
                  side="input"
                  compatibleTarget={compatibleTarget}
                  incompatibleTarget={incompatibleTarget}
                  connected={connected}
                  hasValidationError={hasValidationError}
                />
              );
            })}
          </div>

          {/* Spacer */}
          {blockDef.inputs.length > 0 && blockDef.outputs.length > 0 && (
            <div style={{ width: 1, background: "rgba(255,255,255,0.06)" }} />
          )}

          {/* Output ports — right side */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              gap: 4,
              paddingRight: 2,
              alignItems: "flex-end",
            }}
          >
            {blockDef.outputs.map((port) => (
              <PortHandle
                key={port.id}
                id={port.id}
                label={port.label}
                dataType={port.dataType}
                required={port.required}
                side="output"
                compatibleTarget={false}
                incompatibleTarget={false}
                connected={false}
                hasValidationError={false}
              />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

export default memo(StrategyNode);
