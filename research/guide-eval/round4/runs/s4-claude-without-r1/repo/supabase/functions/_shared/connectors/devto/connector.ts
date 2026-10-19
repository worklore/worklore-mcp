// dev.to connector. The founder's session lives only on her phone: the phone
// reads her notifications and sends them to `ingest` (normalizeIngest); the
// server reads comments on her own articles, and replies inside threads she
// is in on other people's articles, through the public API (sync, every 15
// min). Replies are posted from the phone (reply mode "device").
// Rate rules: DEVTO_RATE (≥1.1 s between requests, ≤25 per run, Retry-After).

import { isEnabled } from "../../core/flags.ts";
import type { AccountRow, Connector, NormalizedItem, OwnMessage, SyncBatch, SyncContext } from "../../core/types.ts";
import { DEVTO_RATE, DevtoArticle, DevtoCommentNode, DevtoPublic } from "./api.ts";
import { flattenTree, hiddenIn, ParsedComment, parseIngestItem } from "./parse.ts";
import { devtoOwnWriting, devtoPublishedWork } from "./sources.ts";

export const DEVTO = "devto";
const MAX_WATCH = 30;
/** Articles whose comment tree one ingest call reads (2 requests each, ≥1.1 s apart). */
const MAX_ENRICH = 4;

/** Pure: parsed comments → the core's items and own messages. Exported for tests. */
export function toBatch(comments: ParsedComment[], ownHandle: string): SyncBatch {
  const own = ownHandle.toLowerCase();
  const items: NormalizedItem[] = [];
  const mine: OwnMessage[] = [];
  for (const c of comments) {
    if (c.author.username.toLowerCase() === own) {
      // Her reply → the person she answered; her top-level comment → the article's author.
      mine.push({
        platform: DEVTO, external_id: c.id_code, kind: "comment", url: c.url, text: c.text, posted_at: c.created_at,
        to_handle: c.parent?.author_username ?? c.article.author_username ?? null,
        answers_external_id: c.parent?.id_code ?? null,
      });
      continue;
    }
    const thread = (c.thread ?? (c.parent ? [{ author: c.parent.author_username ?? "someone", text: c.parent.text }] : []))
      .map((m) => ({ ...m, is_owner: m.author?.toLowerCase() === own }));
    const articleOwner = (c.article.author_username ?? "").toLowerCase();
    items.push({
      platform: DEVTO, external_id: c.id_code, kind: c.kind,
      author: { handle: c.author.username, display_name: c.author.name, avatar_url: c.author.avatar_url, profile_url: c.author.profile_url },
      text: c.text, url: c.url, posted_at: c.created_at, thread,
      my_post: c.article.title ? {
        title: c.article.title, url: c.article.url, text: c.article.text ?? "", author: c.article.author_username ?? null,
        is_owner: !articleOwner || articleOwner === own,
      } : null,
      reply_target: {
        root: { article_id: c.article.id, id_code: c.top_id_code ?? c.parent?.id_code ?? c.id_code },
        parent: { article_id: c.article.id, id_code: c.id_code },
      },
      answered: !!c.answered_by_owner,
    });
  }
  return { items, own: mine };
}

/** Article ids of other people's articles in these comments (threads she's in), merged into the watch list. Pure. */
export function watchList(current: unknown, comments: ParsedComment[], ownHandle: string): number[] {
  const own = ownHandle.toLowerCase();
  const others = comments.filter((p) => p.article.id && p.article.author_username && p.article.author_username.toLowerCase() !== own)
    .map((p) => Number(p.article.id)).filter((n) => Number.isFinite(n) && n > 0);
  return [...new Set([...others, ...((current ?? []) as number[])])].slice(0, MAX_WATCH);
}

async function sync(acct: AccountRow, ctx: SyncContext): Promise<SyncBatch> {
  const api = (ctx.run as DevtoPublic | undefined) ?? new DevtoPublic();
  const settings = acct.settings ?? {};
  const seen = (settings.devto_counts ?? {}) as Record<string, number>;
  const counts: Record<string, number> = { ...seen };
  const out: SyncBatch = { items: [], own: [], hidden: { platform: DEVTO, external_ids: [] } };
  const add = (b: SyncBatch) => { out.items.push(...b.items); out.own.push(...b.own); };
  let articles = 0;

  // Her own articles whose comment count changed.
  const list = await api.get<DevtoArticle[]>(`/articles?username=${encodeURIComponent(acct.handle)}&per_page=30`) ?? [];
  for (const a of list.filter((a) => a.comments_count > 0 && seen[String(a.id)] !== a.comments_count)) {
    const full = await api.get<DevtoArticle>(`/articles/${a.id}`);
    const tree = await api.get<DevtoCommentNode[]>(`/comments?a_id=${a.id}&per_page=1000`) ?? [];
    add(toBatch(flattenTree({ ...a, body_markdown: full?.body_markdown }, acct.handle, tree), acct.handle));
    // Comments she hid on dev.to are done in Hearback too.
    out.hidden!.external_ids.push(...hiddenIn(tree));
    counts[String(a.id)] = a.comments_count;
    articles++;
  }

  // Threads she's in on other people's articles: only her comments (touches)
  // and replies inside her sub-threads become items.
  const own = acct.handle.toLowerCase();
  for (const id of ((settings.watch_articles ?? []) as (number | string)[]).slice(0, MAX_WATCH)) {
    if (api.requests > DEVTO_RATE.maxRequestsPerRun - 5) break;
    const full = await api.get<DevtoArticle>(`/articles/${id}`);
    if (!full || !full.comments_count || counts[String(id)] === full.comments_count) continue;
    const tree = await api.get<DevtoCommentNode[]>(`/comments?a_id=${id}&per_page=1000`) ?? [];
    const parsed = flattenTree(full, acct.handle, tree).filter((c) => c.author.username.toLowerCase() === own || c.under_owner);
    add(toBatch(parsed, acct.handle));
    counts[String(id)] = full.comments_count;
    articles++;
  }
  out.account = { settings: { devto_counts: counts } };
  out.stats = { articles };
  return out;
}

