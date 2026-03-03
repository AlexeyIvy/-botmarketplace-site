export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AIChatOptions {
  maxTokens?: number;
  /** Request JSON-only output (for plan mode). OpenAI: response_format json_object.
   *  Anthropic: handled via system prompt instruction. */
  jsonMode?: boolean;
}

export interface AIProvider {
  chat(
    messages: ChatMessage[],
    system: string,
    options?: AIChatOptions,
  ): Promise<string>;
}

// ---------------------------------------------------------------------------
// OpenAI provider (fetch-based, no SDK)
// ---------------------------------------------------------------------------

class OpenAIProvider implements AIProvider {
  private readonly apiKey: string;
  private readonly model: string;

  constructor(apiKey: string, model: string) {
    this.apiKey = apiKey;
    this.model = model;
  }

  async chat(
    messages: ChatMessage[],
    system: string,
    options?: AIChatOptions,
  ): Promise<string> {
    const body: Record<string, unknown> = {
      model: this.model,
      messages: [{ role: "system", content: system }, ...messages],
      max_tokens: options?.maxTokens ?? 1024,
      stream: false,
    };
    if (options?.jsonMode) {
      body.response_format = { type: "json_object" };
    }

    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });

    if (!res.ok) {
      throw new ProviderError(res.status, `OpenAI error: ${res.status} ${res.statusText}`);
    }

    const json = (await res.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const text = json.choices?.[0]?.message?.content;
    if (!text) throw new ProviderError(502, "OpenAI returned empty response");
    return text;
  }
}

// ---------------------------------------------------------------------------
// Anthropic provider (fetch-based, no SDK)
// ---------------------------------------------------------------------------

class AnthropicProvider implements AIProvider {
  private readonly apiKey: string;
  private readonly model: string;

  constructor(apiKey: string, model: string) {
    this.apiKey = apiKey;
    this.model = model;
  }

  async chat(
    messages: ChatMessage[],
    system: string,
    options?: AIChatOptions,
  ): Promise<string> {
    // Anthropic has no JSON mode API param — the system prompt handles it.
    const body = {
      model: this.model,
      system,
      messages,
      max_tokens: options?.maxTokens ?? 1024,
      stream: false,
    };

    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": this.apiKey,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });

    if (!res.ok) {
      throw new ProviderError(res.status, `Anthropic error: ${res.status} ${res.statusText}`);
    }

    const json = (await res.json()) as {
      content?: Array<{ text?: string }>;
    };
    const text = json.content?.[0]?.text;
    if (!text) throw new ProviderError(502, "Anthropic returned empty response");
    return text;
  }
}

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ProviderError extends Error {
  constructor(
    public readonly providerStatus: number,
    message: string,
  ) {
    super(message);
    this.name = "ProviderError";
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

const DEFAULT_MODELS: Record<string, string> = {
  openai: "gpt-4o-mini",
  anthropic: "claude-haiku-4-5-20251001",
};

export function createProvider(): AIProvider {
  const apiKey = process.env.AI_API_KEY ?? "";
  const providerName = process.env.AI_PROVIDER ?? "openai";
  const model = process.env.AI_MODEL ?? DEFAULT_MODELS[providerName] ?? "gpt-4o-mini";

  if (providerName === "anthropic") {
    return new AnthropicProvider(apiKey, model);
  }
  return new OpenAIProvider(apiKey, model);
}

export function getConfiguredModel(): string {
  const providerName = process.env.AI_PROVIDER ?? "openai";
  return process.env.AI_MODEL ?? DEFAULT_MODELS[providerName] ?? "gpt-4o-mini";
}
