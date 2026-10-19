// The generic pipeline: a connector's SyncBatch → people / identities / items
// / touches. Triage and drafting (triage_run.ts, draft_run.ts) run on the
// stored rows. Knows no platform.

import { admin } from "../server/ctx.ts";
import { addTouch, insertItem, upsertPerson } from "./store.ts";
import type { AccountRow, SyncBatch } from "./types.ts";

/** Where storeBatch writes. The default is the database; tests pass an in-memory one. */
export interface CoreStore {
  upsertPerson: typeof upsertPerson;
  insertItem: typeof insertItem;
  addTouch: typeof addTouch;
  markAnswered(projectId: string, platform: string, externalId: string): Promise<void>;
  /** She hid these on the network: skipped, with the reason, unless already decided. */
  markHidden(projectId: string, platform: string, externalIds: string[]): Promise<number>;
}

export const dbStore: CoreStore = {
  upsertPerson, insertItem, addTouch,
  async markAnswered(projectId, platform, externalId) {
    await admin().from("items").update({ status: "answered" }).eq("project_id", projectId).eq("platform", platform)
      .eq("external_id", externalId).in("status", ["new", "draft_ready"]);
  },
  async markHidden(projectId, platform, externalIds) {
    if (!externalIds.length) return 0;
    const db = admin();
    const { data } = await db.from("items").update({ status: "skipped", skip_reason: `hidden on ${platform}` })
      .eq("project_id", projectId).eq("platform", platform).in("external_id", externalIds).in("status", ["new", "draft_ready"]).select("id");
    const ids = (data ?? []).map((r) => r.id as string);
    if (ids.length) {
      await db.from("drafts").update({ outcome: "superseded", decided_at: new Date().toISOString() }).in("item_id", ids).is("outcome", null);
    }
    return ids.length;
  },
};

export interface StoreResult {
  inserted: string[];
  duplicates: number;
  own_replies: number;
  hidden: number;
}

export async function storeBatch(projectId: string, account: { id: string; handle: string }, batch: SyncBatch, store: CoreStore = dbStore): Promise<StoreResult> {
  const own = account.handle.toLowerCase();
  const inserted: string[] = [];
  let duplicates = 0, own_replies = 0;

  for (const m of batch.own) {
    own_replies++;
    const to = m.to_handle;
    if (!to || to.toLowerCase() === own) continue;
    const personId = await store.upsertPerson(projectId, m.platform, { handle: to });
    await store.addTouch({
      project_id: projectId, person_id: personId, direction: "out", platform: m.platform, kind: m.kind,
      occurred_at: m.posted_at, url: m.url, text: m.text, meta: { external_id: m.external_id },
    });
    // The item she answered (outside Hearback) is no longer waiting.
    if (m.answers_external_id) await store.markAnswered(projectId, m.platform, m.answers_external_id);
  }

  for (const it of batch.items) {
    if (it.author.handle.toLowerCase() === own) continue; // her own message is never an item
    const personId = await store.upsertPerson(projectId, it.platform, it.author);
    const r = await store.insertItem({
      project_id: projectId, account_id: account.id, person_id: personId, platform: it.platform, kind: it.kind,
      external_id: it.external_id, url: it.url, text: it.text, posted_at: it.posted_at,
      root_ref: it.reply_target.root, parent_ref: it.reply_target.parent,
      my_post: it.my_post, thread: it.thread,
      status: it.answered ? "answered" : "new",
    });
    if (r.inserted) inserted.push(r.id); else duplicates++;
  }
  const hidden = batch.hidden?.external_ids.length ? await store.markHidden(projectId, batch.hidden.platform, batch.hidden.external_ids) : 0;
  return { inserted, duplicates, own_replies, hidden };
}

/** Writes what the connector wants remembered on the account (cursor, merged settings). */
export async function applyAccountPatch(account: AccountRow, patch: SyncBatch["account"], polled = true) {
  const settings = { ...(account.settings ?? {}), ...(patch?.settings ?? {}) };
  for (const k of patch?.drop_settings ?? []) delete settings[k];
  const row: Record<string, unknown> = { settings };
  if (polled) Object.assign(row, { last_polled_at: new Date().toISOString(), last_error: null });
  if (patch?.cursor !== undefined) row.cursor = patch.cursor;
  if (patch?.external_id) row.external_id = patch.external_id;
  await admin().from("accounts").update(row).eq("id", account.id);
  account.settings = settings;
}

export async function knownExternalIds(projectId: string, platform: string, ids: string[]): Promise<Set<string>> {
  if (!ids.length) return new Set();
  const { data } = await admin().from("items").select("external_id").eq("project_id", projectId).eq("platform", platform).in("external_id", ids);
  return new Set((data ?? []).map((r: { external_id: string }) => r.external_id));
}
