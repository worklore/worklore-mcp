// Decider adapter for TypeSafe AI's decision model "Jev"
// (POST https://api.typesafe.ai/v1/systemone; spec at https://api.typesafe.ai/openapi.json).
// Models: jev-latest, jev-preview (GET /v1/models). Auth: Authorization: Bearer
// <key>; the key comes from the environment (TYPESAFE_API_KEY), never logged.
// Jev answers typed questions only, so `notes` (free text such as the one-line
// summary) are not produced here; triage falls back to a summariser or the
// message's first sentence.

import { ProviderError } from "../providers/provider.ts";
import type { Answer, DecideOptions, Decider, Decision, Questions } from "./decider.ts";

const URL_ = "https://api.typesafe.ai/v1/systemone";

export interface TypeSafeOptions {
  apiKey: string;
  model?: string;       // jev-latest
  maxRetries?: number;  // 3
  timeoutMs?: number;   // 20 s
}

export class TypeSafeDecider implements Decider {
  readonly name = "typesafe";
  readonly model: string;
  #key: string;
  #retries: number;
  #timeout: number;

  constructor(opts: TypeSafeOptions) {
    if (!opts.apiKey) throw new ProviderError("TYPESAFE_API_KEY is not set");
    this.#key = opts.apiKey;
    this.model = opts.model ?? "jev-latest";
    this.#retries = opts.maxRetries ?? 3;
    this.#timeout = opts.timeoutMs ?? 20_000;
  }

  async decide(state: string | Record<string, unknown>, questions: Questions, _opts: DecideOptions = {}): Promise<Decision> {
    // Our "boolean" is their "noul"; choice and score are the same shape.
    const qs = Object.fromEntries(Object.entries(questions).map(([id, q]) =>
      [id, q.type === "boolean" ? { type: "noul", instructions: q.instructions, criteria: q.criteria } : q]));
    const body = JSON.stringify({ model: this.model, state, questions: qs });
    let last: ProviderError | null = null;
    for (let attempt = 0; attempt <= this.#retries; attempt++) {
      const t0 = Date.now();
      let res: Response;
      try {
        res = await fetch(URL_, {
          method: "POST",
          headers: { "content-type": "application/json", authorization: `Bearer ${this.#key}` },
          body, signal: AbortSignal.timeout(this.#timeout),
        });
      } catch (e) {
        last = new ProviderError(`typesafe: ${(e as Error).message}`, 0, true);
        await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
        continue;
      }
      const latency = Date.now() - t0;
      if (res.ok) {
        // deno-lint-ignore no-explicit-any
        const data: any = await res.json();
        const answers: Record<string, Answer> = {};
        for (const [id, q] of Object.entries(questions)) {
          const a = data.answers?.[id];
          if (!a) throw new ProviderError(`typesafe: no answer for '${id}'`);
          if (q.type === "choice") {
            answers[id] = { answer: a.choice, probabilities: a.probabilities ?? {}, confidence: Number(a.confidence ?? 0) };
          } else if (q.type === "boolean") {
            const p = Number(a.noul);
            answers[id] = { answer: p >= 0.5, probabilities: { true: p, false: Math.round((1 - p) * 1000) / 1000 }, confidence: Math.max(p, 1 - p) };
          } else {
            answers[id] = { answer: Number(a.score), probabilities: {}, confidence: Number(a.confidence ?? 0) };
          }
        }
        return {
          answers, decider: this.name, model: data.model ?? this.model,
          usage: { tokens_in: data.usage?.input_tokens ?? null, tokens_out: data.usage?.output_tokens ?? null },
          latency_ms: latency,
        };
      }
      const txt = (await res.text()).slice(0, 300);
      const retryable = res.status === 429 || res.status >= 500;
      last = new ProviderError(`typesafe ${res.status}: ${txt}`, res.status, retryable);
      if (!retryable) break;
      const ra = Number(res.headers.get("retry-after") ?? 0);
      await new Promise((r) => setTimeout(r, Math.max(ra * 1000, 1000 * 2 ** attempt)));
    }
    throw last!;
  }
}
