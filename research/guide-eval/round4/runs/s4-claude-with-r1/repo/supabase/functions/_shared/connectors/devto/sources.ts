// dev.to as a source (docs/ARCHITECTURE.md › Sources: voice and knowledge).
//
// ownWriting: her own comments, as voice-sample candidates.
//   - Server, public API: the comment trees of her own articles and of the
//     articles she commented on (accounts.settings.watch_articles); her
//     comments there come with the message they answered. Cached per article
//     by comments_count, so an unchanged article costs no tree request.
//   - Phone: the full list of her comments is the page /{username}/comments,
//     which Forem shows only to signed-in visitors (users/show.html.erb renders
//     comments_locked_cta otherwise). The phone reads it with her session and
//     sends the links (deviceRefs); the server then reads each comment's text
//     from the public API (GET /api/comments/{id_code}) and checks its author.
// publishedWork: her articles (GET /api/articles?username=…), skipped when
//   published/edited dates are unchanged since the last run.
// Rate rules: DEVTO_RATE (≥1.1 s between requests, Retry-After on 429), with
// a larger per-run budget for sources, and the caller's deadline.

import { htmlToText } from "../../server/text.ts";
import type { AccountRow, OwnWriting, SourceBatch, SourceContext, SourceDocument } from "../../core/types.ts";
import { DEVTO_RATE, DevtoArticle, DevtoCommentNode, DevtoPublic } from "./api.ts";
import { flattenTree, ParsedComment } from "./parse.ts";

export const DEVTO_SOURCE_BUDGET = 60;
const MAX_REFS = 200;

/** Pure. Her comments in a flattened tree → candidates, with what each answered. */
export function ownWritingFromComments(comments: ParsedComment[], handle: string): OwnWriting[] {
  const own = handle.toLowerCase();
  return comments.filter((c) => c.author.username.toLowerCase() === own).map((c) => ({
    platform: "devto", external_id: c.id_code, url: c.url, text: c.text, posted_at: c.created_at,
    context: c.parent
      ? `Reply to @${c.parent.author_username ?? "someone"} on "${c.article.title}": ${c.parent.text.slice(0, 500)}`
      : `Comment on "${c.article.title}"${c.article.author_username && c.article.author_username.toLowerCase() !== own ? ` by @${c.article.author_username}` : ""}`,
  }));
}

export interface DeviceCommentRef { id_code: string; url?: string; article_title?: string; posted_at?: string }

/** Pure. The phone's refs, validated (id_code shape), deduped, capped. */
export function parseDeviceRefs(raw: unknown[] | undefined): DeviceCommentRef[] {
  const out = new Map<string, DeviceCommentRef>();
  for (const r of (raw ?? []).slice(0, MAX_REFS)) {
    const o = (r ?? {}) as Record<string, unknown>;
    const id = String(o.id_code ?? "").trim();
    if (!/^[a-z0-9]{1,16}$/i.test(id) || out.has(id)) continue;
    out.set(id, {
      id_code: id,
      url: typeof o.url === "string" ? o.url.slice(0, 300) : undefined,
      article_title: typeof o.article_title === "string" ? o.article_title.slice(0, 300) : undefined,
      posted_at: typeof o.posted_at === "string" ? o.posted_at : undefined,
    });
  }
  return [...out.values()];
}

