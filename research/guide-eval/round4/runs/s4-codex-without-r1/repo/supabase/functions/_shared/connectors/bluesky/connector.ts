// Bluesky connector (OFF by default: env CONNECTORS must include "bluesky").
// Auth: handle + app password (Vault), with a stored session because
// createSession is limited (30 per 5 min / 300 per day). Sync: replies,
// mentions and quotes since the cursor, each with its thread. On 429 the
// account backs off until ratelimit-reset. Replies are posted by the server
// (post-bluesky), max 300 graphemes.

import { isEnabled } from "../../core/flags.ts";
import type { AccountRow, Connector, ItemRow, NormalizedItem, SyncBatch, SyncContext } from "../../core/types.ts";
import { HttpError } from "../../server/http.ts";
import { BskyClient, BskyError, buildFacets, postUrl, resolveHandleDid } from "./client.ts";

export const BLUESKY = "bluesky";
export const BLUESKY_MAX = 300;
const REASONS = ["reply", "mention", "quote"];
const FIRST_POLL_DAYS = 14;

// deno-lint-ignore no-explicit-any
type Any = any;

/** Pure: a getPostThread response → {root, chain (parents below the root, oldest first), answered}. Exported for tests. */
export function threadContext(thread: Any, ownDid: string) {
  const parents: Any[] = [];
  let p = thread?.parent;
  while (p && p.post) { parents.unshift(p.post); p = p.parent; }
  const root = parents[0] ?? null;
  const chain = parents.slice(1).map((x) => ({
    author: x.author?.handle ?? "someone", text: x.record?.text ?? "", posted_at: x.record?.createdAt ?? x.indexedAt, is_owner: x.author?.did === ownDid,
  }));
  const answered = (thread?.replies ?? []).some((r: Any) => r?.post?.author?.did === ownDid);
  return { root, chain, answered };
}

/** Pure: one notification (+ its thread context) → a core item. Exported for tests. */
export function notificationToItem(n: Any, ctx: ReturnType<typeof threadContext>, ownDid: string): NormalizedItem {
  const rec = n.record ?? {};
  return {
    platform: BLUESKY, external_id: n.uri,
    kind: n.reason === "reply" ? "reply" : n.reason === "quote" ? "quote" : "mention",
    author: {
      handle: n.author.handle, external_id: n.author.did, display_name: n.author.displayName || null, avatar_url: n.author.avatar ?? null,
      profile_url: `https://bsky.app/profile/${n.author.handle}`,
    },
    text: rec.text ?? "", url: postUrl(n.author.handle, n.uri), posted_at: rec.createdAt ?? n.indexedAt,
    thread: ctx.chain,
    my_post: ctx.root ? {
      title: null, url: postUrl(ctx.root.author?.handle ?? ctx.root.author?.did, ctx.root.uri), text: ctx.root.record?.text ?? "",
      author: ctx.root.author?.handle, is_owner: ctx.root.author?.did === ownDid,
    } : null,
    reply_target: { root: rec.reply?.root ?? { uri: n.uri, cid: n.cid }, parent: { uri: n.uri, cid: n.cid } },
    answered: ctx.answered,
  };
}

async function sync(acct: AccountRow, ctx: SyncContext): Promise<SyncBatch> {
  const backoff = acct.settings?.backoff_until as string | undefined;
  if (backoff && backoff > new Date().toISOString()) return { items: [], own: [], skipped: `backoff until ${backoff}` };

  const client = await BskyClient.forAccount(acct.id);
  const since = acct.cursor ?? new Date(Date.now() - FIRST_POLL_DAYS * 86400_000).toISOString();
  const notifs: Any[] = [];
  let cursor: string | undefined;
  try {
    for (let page = 0; page < 3; page++) {
      const r = await client.call("GET", "app.bsky.notification.listNotifications", { params: { limit: 50, cursor, reasons: REASONS } });
      const batch = (r.notifications ?? []) as Any[];
      notifs.push(...batch.filter((n) => n.indexedAt > since));
      if (!r.cursor || batch.length < 50 || batch.some((n) => n.indexedAt <= since)) break;
      cursor = r.cursor;
    }
  } catch (e) {
    if (e instanceof BskyError && e.status === 429) {
      return {
        items: [], own: [], skipped: "rate limited",
        account: { settings: { backoff_until: e.resetAt ?? new Date(Date.now() + 300_000).toISOString() } },
      };
    }
    throw e;
  }

  const known = await ctx.known(acct.project_id, notifs.map((n) => n.uri));
  const items: NormalizedItem[] = [];
  let newest = acct.cursor ?? since;
  for (const n of notifs.sort((a, b) => a.indexedAt.localeCompare(b.indexedAt))) {
    if (n.indexedAt > newest) newest = n.indexedAt;
    if (!REASONS.includes(n.reason) || n.author?.did === client.did || known.has(n.uri)) continue;
    let tctx: ReturnType<typeof threadContext> = { root: null, chain: [], answered: false };
    try {
      const t = await client.call("GET", "app.bsky.feed.getPostThread", { params: { uri: n.uri, depth: 1, parentHeight: 8 } });
      tctx = threadContext(t.thread, client.did);
    } catch (e) {
      console.error("getPostThread:", (e as Error).message.slice(0, 120));
    }
    items.push(notificationToItem(n, tctx, client.did));
  }
  return { items, own: [], account: { cursor: newest, external_id: client.did, drop_settings: ["backoff_until"] } };
}

async function postReply(acct: AccountRow, item: ItemRow, text: string) {
  const parent = item.parent_ref as { uri?: string; cid?: string } | null;
  const rootRef = item.root_ref as { uri?: string; cid?: string } | null;
  if (!parent?.uri || !parent?.cid) throw new HttpError(422, "bad_request", "This item has no Bluesky reference to reply to.");
  const client = await BskyClient.forAccount(acct.id);
  const facets = await buildFacets(text, resolveHandleDid);
  const root = rootRef?.uri && rootRef?.cid ? rootRef : parent;
  const record = {
    $type: "app.bsky.feed.post", text, createdAt: new Date().toISOString(),
    reply: { root: { uri: root.uri, cid: root.cid }, parent: { uri: parent.uri, cid: parent.cid } },
    ...(facets.length ? { facets } : {}),
  };
  let posted: { uri: string; cid: string };
  try {
    posted = await client.call("POST", "com.atproto.repo.createRecord", { body: { repo: client.did, collection: "app.bsky.feed.post", record } });
  } catch (e) {
    throw new HttpError(502, "upstream_error", `Bluesky didn't take the post: ${(e as Error).message.slice(0, 160)}`);
  }
  return { url: postUrl(client.handle, posted.uri), external_id: posted.uri };
}

export const blueskyConnector: Connector = {
  id: BLUESKY,
  label: "Bluesky",
  auth: "app_password",
  accountAuth: "app_password",
  needsSecret: true,
  enabled: () => isEnabled(BLUESKY),
  schedule: { job: "hb-poll-bluesky", cron: "*/5 * * * *" },
  rateLimit: { minIntervalMs: 0, maxRequestsPerRun: 200, on429: "backoff_account" },
  reply: { mode: "server", maxGraphemes: BLUESKY_MAX },
  sync,
  postReply,
};
