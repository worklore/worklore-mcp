// Knowledge retrieval for one item: top-k chunks of the founder's published
// work by cosine similarity, with three rules the eval taught us:
//   - time:      only what was public BEFORE the item (no hindsight; the eval's
//                leakage rule and also the honest rule for a live draft);
//   - diversity: MMR plus at most `maxPerSource` chunks from one source, so one
//                long report can't fill the whole budget;
//   - exclusion: a caller-supplied filter (the eval drops the held-out reply).
// Pure and in-memory, so the eval, a script and an Edge Function share it. In
// the app, the same query runs in SQL (match_document_chunks in the migration
// draft) and this function re-ranks the ~40 candidates it returns.

import type { KnowledgeChunk } from "./types.ts";

export interface EmbeddedChunk extends KnowledgeChunk {
  embedding: number[];
}

export interface RetrieveOptions {
  k?: number;              // 6
  /** ISO datetime of the item; chunks must have been published strictly before it. */
  before?: string;
  maxPerSource?: number;   // 2
  /** MMR trade-off: 1 = pure relevance, 0 = pure diversity. */
  lambda?: number;         // 0.7
  candidates?: number;     // 40
  /**
   * Drop chunks below this cosine. gemini-embedding-001 at 768d is anisotropic:
   * on our KB the MEDIAN chunk scores 0.59–0.68 against any query and the best
   * 0.73–0.87, so the floor sits just above the median.
   */
  minScore?: number;       // 0.68
  exclude?: (c: KnowledgeChunk) => boolean;
}

export function cosine(a: number[], b: number[]): number {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s; // both normalised
}

/**
 * Was `published` public before `at`? A date-only value (2026-09-28) counts as
 * the whole day, so it is "before" only if the day is earlier than at's day:
 * a commit or story from the same day as the comment might be the answer to it.
 */
export function isBefore(published: string, at: string): boolean {
  if (!published) return false;
  if (published.length <= 10) return published < at.slice(0, 10);
  return published < at;
}

export function retrieve(query: number[], chunks: EmbeddedChunk[], opts: RetrieveOptions = {}): KnowledgeChunk[] {
  const k = opts.k ?? 6, lambda = opts.lambda ?? 0.7, maxPer = opts.maxPerSource ?? 2;
  const pool = chunks
    .filter((c) => !opts.before || isBefore(c.published_at, opts.before))
    .filter((c) => !opts.exclude?.(c))
    .map((c) => ({ c, s: cosine(query, c.embedding) }))
    .filter((x) => x.s >= (opts.minScore ?? 0.68))
    .sort((a, b) => b.s - a.s)
    .slice(0, opts.candidates ?? 40);

  const chosen: typeof pool = [];
  const perSource = new Map<string, number>();
  const src = (c: KnowledgeChunk) => c.source_url ?? c.source_ref ?? c.id;
  while (chosen.length < k) {
    let best = -1, bestVal = -Infinity;
    for (let i = 0; i < pool.length; i++) {
      const x = pool[i];
      if ((perSource.get(src(x.c)) ?? 0) >= maxPer) continue;
      const red = chosen.length ? Math.max(...chosen.map((y) => cosine(x.c.embedding, y.c.embedding))) : 0;
      const val = lambda * x.s - (1 - lambda) * red;
      if (val > bestVal) { bestVal = val; best = i; }
    }
    if (best < 0) break;
    const [x] = pool.splice(best, 1);
    chosen.push(x);
    perSource.set(src(x.c), (perSource.get(src(x.c)) ?? 0) + 1);
  }
  // deno-lint-ignore no-unused-vars
  return chosen.map(({ c: { embedding, ...rest }, s }) => ({ ...rest, score: Math.round(s * 1000) / 1000 }));
}
