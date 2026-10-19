// Gemini via the Generative Language REST API. The key travels only in the
// x-goog-api-key header, never in the URL (URLs end up in logs).

import { GenerateRequest, GenerateResult, Provider, ProviderError, userTurn } from "./provider.ts";

const BASE = "https://generativelanguage.googleapis.com/v1beta/models";

export interface GeminiOptions {
  apiKey: string;
  model?: string;          // default gemini-3.1-flash-lite (free tier: 500 req/day)
  maxRetries?: number;
  /** Thinking budget for models that think; 0 keeps flash-lite fast and cheap. */
  thinkingBudget?: number;
}

export class GeminiProvider implements Provider {
  readonly name = "gemini";
  readonly model: string;
  #key: string;
  #retries: number;
  #thinking?: number;

  constructor(opts: GeminiOptions) {
    if (!opts.apiKey) throw new ProviderError("GEMINI_API_KEY is not set");
    this.#key = opts.apiKey;
    this.model = opts.model ?? "gemini-3.1-flash-lite";
    this.#retries = opts.maxRetries ?? 3;
    this.#thinking = opts.thinkingBudget;
  }

  async generate(req: GenerateRequest): Promise<GenerateResult> {
    const body: Record<string, unknown> = {
      systemInstruction: { parts: [{ text: req.system }] },
      contents: [{ role: "user", parts: [{ text: userTurn(req) }] }],
      generationConfig: {
        temperature: req.temperature ?? 0.7,
        maxOutputTokens: req.max_output_tokens ?? 1024,
        ...(req.json ? { responseMimeType: "application/json" } : {}),
        ...(this.#thinking !== undefined ? { thinkingConfig: { thinkingBudget: this.#thinking } } : {}),
      },
    };
    const url = `${BASE}/${this.model}:generateContent`;
    let lastErr: ProviderError | null = null;
    for (let attempt = 0; attempt <= this.#retries; attempt++) {
      const t0 = Date.now();
      const res = await fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json", "x-goog-api-key": this.#key },
        body: JSON.stringify(body),
      });
      const latency = Date.now() - t0;
      if (res.ok) {
        // deno-lint-ignore no-explicit-any
        const data: any = await res.json();
        const cand = data.candidates?.[0];
        const text = (cand?.content?.parts ?? [])
          .filter((p: { thought?: boolean }) => !p.thought)
          .map((p: { text?: string }) => p.text ?? "").join("").trim();
        // Thinking models (gemini-3.5-flash) spend maxOutputTokens on thoughts first;
        // a cut-off draft is worse than an error the app can retry.
        if (cand?.finishReason === "MAX_TOKENS") {
          throw new ProviderError(`truncated at maxOutputTokens (thoughts ${data.usageMetadata?.thoughtsTokenCount ?? "?"} tokens); raise max_output_tokens or set thinkingBudget`);
        }
        if (!text) {
          throw new ProviderError(`empty response (finishReason=${cand?.finishReason ?? "?"}, block=${data.promptFeedback?.blockReason ?? "-"})`);
        }
        return {
          text,
          model: data.modelVersion ?? this.model,
          tokens_in: data.usageMetadata?.promptTokenCount ?? null,
          tokens_out: (data.usageMetadata?.candidatesTokenCount ?? 0) + (data.usageMetadata?.thoughtsTokenCount ?? 0) || null,
          latency_ms: latency,
          provider: this.name,
          usage: {
            input: data.usageMetadata?.promptTokenCount ?? 0,
            output: (data.usageMetadata?.candidatesTokenCount ?? 0) + (data.usageMetadata?.thoughtsTokenCount ?? 0),
            ...(data.usageMetadata?.cachedContentTokenCount ? { cache_read: data.usageMetadata.cachedContentTokenCount } : {}),
          },
        };
      }
      const errText = (await res.text()).slice(0, 500);
      const retryable = res.status === 429 || res.status >= 500;
      lastErr = new ProviderError(`gemini ${res.status}: ${errText}`, res.status, retryable);
      if (!retryable || attempt === this.#retries) break;
      // 429 on the free tier: respect the server's RetryInfo if present.
      const m = errText.match(/"retryDelay":\s*"(\d+)s"/);
      const delay = m ? Number(m[1]) * 1000 : 2000 * 2 ** attempt;
      await new Promise((r) => setTimeout(r, Math.min(delay, 60_000)));
    }
    throw lastErr!;
  }
}
