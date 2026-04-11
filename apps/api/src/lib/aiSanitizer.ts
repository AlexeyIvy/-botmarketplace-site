/**
 * AI Input Sanitizer (#232)
 *
 * Filters user-supplied prompts before sending to AI providers.
 * Detects common prompt-injection patterns and strips/rejects them.
 */

// ---------------------------------------------------------------------------
// Injection detection patterns
// ---------------------------------------------------------------------------

/**
 * Patterns that strongly indicate prompt injection attempts.
 * Each entry: [regex, human-readable label].
 */
const INJECTION_PATTERNS: Array<[RegExp, string]> = [
  // System/role override attempts
  [/\bsystem\s*:\s/i, "system-role-override"],
  [/\b(ignore|disregard|forget)\s+(all\s+)?(the\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)/i, "instruction-override"],
  [/\byou\s+are\s+now\b/i, "persona-hijack"],
  [/\bact\s+as\s+(a\s+)?(?:different|new|another)\b/i, "persona-hijack"],
  [/\bpretend\s+(you\s+are|to\s+be)\b/i, "persona-hijack"],

  // Data exfiltration attempts
  [/\b(reveal|show|output|print|display|leak)\s+(your|the|all)\s+(system\s+)?prompt/i, "prompt-extraction"],
  [/\brepeat\s+(the\s+)?(system|initial|above)\s+(prompt|message|instructions?)/i, "prompt-extraction"],
  [/\bwhat\s+(are|were)\s+your\s+(original\s+)?instructions/i, "prompt-extraction"],

  // Delimiter injection
  [/```\s*(system|assistant)\b/i, "delimiter-injection"],
  [/\[INST\]/i, "delimiter-injection"],
  [/<\|im_start\|>/i, "delimiter-injection"],
  [/<\|system\|>/i, "delimiter-injection"],

  // Encoded payloads (base64-wrapped injection)
  [/\bbase64\s*[:(]\s*[A-Za-z0-9+/=]{50,}/i, "encoded-payload"],
];

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface SanitizeResult {
  safe: boolean;
  cleaned: string;
  /** If unsafe, which pattern was matched */
  reason?: string;
}

/**
 * Sanitize a single user message before sending to AI.
 *
 * - Strips invisible Unicode characters (zero-width spaces, etc.)
 * - Normalizes excessive whitespace
 * - Checks against known injection patterns
 *
 * Returns { safe: true, cleaned } for clean messages,
 * or { safe: false, cleaned, reason } for detected injections.
 */
export function sanitizePrompt(input: string): SanitizeResult {
  // Strip invisible/control characters (keep newlines, tabs, standard space)
  let cleaned = input.replace(/[\u200B-\u200F\u2028-\u202F\uFEFF\u00AD]/g, "");

  // Normalize excessive whitespace (>3 consecutive newlines → 2)
  cleaned = cleaned.replace(/\n{4,}/g, "\n\n\n");

  // Check for injection patterns
  for (const [pattern, label] of INJECTION_PATTERNS) {
    if (pattern.test(cleaned)) {
      return { safe: false, cleaned, reason: label };
    }
  }

  return { safe: true, cleaned };
}

/**
 * Sanitize an array of chat messages (for /ai/chat endpoint).
 * Only user messages are checked; assistant messages pass through.
 *
 * Returns the sanitized messages array and the first rejection reason (if any).
 */
export function sanitizeMessages(
  messages: Array<{ role: string; content: string }>,
): { messages: Array<{ role: string; content: string }>; rejection?: string } {
  const sanitized = messages.map((msg) => {
    if (msg.role !== "user") return msg;
    const result = sanitizePrompt(msg.content);
    if (!result.safe) {
      return { ...msg, content: result.cleaned, _rejected: result.reason };
    }
    return { ...msg, content: result.cleaned };
  });

  const rejected = sanitized.find((m) => (m as { _rejected?: string })._rejected);
  const reason = (rejected as { _rejected?: string })?._rejected;

  return {
    messages: sanitized.map(({ role, content }) => ({ role, content })),
    rejection: reason,
  };
}
