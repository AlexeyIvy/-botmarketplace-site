/**
 * Task 29 — AI Explainability module
 *
 * Prompt templates + LLM call helpers for the four explain features:
 * 1. Explain Graph — strategy summary in plain language
 * 2. Explain Validation Issue — error explanation + suggested fix
 * 3. Explain Run Delta — differences between two backtest runs
 * 4. Suggest Safer Risk Config — flag risky SL/TP configurations
 *
 * Safety boundaries (docs/24 §8.5):
 * - No compiler bypass — suggestions are advisory only
 * - No validation bypass — AI cannot produce invalid graph states
 * - No trade execution — operates on backtest data only
 * - No secret access — no API keys, credentials, or private data
 */

import { createProvider, ProviderError } from "./ai/provider.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ExplainGraphInput {
  compiledDsl: Record<string, unknown>;
  graphJson: Record<string, unknown>;
}

export interface ExplainValidationInput {
  issue: { severity: string; message: string; nodeId?: string };
  nodeContext: Record<string, unknown>;
}

export interface ExplainDeltaInput {
  runA: Record<string, unknown>;
  runB: Record<string, unknown>;
  metricsDiff: Record<string, unknown>;
}

export interface ExplainRiskInput {
  riskParams: Record<string, unknown>;
}

export interface ExplainResult {
  explanation: string;
}

export interface RiskResult {
  warning: string | null;
  suggestions: string[];
}

// ---------------------------------------------------------------------------
// System prompts — kept minimal + focused per safety boundaries
// ---------------------------------------------------------------------------

const SAFETY_PREAMBLE = `You are an AI assistant for a trading strategy IDE. You explain strategy configurations and backtest results.

HARD SAFETY RULES — you must NEVER:
- Suggest bypassing validation or the compiler
- Suggest or execute any live trades
- Access, mention, or output API keys, credentials, or secrets
- Produce graph states or DSL directly — only explain in natural language

Your role is ADVISORY ONLY. Users apply changes through the graph editor.`;

function buildExplainGraphPrompt(input: ExplainGraphInput): string {
  const dslSummary = JSON.stringify(input.compiledDsl, null, 2).slice(0, 3000);
  const graphSummary = JSON.stringify(input.graphJson, null, 2).slice(0, 2000);

  return `${SAFETY_PREAMBLE}

Summarize this trading strategy in 2-3 plain-language sentences. Describe what the strategy does, which indicators it uses, and what the entry/exit logic is. Be concise and avoid jargon.

Compiled DSL:
${dslSummary}

Graph structure:
${graphSummary}`;
}

function buildExplainValidationPrompt(input: ExplainValidationInput): string {
  const issueJson = JSON.stringify(input.issue);
  const contextJson = JSON.stringify(input.nodeContext, null, 2).slice(0, 2000);

  return `${SAFETY_PREAMBLE}

A user has a validation error in their strategy graph. Explain the error in plain language and suggest how to fix it. Keep your response to 2-3 sentences.

Validation issue:
${issueJson}

Node context:
${contextJson}`;
}

function buildExplainDeltaPrompt(input: ExplainDeltaInput): string {
  const runAJson = JSON.stringify(input.runA, null, 2).slice(0, 1500);
  const runBJson = JSON.stringify(input.runB, null, 2).slice(0, 1500);
  const diffJson = JSON.stringify(input.metricsDiff, null, 2);

  return `${SAFETY_PREAMBLE}

Compare these two backtest runs and summarize what changed and the likely cause in 2-4 sentences. Focus on the most significant metric differences.

Run A:
${runAJson}

Run B:
${runBJson}

Metrics diff:
${diffJson}`;
}

function buildRiskPrompt(input: ExplainRiskInput): string {
  const paramsJson = JSON.stringify(input.riskParams, null, 2);

  return `${SAFETY_PREAMBLE}

Analyze these risk management parameters (stop-loss / take-profit configuration) for a trading strategy. If the configuration looks risky (e.g., very wide stop-loss, no take-profit, extreme values), provide a short warning and suggest safer bounds. If the configuration looks reasonable, respond with "SAFE".

Respond in JSON format:
{"warning": "string or null if safe", "suggestions": ["suggestion 1", "suggestion 2"]}

Risk parameters:
${paramsJson}`;
}

// ---------------------------------------------------------------------------
// LLM call wrapper — reuses existing provider infrastructure
// ---------------------------------------------------------------------------

const MAX_EXPLAIN_TOKENS = 512;

export async function callExplain(systemPrompt: string, jsonMode = false): Promise<string> {
  const provider = createProvider();
  return provider.chat(
    [{ role: "user", content: "Please analyze the above and respond." }],
    systemPrompt,
    { maxTokens: MAX_EXPLAIN_TOKENS, jsonMode },
  );
}

// ---------------------------------------------------------------------------
// Public API — each function validates input, builds prompt, calls LLM
// ---------------------------------------------------------------------------

export async function explainGraph(input: ExplainGraphInput): Promise<ExplainResult> {
  if (!input.compiledDsl || typeof input.compiledDsl !== "object") {
    throw new ExplainInputError("compiledDsl is required and must be an object");
  }
  if (!input.graphJson || typeof input.graphJson !== "object") {
    throw new ExplainInputError("graphJson is required and must be an object");
  }

  const prompt = buildExplainGraphPrompt(input);
  const explanation = await callExplain(prompt);
  return { explanation };
}

export async function explainValidation(input: ExplainValidationInput): Promise<ExplainResult> {
  if (!input.issue || typeof input.issue !== "object") {
    throw new ExplainInputError("issue is required and must be an object");
  }
  if (!input.issue.message || typeof input.issue.message !== "string") {
    throw new ExplainInputError("issue.message is required");
  }

  const prompt = buildExplainValidationPrompt(input);
  const explanation = await callExplain(prompt);
  return { explanation };
}

export async function explainDelta(input: ExplainDeltaInput): Promise<ExplainResult> {
  if (!input.runA || typeof input.runA !== "object") {
    throw new ExplainInputError("runA is required and must be an object");
  }
  if (!input.runB || typeof input.runB !== "object") {
    throw new ExplainInputError("runB is required and must be an object");
  }
  if (!input.metricsDiff || typeof input.metricsDiff !== "object") {
    throw new ExplainInputError("metricsDiff is required and must be an object");
  }

  const prompt = buildExplainDeltaPrompt(input);
  const explanation = await callExplain(prompt);
  return { explanation };
}

export async function suggestRisk(input: ExplainRiskInput): Promise<RiskResult> {
  if (!input.riskParams || typeof input.riskParams !== "object") {
    throw new ExplainInputError("riskParams is required and must be an object");
  }

  const prompt = buildRiskPrompt(input);
  const raw = await callExplain(prompt, true);

  try {
    const parsed = JSON.parse(raw) as { warning?: string | null; suggestions?: string[] };
    return {
      warning: parsed.warning ?? null,
      suggestions: Array.isArray(parsed.suggestions) ? parsed.suggestions : [],
    };
  } catch {
    // Fallback: treat raw text as a warning if JSON parsing fails
    return { warning: raw, suggestions: [] };
  }
}

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export class ExplainInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ExplainInputError";
  }
}

// Re-export ProviderError for route-level error handling
export { ProviderError };
