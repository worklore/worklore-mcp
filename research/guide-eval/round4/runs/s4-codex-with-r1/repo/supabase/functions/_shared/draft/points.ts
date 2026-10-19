// Points she could make: before a redraft, the app asks her what her point is
// and offers 2–3 candidates. They come only from what she has already said:
// her messages in this thread, what she wrote to this person before, and her
// published work. The model picks and condenses; it never adds a view of its
// own (a redraft that invented "save the prompt as the why" is the reason).

import type { Provider } from "./providers/provider.ts";
import type { DraftRequest } from "./types.ts";

export interface PointSource {
  id: string;                 // T1 (thread), P1 (earlier with this person), K1 (published work)
  kind: "thread" | "earlier" | "published";
  title: string;
  url: string | null;
  text: string;
}

export interface Point {
  text: string;
  /** Where it comes from; `excerpt` is the source text she can open in the app. */
  source: Omit<PointSource, "text"> & { excerpt: string };
}

const CAP = { thread: 2500, earlier: 600, published: 900 };

/** Pure: her own material for this item, each with an id the model cites. */
export function pointSources(req: DraftRequest): PointSource[] {
  const out: PointSource[] = [];
  const mine = req.context.chain.filter((m) => m.is_owner);
  mine.forEach((m, i) => out.push({ id: `T${i + 1}`, kind: "thread", title: "Your comment in this thread", url: null, text: m.text.slice(0, CAP.thread) }));
  (req.person?.touches ?? []).filter((t) => t.direction === "out").slice(0, 3)
    .forEach((t, i) => out.push({ id: `P${i + 1}`, kind: "earlier", title: `You wrote to them on ${t.occurred_at.slice(0, 10)}`, url: t.url ?? null, text: t.text.slice(0, CAP.earlier) }));
  (req.knowledge ?? []).slice(0, 4)
    .forEach((k, i) => out.push({ id: `K${i + 1}`, kind: "published", title: k.title, url: k.source_url, text: k.text.slice(0, CAP.published) }));
  return out;
}

export const POINTS_SYSTEM = `You help a founder decide what to say in a reply. You do not write the reply.
From HER material only (the numbered sources), pick up to 3 distinct points she could make that answer this message.
Rules:
- Each point is a view or fact she already stated in that source. Restate it in one sentence, in her words where possible (first person, as she would say it).
- Never add a view, idea, example or conclusion that is not in her source. Fewer points is better than an invented one.
- A point must bear on what they wrote. Skip sources that don't.
- Prefer her comment in this thread when they reply to it.
Answer with JSON only: {"points":[{"source":"T1","text":"..."}]}`;

/** Pure: the user turn for the points request. */
export function pointsPrompt(req: DraftRequest, sources: PointSource[]): string {
  const item = req.context.item;
  const parent = req.context.chain.at(-1);
  return [
    req.context.post?.title ? `Post: "${req.context.post.title}"` : null,
    parent && !parent.is_owner ? `They answer @${parent.author}:\n${parent.text.slice(0, 1200)}` : null,
    `Message to answer, by @${item.author}:\n${item.text.slice(0, 2000)}`,
    `Her material:\n${sources.map((s) => `[${s.id}] ${s.title}\n${s.text}`).join("\n\n")}`,
  ].filter(Boolean).join("\n\n");
}

/** Pure: the model's JSON → points with their sources; unknown sources and duplicates are dropped. */
export function parsePoints(raw: string, sources: PointSource[]): Point[] {
  const json = raw.slice(raw.indexOf("{"), raw.lastIndexOf("}") + 1);
  let list: unknown[] = [];
  try { list = (JSON.parse(json) as { points?: unknown[] }).points ?? []; } catch { return []; }
  const byId = new Map(sources.map((s) => [s.id, s]));
  const seen = new Set<string>();
  const out: Point[] = [];
  for (const p of list) {
    const o = (p ?? {}) as { source?: unknown; text?: unknown };
    const src = byId.get(String(o.source ?? "").replace(/[\[\]]/g, "").trim());
    const text = String(o.text ?? "").replace(/\s+/g, " ").trim();
    if (!src || text.length < 8 || seen.has(text.toLowerCase())) continue;
    seen.add(text.toLowerCase());
    const { text: excerpt, ...rest } = src;
    out.push({ text: text.slice(0, 400), source: { ...rest, excerpt } });
    if (out.length === 3) break;
  }
  return out;
}

export async function suggestPoints(req: DraftRequest, provider: Provider): Promise<{ points: Point[]; model: string | null }> {
  const sources = pointSources(req);
  if (!sources.length) return { points: [], model: null };
  const out = await provider.generate({ system: POINTS_SYSTEM, prompt: pointsPrompt(req, sources), temperature: 0.2, max_output_tokens: 1200, json: true });
  return { points: parsePoints(out.text, sources), model: out.model };
}
