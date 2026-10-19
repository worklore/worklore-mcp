// The core is platform-free: a third connector plugs in through the registry
// and its items go through the same pipeline, with no change to core code.
//   deno test -A supabase/functions/_shared/

import { assert, assertEquals } from "jsr:@std/assert@1";
import "../connectors/mod.ts";
import { toBatch, watchList } from "../connectors/devto/connector.ts";
import { notificationToItem } from "../connectors/bluesky/connector.ts";
import type { ParsedComment } from "../connectors/devto/parse.ts";
import { CoreStore, storeBatch } from "./pipeline.ts";
import { connector, connectors, registerConnector, replyLimit, unregisterConnector } from "./registry.ts";
import { enabledConnectorIds } from "./flags.ts";
import type { Connector, SyncBatch } from "./types.ts";

/** An in-memory CoreStore: what storeBatch would write. */
function memoryStore() {
  const people = new Map<string, string>();
  const items: Record<string, unknown>[] = [];
  const touches: Record<string, unknown>[] = [];
  const answered: string[] = [];
  const hidden: string[] = [];
  const store: CoreStore = {
    upsertPerson: (_p, platform, who) => {
      const k = `${platform}:${who.handle}`;
      if (!people.has(k)) people.set(k, `person-${people.size + 1}`);
      return Promise.resolve(people.get(k)!);
    },
    insertItem: (row) => {
      const dup = items.find((i) => i.platform === row.platform && i.external_id === row.external_id);
      if (dup) return Promise.resolve({ id: dup.id as string, inserted: false });
      const id = `item-${items.length + 1}`;
      items.push({ ...row, id });
      return Promise.resolve({ id, inserted: true });
    },
    addTouch: (t) => { touches.push(t); return Promise.resolve(); },
    markAnswered: (_p, platform, ext) => { answered.push(`${platform}:${ext}`); return Promise.resolve(); },
    markHidden: (_p, platform, exts) => { hidden.push(...exts.map((e) => `${platform}:${e}`)); return Promise.resolve(exts.length); },
  };
  return { store, people, items, touches, answered };
}

const fakeMastodon: Connector = {
  id: "mastodon", label: "Mastodon", auth: "oauth", accountAuth: "oauth", needsSecret: true,
  enabled: () => true, schedule: { job: "hb-poll-mastodon", cron: "*/10 * * * *" },
  rateLimit: { minIntervalMs: 1000, maxRequestsPerRun: 30, on429: "backoff_account" },
  reply: { mode: "server", maxGraphemes: 500 },
  sync: (account) => Promise.resolve<SyncBatch>({
    items: [{
      platform: "mastodon", external_id: "109", kind: "reply", author: { handle: "ana@hachyderm.io", display_name: "Ana" },
      text: "Does it read Mastodon too?", url: "https://hachyderm.io/@ana/109", posted_at: "2026-10-09T10:00:00Z",
      thread: [{ author: account.handle, text: "Shipped!", is_owner: true }],
      my_post: { url: "https://hachyderm.io/@me/1", text: "Shipped!", is_owner: true }, reply_target: { root: { id: "1" }, parent: { id: "109" } },
    }],
    own: [{ platform: "mastodon", external_id: "110", kind: "reply", to_handle: "bob@x.social", url: null, text: "thanks", posted_at: "2026-10-09T11:00:00Z", answers_external_id: "108" }],
    account: { cursor: "110" },
  }),
};

Deno.test("a fake third connector registers and flows through the core pipeline", async () => {
  registerConnector(fakeMastodon);
  try {
    assertEquals(connector("mastodon")?.label, "Mastodon");
    assert(connectors().some((c) => c.id === "devto"));
    assertEquals(replyLimit("mastodon"), 500); // the core's draft limit comes from the connector

    const acct = { id: "a1", project_id: "p1", platform: "mastodon", handle: "me@hachyderm.io" };
    const batch = await fakeMastodon.sync!(acct, { run: undefined, known: () => Promise.resolve(new Set()) });
    const m = memoryStore();
    const r = await storeBatch("p1", acct, batch, m.store);
    assertEquals(r.inserted, ["item-1"]);
    assertEquals(r.own_replies, 1);
    assertEquals(m.items[0].platform, "mastodon");
    assertEquals(m.items[0].status, "new");
    assertEquals(m.items[0].parent_ref, { id: "109" });
    assertEquals(m.touches.map((t) => t.direction), ["out"]);
    assertEquals(m.answered, ["mastodon:108"]);
    // Again: deduped by (platform, external_id).
    assertEquals((await storeBatch("p1", acct, batch, m.store)).duplicates, 1);
  } finally {
    unregisterConnector("mastodon");
  }
});

Deno.test("flags: dev.to on, Bluesky off by default", () => {
  assertEquals(enabledConnectorIds(""), ["devto"]);
  assertEquals(enabledConnectorIds("devto, Bluesky"), ["devto", "bluesky"]);
  assertEquals(connector("bluesky")?.reply.maxGraphemes, 300);
  assertEquals(replyLimit("devto"), null);
});

const comment = (o: Partial<ParsedComment>): ParsedComment => ({
  id_code: "c1", kind: "comment", text: "Nice", url: "https://dev.to/sam/comment/c1", created_at: "2026-10-09T10:00:00Z",
  author: { username: "sam" }, article: { id: 7, title: "T", url: "https://dev.to/yahhi/t", author_username: "yahhi" }, ...o,
});

Deno.test("dev.to: comments → items, her own comments → own messages", () => {
  const b = toBatch([
    comment({ answered_by_owner: true, thread: [] }),
    comment({ id_code: "c2", author: { username: "Yahhi" }, parent: { id_code: "c1", text: "Nice", author_username: "sam" } }),
  ], "yahhi");
  assertEquals(b.items.length, 1);
  assertEquals(b.items[0].answered, true);
  assertEquals(b.items[0].reply_target.parent, { article_id: 7, id_code: "c1" });
  assertEquals(b.own, [{
    platform: "devto", external_id: "c2", kind: "comment", url: "https://dev.to/sam/comment/c1", text: "Nice",
    posted_at: "2026-10-09T10:00:00Z", to_handle: "sam", answers_external_id: "c1",
  }]);
  assertEquals(watchList([5], [comment({ article: { id: 9, title: "x", url: "u", author_username: "other" } })], "yahhi"), [9, 5]);
});

Deno.test("Bluesky: a notification → a core item", () => {
  const it = notificationToItem({
    uri: "at://did:x/app.bsky.feed.post/3k", cid: "c", reason: "reply", indexedAt: "2026-10-09T10:00:00Z",
    author: { handle: "ana.bsky.social", did: "did:x", displayName: "Ana" }, record: { text: "hi", reply: { root: { uri: "at://r", cid: "rc" } } },
  }, { root: null, chain: [], answered: false }, "did:me");
  assertEquals([it.platform, it.kind, it.url], ["bluesky", "reply", "https://bsky.app/profile/ana.bsky.social/post/3k"]);
  assertEquals(it.reply_target.root, { uri: "at://r", cid: "rc" });
});
