"use client";

// ---------------------------------------------------------------------------
// Phase 3B — Custom edge renderer for Strategy Graph
// Per §6.3.1 edge appearance table
// ---------------------------------------------------------------------------

import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  useStore as useRFStore,
} from "@xyflow/react";
import type { EdgeProps } from "@xyflow/react";

import { PORT_TYPE_COLOR, PORT_TYPE_ABBR, type PortDataType } from "../blockDefs";

export interface StrategyEdgeData extends Record<string, unknown> {
  dataType: PortDataType;
  isStale?: boolean;
  isInvalid?: boolean;
}

function StrategyEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  source,
  target,
}: EdgeProps) {
  const edgeData = data as StrategyEdgeData | undefined;
  const dataType = edgeData?.dataType;
  const isStale = edgeData?.isStale ?? false;
  const isInvalid = edgeData?.isInvalid ?? false;

  const typeColor = dataType ? PORT_TYPE_COLOR[dataType] : "#8090A0";
  const typeAbbr = dataType ? PORT_TYPE_ABBR[dataType] : "?";

  // Edge style per §6.3.1 table
  const strokeColor = isInvalid
    ? "#D44C4C"
    : isStale
    ? `${typeColor}59`  // 35% opacity
    : selected
    ? typeColor
    : `${typeColor}CC`;  // 80% opacity

  const strokeWidth = selected ? 3 : 2;
  const strokeDasharray = isStale
    ? "6 3"
    : isInvalid
    ? "4 2"
    : undefined;

  const boxShadow = selected
    ? `0 0 6px 2px ${typeColor}66`
    : undefined;

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Look up source/target node labels for hover label
  const nodes = useRFStore((s) => s.nodes);
  const sourceNode = nodes.find((n) => n.id === source);
  const targetNode = nodes.find((n) => n.id === target);
  const sourceLabel = (sourceNode?.data as { blockType?: string })?.blockType ?? "?";
  const targetLabel = (targetNode?.data as { blockType?: string })?.blockType ?? "?";

  const ariaLabel = dataType
    ? `Edge from ${sourceLabel} output to ${targetLabel} input, type ${dataType}`
    : `Edge from ${sourceLabel} to ${targetLabel}`;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: strokeColor,
          strokeWidth,
          strokeDasharray,
          filter: boxShadow ? `drop-shadow(0 0 4px ${typeColor}66)` : undefined,
        }}
        aria-label={ariaLabel}
      />

      {/* Selected edge label showing type info */}
      {selected && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              background: "rgba(14,18,24,0.92)",
              border: `1px solid ${typeColor}60`,
              borderRadius: 4,
              padding: "2px 7px",
              fontSize: 10,
              color: typeColor,
              fontFamily: "'SF Mono', 'Fira Code', monospace",
              letterSpacing: "0.03em",
              pointerEvents: "none",
              whiteSpace: "nowrap",
            }}
          >
            {sourceLabel} → {targetLabel} [{typeAbbr}]
          </div>
        </EdgeLabelRenderer>
      )}

      {/* Stale label */}
      {isStale && !selected && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              background: "rgba(14,18,24,0.85)",
              border: "1px solid rgba(251,191,36,0.4)",
              borderRadius: 3,
              padding: "1px 5px",
              fontSize: 9,
              color: "#FBBF24",
              fontFamily: "'SF Mono', 'Fira Code', monospace",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              pointerEvents: "none",
            }}
          >
            stale
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export default memo(StrategyEdge);
