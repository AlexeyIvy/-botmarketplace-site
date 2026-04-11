export type PortDataType = "Series<OHLCV>" | "Series<number>" | "Series<boolean>" | "Signal" | "RiskParams" | "OrderModel";
export declare const PORT_TYPE_COLOR: Record<PortDataType, string>;
export declare const PORT_TYPE_ABBR: Record<PortDataType, string>;
export type BlockCategory = "input" | "indicator" | "logic" | "execution" | "risk";
export declare const CATEGORY_COLOR: Record<BlockCategory, string>;
export declare const CATEGORY_LABEL: Record<BlockCategory, string>;
export interface PortDef {
    id: string;
    label: string;
    dataType: PortDataType;
    required: boolean;
}
export interface ParamDef {
    id: string;
    label: string;
    type: "number" | "select" | "string";
    defaultValue: unknown;
    options?: string[];
    min?: number;
    max?: number;
}
export interface BlockDef {
    type: string;
    label: string;
    category: BlockCategory;
    inputs: PortDef[];
    outputs: PortDef[];
    params: ParamDef[];
    description: string;
}
export declare const BLOCK_DEFS: BlockDef[];
export interface LabNodeData extends Record<string, unknown> {
    blockType: string;
    params: Record<string, unknown>;
    isStale?: boolean;
}
export declare const BLOCK_DEF_MAP: Record<string, BlockDef>;
export declare function isPortTypeCompatible(outputType: PortDataType, inputType: PortDataType): boolean;
