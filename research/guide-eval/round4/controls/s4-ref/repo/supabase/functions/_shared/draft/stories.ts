// Which of her stories fits a comment, for "Invite to try": the story is the
// invitation (a link to how she solved the same kind of problem), so it must
// be about THEIR problem, not just the same topic.
//
// Selection is two cheap steps, never a pass over every story:
// 1. the vector index returns the nearest story chunks to the comment (SQL,
//    match_document_chunks with kinds ['story'], HNSW: a few dozen rows);
// 2. this pure re-rank groups them per story and adds a keyword bonus for
//    words the comment shares with the story's title. Titles are short and
//    specific ("zsh", "MCP Registry", "Figma"), so a shared title word is
//    strong evidence; embeddings alone rank "same area" too high.
// A story below the floor is not offered: then the draft invites with the
// product link, as before.

import type { KnowledgeChunk } from "./types.ts";
import { terms } from "./text.ts";

export interface StoryChunk extends KnowledgeChunk {
  /** Cosine to the comment (match_document_chunks.similarity). */
  similarity: number;
}

export interface StoryPick {
  title: string;
  url: string;
  /** The chunk that matched best: what the draft may say about the story. */
  chunk: KnowledgeChunk;
  similarity: number;
  /** Comment words found in the title. */
  shared: string[];
  score: number;
}

export interface PickOptions {
  /** At most this many stories offered to the draft. */
  k?: number;            // 3
  /** Minimum score (cosine + keyword bonus). */
  floor?: number;        // 0.74
  /** Bonus per shared title word, and its cap. */
  perWord?: number;      // 0.03
  maxBonus?: number;     // 0.09
  /** Titles not to offer (her post they comment on: they have read it). */
  excludeTitles?: (string | null | undefined)[];
  /** Links already in the thread. */
  excludeUrls?: (string | null | undefined)[];
}

/** "Doc title › Section" → "Doc title". */
export function storyTitle(chunkTitle: string): string {
  return chunkTitle.split(" › ")[0].trim();
}

const norm = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();

/** Pure. The best stories for `comment` among the nearest story chunks. */
export function pickStories(comment: string, chunks: StoryChunk[], opts: PickOptions = {}): StoryPick[] {
  const k = opts.k ?? 3, floor = opts.floor ?? 0.74, perWord = opts.perWord ?? 0.03, maxBonus = opts.maxBonus ?? 0.09;
  const skipTitles = new Set((opts.excludeTitles ?? []).filter(Boolean).map((t) => norm(t!)));
  const skipUrls = new Set((opts.excludeUrls ?? []).filter(Boolean).map((u) => u!.replace(/\/$/, "")));
  const want = new Set(terms(comment));
  const best = new Map<string, StoryChunk>();
  for (const c of chunks) {
    if (!c.source_url) continue; // a story she can't link is no invitation
    const prev = best.get(c.source_url);
    if (!prev || c.similarity > prev.similarity) best.set(c.source_url, c);
  }
  const out: StoryPick[] = [];
  for (const [url, c] of best) {
    const title = storyTitle(c.title);
    if (skipTitles.has(norm(title)) || skipUrls.has(url.replace(/\/$/, ""))) continue;
    const shared = [...new Set(terms(title))].filter((t) => want.has(t));
    const score = c.similarity + Math.min(maxBonus, shared.length * perWord);
    if (score < floor) continue;
    out.push({ title, url, chunk: c, similarity: c.similarity, shared, score: Math.round(score * 1000) / 1000 });
  }
  return out.sort((a, b) => b.score - a.score).slice(0, k);
}
