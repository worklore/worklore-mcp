// Claude via the Messages API (POST /v1/messages, anthropic-version 2023-06-01).
// The key travels only in the x-api-key header, never in a URL or a log line.
//
// Prompt caching: the system rules and the request's stable `context` (the
// project profile) go in as system blocks with cache_control on the last one,
// so every draft of a project within 5 minutes reads that prefix from cache.
// The per-item part (voice samples, sources, thread, task) is the user turn.
//
// Thinking is adaptive on the current models and can't be turned off on
// Sonnet/Opus 5.5; `effort` controls how much they think. Sampling parameters
// are rejected by these models, so req.temperature is ignored.

import { costUsd } from "./pricing.ts";
import { GenerateRequest, GenerateResult, Provider, ProviderError } from "./provider.ts";

const URL_MESSAGES = "https://api.anthropic.com/v1/messages";

export type Effort = "low" | "medium" | "high" | "xhigh" | "max";

export interface AnthropicOptions {
  apiKey: string;
  model?: string;            // default claude-sonnet-5-5
  effort?: Effort;           // default medium
  /** Per attempt. Default 90 s. */
  timeoutMs?: number;
  /** Retries on 429 / 529 (overloaded). Default 1. */
  maxRetries?: number;
  /** Floor for max_tokens: thinking counts against it. Default 8000. */
  minMaxTokens?: number;
  /** Test seam. */
  fetch?: typeof fetch;
  /** Test seam: backoff sleeper. */
  sleep?: (ms: number) => Promise<void>;
}

// Server-side refusal fallback (beta). Sonnet 5.5 accepts only the "default" form.
const FALLBACK_MODELS = /^claude-(sonnet|opus)-5-5/;

export class AnthropicProvider implements Provider {
  readonly name = "anthropic";
  readonly model: string;
  #key: string;
  #effort: Effort;
  #timeout: number;
  #retries: number;
  #minMax: number;
  #fetch: typeof fetch;
  #sleep: (ms: number) => Promise<void>;

  constructor(opts: AnthropicOptions) {
    if (!opts.apiKey) throw new ProviderError("ANTHROPIC_API_KEY is not set");
    this.#key = opts.apiKey;
    this.model = opts.model ?? "claude-sonnet-5-5";
    this.#effort = opts.effort ?? "medium";
    this.#timeout = opts.timeoutMs ?? 90_000;
    this.#retries = opts.maxRetries ?? 1;
    this.#minMax = opts.minMaxTokens ?? 8000;
    this.#fetch = opts.fetch ?? fetch;
    this.#sleep = opts.sleep ?? ((ms) => new Promise((r) => setTimeout(r, ms)));
  }

  body(req: GenerateRequest): Record<string, unknown> {
    const cache = { type: "ephemeral" };
    const system = req.context
      ? [{ type: "text", text: req.system }, { type: "text", text: req.context, cache_control: cache }]
      : [{ type: "text", text: req.system, cache_control: cache }];
    const prompt = req.json ? `${req.prompt}\n\nReturn only the JSON object, no prose, no code fence.` : req.prompt;
    return {
      model: this.model,
      max_tokens: Math.max(req.max_output_tokens ?? 0, this.#minMax),
      system,
      messages: [{ role: "user", content: prompt }],
      thinking: { type: "adaptive" },
      output_config: { effort: this.#effort },
      ...(FALLBACK_MODELS.test(this.model) ? { fallbacks: "default" } : {}),
    };
  }

  async generate(req: GenerateRequest): Promise<GenerateResult> {
    const body = JSON.stringify(this.body(req));
    const headers: Record<string, string> = {
      "content-type": "application/json",
      "x-api-key": this.#key,
      "anthropic-version": "2023-06-01",
    };
    if (FALLBACK_MODELS.test(this.model)) headers["anthropic-beta"] = "server-side-fallback-2026-07-01";

    let lastErr: ProviderError | null = null;
    for (let attempt = 0; attempt <= this.#retries; attempt++) {
      const t0 = Date.now();
      let res: Response;
      try {
        res = await this.#fetch(URL_MESSAGES, { method: "POST", headers, body, signal: AbortSignal.timeout(this.#timeout) });
      } catch (e) {
        const timedOut = (e as Error).name === "TimeoutError" || (e as Error).name === "AbortError";
        // A timed-out generation is not retried: it would double the wait. The caller falls back.
        throw new ProviderError(timedOut ? `anthropic: timed out after ${this.#timeout} ms` : `anthropic: ${(e as Error).message.slice(0, 200)}`, undefined, false);
      }
      const latency = Date.now() - t0;
      if (res.ok) {
        // deno-lint-ignore no-explicit-any
        const data: any = await res.json();
        if (data.stop_reason === "refusal") {
          throw new ProviderError(`anthropic: refused (${data.stop_details?.category ?? "no category"})`, 200, false);
        }
        if (data.stop_reason === "max_tokens") {
          throw new ProviderError(`anthropic: truncated at max_tokens (${data.usage?.output_tokens ?? "?"} out); raise max_output_tokens or lower effort`);
        }
        const text = (data.content ?? []).filter((b: { type: string }) => b.type === "text").map((b: { text: string }) => b.text).join("").trim();
        if (!text) throw new ProviderError(`anthropic: empty response (stop_reason=${data.stop_reason ?? "?"})`);
        const u = data.usage ?? {};
        const usage = {
          input: u.input_tokens ?? 0,
          output: u.output_tokens ?? 0,
          cache_read: u.cache_read_input_tokens ?? 0,
          cache_write: u.cache_creation_input_tokens ?? 0,
        };
        const model = data.model ?? this.model;
        return {
          text,
          model,
          provider: this.name,
          tokens_in: usage.input + usage.cache_read + usage.cache_write,
          tokens_out: usage.output,
          usage: { ...usage, cost_usd: costUsd(model, usage) },
          latency_ms: latency,
        };
      }
      const errText = (await res.text()).slice(0, 400).replace(/\s+/g, " ");
      const retryable = res.status === 429 || res.status === 529;
      lastErr = new ProviderError(`anthropic ${res.status}: ${errText}`, res.status, retryable);
      if (!retryable || attempt === this.#retries) break;
      const ra = Number(res.headers.get("retry-after"));
      const delay = Number.isFinite(ra) && ra > 0 ? ra * 1000 : 2000 * 2 ** attempt + Math.random() * 500;
      await this.#sleep(Math.min(delay, 20_000));
    }
    throw lastErr!;
  }
}
