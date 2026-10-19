// Context assembly under a token budget.
//
// Truncation is by priority, never by cutting the middle of the thread:
//   must keep   the comment itself, the profile, the message it answers,
//               the post's title + opening, 3 voice samples
//   then add    (nearest first) older messages in the chain, more of the post,
//               voice samples 4–6, person summary and touches, memory snippets,
//               knowledge chunks (her published work, retrieved per item)
// Anything that does not fit is dropped whole and noted in the report, and a
// dropped run of chain messages becomes one "[n earlier messages omitted]" line,
// so the model always sees the thread's beginning (the post) and its end.

import { bm25, estimateTokens, median, terms, truncateToTokens, words } from "./text.ts";
import type { ContextReport, DraftRequest, KnowledgeChunk, MemorySnippet, ThreadMessage, VoiceSample } from "./types.ts";

export interface AssembleOptions {
  budgetTokens?: number;     // default 6000 (7500 with knowledge), clamp 4000–8000
  minVoice?: number;         // 3
  maxVoice?: number;         // 6
  maxMemory?: number;        // 3
  maxKnowledge?: number;     // 6
}

export interface Assembled {
  profile: string;
  post: string;              // title + (part of) the post
  chain: ThreadMessage[];    // kept chain messages (oldest first)
  omittedChain: number;
  item: ThreadMessage;
  voice: VoiceSample[];
  person: string | null;
  memory: MemorySnippet[];
  knowledge: KnowledgeChunk[];
  targetWords: [number, number];
  report: ContextReport;
}

const CAP = { item: 1500, profile: 700, chainMsg: 600, postMin: 250, postMax: 1200, voice: 300, person: 250, touch: 120, memory: 180, knowledge: 450 };

export function profileText(p: DraftRequest["project"]): string {
  const lines = [
    `Product: ${p.name}${p.one_liner ? ` (${p.one_liner})` : ""}`,
    p.audience && `For: ${p.audience}`,
    p.views && `What we believe / positions:\n${p.views}`,
    p.red_lines && `Never promise or say:\n${p.red_lines}`,
    p.tone && `Tone: ${p.tone}`,
    p.links?.length && `Links you may use (only these):\n${p.links.map((l) => `- ${l.title}: ${l.url}`).join("\n")}`,
    p.founder_name && `You are ${p.founder_name}${p.founder_handle ? ` (@${p.founder_handle})` : ""}, the founder.`,
    p.voice_notes && `How ${p.founder_name ?? "the founder"} writes: ${p.voice_notes}`,
  ].filter(Boolean);
  return truncateToTokens(lines.join("\n"), CAP.profile);
}

function voiceDoc(v: VoiceSample) { return `${v.in_reply_to ?? ""}\n${v.text}`; }

/** Rank voice samples by similarity to this item; ties broken by recency. */
export function rankVoice(req: DraftRequest): VoiceSample[] {
  // A sample already visible in the thread (her earlier message here) adds nothing.
  const norm = (s: string) => s.replace(/\s+/g, " ").trim().slice(0, 200);
  const inThread = new Set(req.context.chain.map((m) => norm(m.text)));
  const pool = req.voice_pool.filter((v) => !inThread.has(norm(v.text)));
  if (!pool.length) return [];
  const parent = req.context.chain.at(-1)?.text ?? "";
  const query = [req.context.item.text, parent, req.context.post?.title ?? ""].join("\n");
  const scores = bm25(query, pool.map(voiceDoc));
  const idx = pool.map((_, i) => i).sort((a, b) =>
    scores[b] - scores[a] || (pool[b].posted_at ?? "").localeCompare(pool[a].posted_at ?? ""));
  // Light diversity: skip a sample that is near-duplicate of one already chosen.
  const chosen: number[] = [];
  for (const i of idx) {
    const ti = new Set(terms(pool[i].text));
    const dup = chosen.some((j) => {
      const tj = new Set(terms(pool[j].text));
      const inter = [...ti].filter((t) => tj.has(t)).length;
      return inter / Math.max(1, Math.min(ti.size, tj.size)) > 0.8;
    });
    if (!dup) chosen.push(i);
  }
  return chosen.map((i) => pool[i]);
}

