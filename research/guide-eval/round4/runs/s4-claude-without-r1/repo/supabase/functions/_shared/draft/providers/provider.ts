// A model provider is anything that turns a prompt into text. The engine only
// sees this interface, so swapping Gemini for Anthropic/OpenAI is a config
// change, and drafts.provider/model/tokens record which one wrote what.

export interface GenerateRequest {
  system: string;
  /**
   * Optional stable prefix of the user turn (the project profile): the same for
   * every request of a project. A provider with prompt caching caches it with
   * the system rules; others send `${context}\n${prompt}` as the user turn.
   */
  context?: string;
  prompt: string;
  temperature?: number;
  max_output_tokens?: number;
  /** Ask for a JSON object back (used by the judge, not by drafting). */
  json?: boolean;
}

export interface GenerateResult {
  text: string;
  model: string;
  /** Who actually answered, when it can differ from Provider.name (a fallback chain). */
  provider?: string;
  /** All prompt tokens (uncached + cache writes + cache reads). */
  tokens_in: number | null;
  /** Output tokens, thinking included. */
  tokens_out: number | null;
  /** Breakdown where the provider reports it (drafts.tokens). */
  usage?: TokenUsage;
  latency_ms: number;
}

export interface TokenUsage {
  input: number;          // uncached prompt tokens
  output: number;
  cache_read?: number;
  cache_write?: number;
  /** USD at list price (pricing.ts), when the model's price is known. */
  cost_usd?: number;
}

/** The user turn as one string, for providers without a separate cached block. */
export function userTurn(req: GenerateRequest): string {
  return req.context ? `${req.context}\n${req.prompt}` : req.prompt;
}

export interface Provider {
  readonly name: string;   // drafts.provider
  readonly model: string;  // drafts.model
  generate(req: GenerateRequest): Promise<GenerateResult>;
}

export class ProviderError extends Error {
  constructor(message: string, readonly status?: number, readonly retryable = false) {
    super(message);
  }
}

export type EmbedTask = "document" | "query";

/** Text → vector, for knowledge retrieval. Vectors come back L2-normalised. */
export interface Embedder {
  readonly name: string;
  readonly model: string;
  readonly dims: number;
  /** titles: optional per-text document titles (Gemini uses them for "document" embeddings). */
  embed(texts: string[], task: EmbedTask, titles?: (string | undefined)[]): Promise<number[][]>;
}
