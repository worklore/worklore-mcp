// Gemini embeddings (gemini-embedding-001 on the free key). batchEmbedContents
// takes up to 100 texts per request; the key goes in the x-goog-api-key header.
// Below 3072 dimensions the vectors are not normalised by the API, so we
// normalise here (cosine = dot product downstream, and pgvector's <=> agrees).

import { Embedder, EmbedTask, ProviderError } from "./provider.ts";

const BASE = "https://generativelanguage.googleapis.com/v1beta/models";

export interface GeminiEmbedOptions {
  apiKey: string;
  model?: string;   // default gemini-embedding-001
  dims?: number;    // default 768 (Matryoshka truncation; matches vector(768) in the migration)
  /** Called once per HTTP request, for request budgets. */
  onRequest?: (n: number, ok: boolean) => void | Promise<void>;
}

export class GeminiEmbedder implements Embedder {
  readonly name = "gemini";
  readonly model: string;
  readonly dims: number;
  #key: string;
  #onRequest?: GeminiEmbedOptions["onRequest"];

  constructor(opts: GeminiEmbedOptions) {
    if (!opts.apiKey) throw new ProviderError("GEMINI_API_KEY is not set");
    this.#key = opts.apiKey;
    this.model = opts.model ?? "gemini-embedding-001";
    this.dims = opts.dims ?? 768;
    this.#onRequest = opts.onRequest;
  }

  async embed(texts: string[], task: EmbedTask, titles?: (string | undefined)[]): Promise<number[][]> {
    const out: number[][] = [];
    for (let i = 0; i < texts.length; i += 100) {
      const slice = texts.slice(i, i + 100);
      const body = {
        requests: slice.map((t, j) => ({
          model: `models/${this.model}`,
          content: { parts: [{ text: t }] },
          taskType: task === "document" ? "RETRIEVAL_DOCUMENT" : "RETRIEVAL_QUERY",
          ...(task === "document" && titles?.[i + j] ? { title: titles[i + j] } : {}),
          outputDimensionality: this.dims,
        })),
      };
      let vecs: number[][] | null = null;
      let lastErr = "";
      for (let attempt = 0; attempt < 4 && !vecs; attempt++) {
        const res = await fetch(`${BASE}/${this.model}:batchEmbedContents`, {
          method: "POST",
          headers: { "content-type": "application/json", "x-goog-api-key": this.#key },
          body: JSON.stringify(body),
        });
        await this.#onRequest?.(slice.length, res.ok);
        if (res.ok) {
          // deno-lint-ignore no-explicit-any
          const data: any = await res.json();
          vecs = (data.embeddings ?? []).map((e: { values: number[] }) => normalise(e.values));
          if (vecs!.length !== slice.length) throw new ProviderError(`embeddings: asked ${slice.length}, got ${vecs!.length}`);
          break;
        }
        const err = (await res.text()).slice(0, 400);
        lastErr = `${res.status}: ${err.replace(/\s+/g, " ").slice(0, 200)}`;
        if (res.status !== 429 && res.status < 500) throw new ProviderError(`gemini embed ${res.status}: ${err}`, res.status);
        const m = err.match(/"retryDelay":\s*"(\d+)s"/);
        await new Promise((r) => setTimeout(r, Math.min(m ? Number(m[1]) * 1000 : 3000 * 2 ** attempt, 60_000)));
      }
      if (!vecs) throw new ProviderError(`gemini embed: gave up after retries (${lastErr})`, 429, true);
      out.push(...vecs);
    }
    return out;
  }
}

export function normalise(v: number[]): number[] {
  const n = Math.hypot(...v) || 1;
  return v.map((x) => x / n);
}