export function rankMemory(req: DraftRequest): MemorySnippet[] {
  const pool = req.memory_pool;
  if (!pool.length) return [];
  const query = [req.context.item.text, req.context.chain.at(-1)?.text ?? "", req.context.post?.title ?? ""].join("\n");
  const scores = bm25(query, pool.map((m) => m.text));
  return pool.map((m, i) => ({ m, s: scores[i] })).filter((x) => x.s > 0).sort((a, b) => b.s - a.s).map((x) => x.m);
}

/**
 * Her typical length for this kind of message: median of the most similar
 * samples, nudged by the comment's length. A short message is sized from her
 * short replies, and no reply runs much longer than what it answers (her
 * long dev.to comments made a 60-word reply into a 130-word draft).
 */
export function targetLength(req: DraftRequest, similar: VoiceSample[]): [number, number] {
  const itemW = words(req.context.item.text);
  const shortOnly = (n: number) => n <= Math.max(60, itemW * 2);
  const all = req.voice_pool.map((v) => words(v.text));
  const short = all.filter(shortOnly);
  const useShort = itemW < 120 && short.length >= 5;
  const pool = useShort ? short : all;
  const near = similar.slice(0, 6).map((v) => words(v.text)).filter((n) => !useShort || shortOnly(n));
  const base = near.length >= 3 ? median(near) * 0.6 + median(pool) * 0.4 : (pool.length ? median(pool) : 60);
  const nudged = itemW < 25 ? base * 0.7 : itemW > 200 ? base * 1.15 : base;
  const mid = Math.max(15, Math.min(Math.round(nudged), Math.max(30, Math.round(itemW * 1.5))));
  return [Math.round(mid * 0.6), Math.round(mid * 1.35)];
}