export async function devtoOwnWriting(acct: AccountRow, ctx: SourceContext, api = new DevtoPublic(DEVTO_SOURCE_BUDGET, DEVTO_RATE.minIntervalMs)): Promise<SourceBatch> {
  const counts = { ...((ctx.state.counts ?? {}) as Record<string, number>) };
  const writing: OwnWriting[] = [];
  const room = () => Date.now() < ctx.deadline && api.requests < DEVTO_SOURCE_BUDGET - 2;
  let articles = 0, fetched = 0, foreign = 0;
  let stopped: string | null = null;
  try {
    // 1. Trees of her own articles and of the ones she commented on.
    const mine = await api.get<DevtoArticle[]>(`/articles?username=${encodeURIComponent(acct.handle)}&per_page=30`) ?? [];
    const queue: { id: number; count: number | null; art?: DevtoArticle }[] = mine.filter((a) => a.comments_count > 0)
      .map((a) => ({ id: a.id, count: a.comments_count, art: a }));
    for (const id of ((acct.settings?.watch_articles ?? []) as (number | string)[])) {
      if (!queue.some((q) => q.id === Number(id))) queue.push({ id: Number(id), count: null });
    }
    for (const q of queue) {
      if (!room()) { stopped = "budget"; break; }
      if (q.count !== null && counts[String(q.id)] === q.count) continue;
      const art = q.art ?? await api.get<DevtoArticle>(`/articles/${q.id}`);
      if (!art) continue;
      if (counts[String(q.id)] === art.comments_count || !room()) continue;
      const tree = await api.get<DevtoCommentNode[]>(`/comments?a_id=${q.id}&per_page=1000`) ?? [];
      writing.push(...ownWritingFromComments(flattenTree(art, acct.handle, tree), acct.handle));
      counts[String(q.id)] = art.comments_count;
      articles++;
    }
    // 2. Comments the phone listed that the trees didn't cover.
    const refs = parseDeviceRefs(ctx.deviceRefs).filter((r) => !writing.some((w) => w.external_id === r.id_code));
    const known = await ctx.knownWriting("devto", refs.map((r) => r.id_code));
    for (const r of refs.filter((r) => !known.has(r.id_code))) {
      if (!room()) { stopped = "budget"; break; }
      const c = await api.get<DevtoCommentNode>(`/comments/${r.id_code}`);
      fetched++;
      if (!c?.user?.username || c.user.username.toLowerCase() !== acct.handle.toLowerCase()) { foreign++; continue; }
      writing.push({
        platform: "devto", external_id: c.id_code, url: r.url ?? `https://dev.to/${c.user.username}/comment/${c.id_code}`,
        text: htmlToText(c.body_html ?? ""), posted_at: c.created_at ?? r.posted_at ?? null,
        context: r.article_title ? `Comment on "${r.article_title}"` : null,
      });
    }
  } catch (e) {
    return { writing, state: { counts }, status: /429|rate/i.test((e as Error).message) ? "rate_limited" : "error", message: (e as Error).message.slice(0, 200), stats: { articles, fetched } };
  }
  return { writing, state: { counts }, status: "ok", message: stopped ? "Stopped early (time or request budget); the rest next run." : null, stats: { articles, fetched, foreign } };
}

export async function devtoPublishedWork(acct: AccountRow, ctx: SourceContext, api = new DevtoPublic(DEVTO_SOURCE_BUDGET, DEVTO_RATE.minIntervalMs)): Promise<SourceBatch> {
  const seen = { ...((ctx.state.dates ?? {}) as Record<string, string>) };
  const documents: SourceDocument[] = [];
  let unchanged = 0;
  try {
    const list = await api.get<(DevtoArticle & { edited_at?: string | null; language?: string })[]>(
      `/articles?username=${encodeURIComponent(acct.handle)}&per_page=30`) ?? [];
    for (const a of list.slice(0, 30)) {
      const date = a.edited_at && a.edited_at > a.published_at ? a.edited_at : a.published_at;
      if (seen[String(a.id)] === date) { unchanged++; continue; }
      if (Date.now() > ctx.deadline) break;
      const full = await api.get<DevtoArticle & { edited_at?: string | null }>(`/articles/${a.id}`);
      if (!full?.body_markdown) continue;
      documents.push({ kind: "article", title: full.title, url: full.url, published_at: date, markdown: full.body_markdown, lang: a.language ?? "en", label: "quotable" });
      seen[String(a.id)] = date;
    }
  } catch (e) {
    return { documents, state: { dates: seen }, status: "error", message: (e as Error).message.slice(0, 200) };
  }
  return { documents, state: { dates: seen }, status: documents.length || unchanged ? "ok" : "empty", stats: { articles: documents.length, unchanged } };
}