/**
 * Pure: the phone's comments with what the public comment tree knows. The
 * phone reads notifications, where dev.to cuts the parent comment to ~80
 * characters ("Re: I understand the wish… ve...") and gives no ancestors or
 * article body; the tree has them all. A comment not in the tree stays as
 * the phone sent it. Exported for tests.
 */
export function mergeTree(phone: ParsedComment, tree: ParsedComment | undefined, article: DevtoArticle | null): ParsedComment {
  if (!tree) return phone;
  return {
    ...phone,
    text: tree.text.length > phone.text.length ? tree.text : phone.text,
    parent: tree.parent ?? phone.parent,
    thread: tree.thread,
    top_id_code: tree.top_id_code,
    answered_by_owner: tree.answered_by_owner,
    under_owner: tree.under_owner,
    article: article
      ? { ...phone.article, author_username: tree.article.author_username ?? phone.article.author_username, text: tree.article.text ?? phone.article.text }
      : phone.article,
  };
}

/** Reads the comment tree (and the article) of up to MAX_ENRICH articles in this ingest; any failure keeps the phone's version. */
async function enrich(parsed: ParsedComment[], owner: string, api: DevtoPublic): Promise<ParsedComment[]> {
  const ids = [...new Set(parsed.map((p) => String(p.article.id)).filter((id) => /^\d+$/.test(id)))].slice(0, MAX_ENRICH);
  const byArticle = new Map<string, { article: DevtoArticle | null; tree: Map<string, ParsedComment> }>();
  for (const id of ids) {
    try {
      const article = await api.get<DevtoArticle>(`/articles/${id}`);
      const nodes = await api.get<DevtoCommentNode[]>(`/comments?a_id=${id}&per_page=1000`) ?? [];
      const p = parsed.find((x) => String(x.article.id) === id)!;
      const flat = flattenTree(article ?? { id: Number(id), title: p.article.title, url: p.article.url, user: p.article.author_username ? { username: p.article.author_username } : undefined }, owner, nodes);
      byArticle.set(id, { article, tree: new Map(flat.map((c) => [c.id_code, c])) });
    } catch (e) {
      console.error(`dev.to tree for ${id}:`, (e as Error).message.slice(0, 120));
    }
  }
  return parsed.map((p) => {
    const a = byArticle.get(String(p.article.id));
    return a ? mergeTree(p, a.tree.get(p.id_code), a.article) : p;
  });
}

async function normalizeIngest(raw: unknown[], acct: AccountRow, ctx?: { run?: unknown }) {
  let parsed: ParsedComment[] = [];
  const rejected: { index: number; reason: string }[] = [];
  raw.forEach((r, i) => {
    try { parsed.push(parseIngestItem(r as Record<string, unknown>)); } catch (e) { rejected.push({ index: i, reason: (e as Error).message }); }
  });
  const api = (ctx?.run as DevtoPublic | undefined) ?? new DevtoPublic(MAX_ENRICH * 2, DEVTO_RATE.minIntervalMs);
  parsed = await enrich(parsed, acct.handle, api);
  const batch = toBatch(parsed, acct.handle);
  // Threads on other people's articles: watch them so the public poller keeps
  // reading replies while the phone is asleep.
  const settings = acct.settings ?? {};
  const watch = watchList(settings.watch_articles, parsed, acct.handle);
  if (watch.length) batch.account = { settings: { watch_articles: watch } };
  return { batch, rejected };
}

export const devtoConnector: Connector = {
  id: DEVTO,
  label: "dev.to",
  auth: "device_session",
  accountAuth: "none",
  needsSecret: false,
  enabled: () => isEnabled(DEVTO),
  schedule: { job: "hb-poll-devto-public", cron: "*/15 * * * *" },
  rateLimit: { minIntervalMs: DEVTO_RATE.minIntervalMs, maxRequestsPerRun: DEVTO_RATE.maxRequestsPerRun, on429: DEVTO_RATE.on429 },
  reply: { mode: "device", maxGraphemes: null },
  beginRun: () => new DevtoPublic(DEVTO_RATE.maxRequestsPerRun, DEVTO_RATE.minIntervalMs),
  sync,
  normalizeIngest,
  ownWriting: (acct, ctx) => devtoOwnWriting(acct, ctx),
  publishedWork: (acct, ctx) => devtoPublishedWork(acct, ctx),
};