export function assemble(req: DraftRequest, opts: AssembleOptions = {}): Assembled {
  const hasKnowledge = !!req.knowledge?.length;
  const budget = Math.min(8000, Math.max(4000, opts.budgetTokens ?? (hasKnowledge ? 7500 : 6000)));
  const maxKnowledge = opts.maxKnowledge ?? 6;
  const minVoice = opts.minVoice ?? 3, maxVoice = opts.maxVoice ?? 6, maxMemory = opts.maxMemory ?? 3;
  const sections: ContextReport["sections"] = [];
  let used = 0;
  const take = (name: string, text: string, opt: { truncated?: boolean } = {}) => {
    const t = estimateTokens(text);
    used += t;
    sections.push({ name, tokens: t, ...(opt.truncated ? { truncated: true } : {}) });
  };
  const fits = (text: string) => used + estimateTokens(text) <= budget;
  const drop = (name: string, text: string) => sections.push({ name, tokens: estimateTokens(text), dropped: true });

  // Rules and output scaffolding cost ~900 tokens; reserve them.
  used += 900;
  sections.push({ name: "rules", tokens: 900 });

  // --- must keep
  const profile = profileText(req.project);
  take("profile", profile);
  const itemText = truncateToTokens(req.context.item.text, CAP.item);
  const item = { ...req.context.item, text: itemText };
  take("item", itemText, { truncated: itemText !== req.context.item.text });

  const chainAll = req.context.chain.map((m) => ({ ...m, text: truncateToTokens(m.text, CAP.chainMsg) }));
  const keep = new Set<number>();
  if (chainAll.length) { keep.add(chainAll.length - 1); take("chain[-1]", chainAll.at(-1)!.text); }

  const post = req.context.post;
  const postHead = post ? `${post.title ? `"${post.title}"` : ""}${post.author ? ` by @${post.author}${post.is_owner ? " (you)" : ""}` : ""}` : "";
  let postBody = post ? truncateToTokens(post.text, CAP.postMin) : "";
  take("post", postHead + "\n" + postBody, { truncated: !!post && postBody !== post.text });

  const ranked = rankVoice(req);
  const voice: VoiceSample[] = [];
  const clipV = (v: VoiceSample) => ({ ...v, text: truncateToTokens(v.text, CAP.voice), in_reply_to: v.in_reply_to ? truncateToTokens(v.in_reply_to, 80) : undefined });
  for (const v of ranked.slice(0, minVoice)) { const c = clipV(v); voice.push(c); take(`voice:${v.id}`, voiceDoc(c)); }

  // --- then add, nearest-first
  for (let i = chainAll.length - 2; i >= 0; i--) {
    const m = chainAll[i];
    // Contiguous from the end: once one does not fit, everything older goes too,
    // so the kept part is always an unbroken tail of the thread.
    if (fits(m.text)) { keep.add(i); take(`chain[${i}]`, m.text); } else { for (let j = i; j >= 0; j--) drop(`chain[${j}]`, chainAll[j].text); break; }
  }
  if (post && post.text.length > postBody.length) {
    const more = truncateToTokens(post.text, CAP.postMax);
    const extra = estimateTokens(more) - estimateTokens(postBody);
    if (used + extra <= budget) { used += extra; postBody = more; sections.push({ name: "post+", tokens: extra }); }
  }
  let person: string | null = null;
  if (req.person) {
    const p = req.person;
    const head = [
      `@${p.handle}${p.display_name ? ` (${p.display_name})` : ""}${p.stage ? `, stage: ${p.stage}` : ""}`,
      p.summary && `Who: ${p.summary}`, p.builds && `Builds: ${p.builds}`,
      p.cares_about && `Cares about: ${p.cares_about}`, p.notes && `Founder's notes: ${p.notes}`,
    ].filter(Boolean).join("\n");
    const s = truncateToTokens(head, CAP.person);
    if (fits(s)) { person = s; take("person", s); } else drop("person", s);
  }
  const memRanked = rankMemory(req);
  const memory: MemorySnippet[] = [];
  for (const m of memRanked.slice(0, 2)) {
    const c = { ...m, text: truncateToTokens(m.text, CAP.memory) };
    if (fits(c.text)) { memory.push(c); take(`memory:${m.id}`, c.text); } else drop(`memory:${m.id}`, c.text);
  }
  // Knowledge comes before the extra voice samples: with her published work in
  // reach, a concrete fact of hers is worth more than a fourth style example.
  const knowledge: KnowledgeChunk[] = [];
  for (const k of (req.knowledge ?? []).slice(0, maxKnowledge)) {
    const text = truncateToTokens(k.text, CAP.knowledge);
    const c = { ...k, text };
    if (fits(text)) { knowledge.push(c); take(`knowledge:${k.id}`, text, { truncated: text !== k.text }); } else drop(`knowledge:${k.id}`, text);
  }
  for (const v of ranked.slice(minVoice, maxVoice)) {
    const c = clipV(v);
    if (fits(voiceDoc(c))) { voice.push(c); take(`voice:${v.id}`, voiceDoc(c)); }
  }
  if (person && req.person?.touches?.length) {
    const touches = [...req.person.touches].sort((a, b) => b.occurred_at.localeCompare(a.occurred_at)).slice(0, 4);
    const lines: string[] = [];
    for (const t of touches) {
      const line = `- ${t.occurred_at.slice(0, 10)} ${t.direction === "in" ? "they wrote" : "you wrote"}: ${truncateToTokens(t.text, CAP.touch)}`;
      if (fits(line)) { lines.push(line); take("touch", line); } else break;
    }
    if (lines.length) person += `\nEarlier touches (newest first):\n${lines.join("\n")}`;
  }
  for (const m of memRanked.slice(2, maxMemory)) {
    const c = { ...m, text: truncateToTokens(m.text, CAP.memory) };
    if (fits(c.text)) { memory.push(c); take(`memory:${m.id}`, c.text); }
  }

  const kept = [...keep].sort((a, b) => a - b);
  const chain = kept.map((i) => chainAll[i]);
  const omittedChain = chainAll.length - kept.length;

  return {
    profile, item, voice, person, memory, knowledge, chain, omittedChain,
    post: post ? `${postHead}\n${postBody}`.trim() : "",
    targetWords: targetLength(req, ranked),
    report: { budget_tokens: budget, used_tokens: used, sections, voice_sample_ids: voice.map((v) => v.id), memory_ids: memory.map((m) => m.id), knowledge_ids: knowledge.map((k) => k.id) },
  };
}
