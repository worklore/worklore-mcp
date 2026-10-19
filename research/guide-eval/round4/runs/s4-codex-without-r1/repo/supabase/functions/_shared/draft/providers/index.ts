// Provider registry. Add a provider by implementing Provider (provider.ts) and
// adding a case here; nothing else in the engine changes.

import { AnthropicProvider, Effort } from "./anthropic.ts";
import { GeminiProvider } from "./gemini.ts";
import { GeminiEmbedder } from "./embed-gemini.ts";
import { Embedder, GenerateRequest, GenerateResult, Provider, ProviderError } from "./provider.ts";

export type { Embedder, EmbedTask, GenerateRequest, GenerateResult, Provider, TokenUsage } from "./provider.ts";
export { ProviderError, userTurn } from "./provider.ts";
export { AnthropicProvider } from "./anthropic.ts";
export type { AnthropicOptions, Effort } from "./anthropic.ts";
export { costUsd, PRICES } from "./pricing.ts";
export { GeminiProvider } from "./gemini.ts";
export { GeminiEmbedder } from "./embed-gemini.ts";

/** Embeddings for knowledge retrieval. Changing model or dims means re-embedding every chunk. */
export function makeEmbedder(cfg: { provider: "gemini"; model?: string; dims?: number }, env: (k: string) => string | undefined): Embedder {
  return new GeminiEmbedder({ apiKey: env("GEMINI_API_KEY") ?? "", model: cfg.model, dims: cfg.dims });
}

export interface ProviderConfig {
  provider: "gemini" | "anthropic" | "openai";
  model?: string;
  /** Gemini thinking budget in tokens (0 = off where allowed). */
  thinkingBudget?: number;
  /** Anthropic effort (default medium). */
  effort?: Effort;
}

/**
 * "anthropic:claude-sonnet-5-5" → {anthropic, claude-sonnet-5-5}. A bare model
 * name picks the provider by its prefix ("claude-…" → anthropic, else gemini),
 * so the old DRAFT_MODEL=gemini-3.1-flash-lite keeps working.
 */
export function parseModelSpec(spec: string): ProviderConfig {
  const s = spec.trim();
  const m = s.match(/^(gemini|anthropic|openai):(.+)$/);
  if (m) return { provider: m[1] as ProviderConfig["provider"], model: m[2].trim() };
  return { provider: /^claude-/.test(s) ? "anthropic" : "gemini", model: s || undefined };
}

/** env: a getter so this works with Deno.env.get in an Edge Function and with a plain map in tests. */
export function makeProvider(cfg: ProviderConfig, env: (k: string) => string | undefined): Provider {
  switch (cfg.provider) {
    case "gemini":
      return new GeminiProvider({ apiKey: env("GEMINI_API_KEY") ?? "", model: cfg.model, thinkingBudget: cfg.thinkingBudget });
    case "anthropic":
      return new AnthropicProvider({ apiKey: env("ANTHROPIC_API_KEY") ?? "", model: cfg.model, effort: cfg.effort });
    case "openai":
      // Slot: POST https://api.openai.com/v1/responses with Authorization: Bearer;
      // system → instructions, prompt → input; usage.input_tokens/output_tokens.
      throw new ProviderError("openai provider not implemented yet (env OPENAI_API_KEY)");
  }
}

/**
 * Primary first; on any error the fallback answers the same request. The
 * result says who answered (GenerateResult.provider/model), so drafts record
 * the model that actually wrote them.
 */
export class FallbackProvider implements Provider {
  readonly name: string;
  readonly model: string;
  constructor(readonly primary: Provider, readonly fallback: Provider, private onFallback?: (e: Error) => void) {
    this.name = primary.name;
    this.model = primary.model;
  }
  async generate(req: GenerateRequest): Promise<GenerateResult> {
    try {
      const r = await this.primary.generate(req);
      return { ...r, provider: r.provider ?? this.primary.name };
    } catch (e) {
      (this.onFallback ?? ((x: Error) => console.error(`provider ${this.primary.name}/${this.primary.model} failed, falling back to ${this.fallback.name}: ${x.message.slice(0, 200)}`)))(e as Error);
      const r = await this.fallback.generate(req);
      return { ...r, provider: r.provider ?? this.fallback.name };
    }
  }
}
