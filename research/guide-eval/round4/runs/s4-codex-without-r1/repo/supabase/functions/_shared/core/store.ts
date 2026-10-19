// Core storage: people (one per person, many identities), items (deduped by
// platform id), touches (the person's timeline). Platform-free: the platform
// is just the connector id. All writes use the service role after the
// caller's membership was checked.

import { admin } from "../server/ctx.ts";


export interface IdentityIn {
  handle: string;
  external_id?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  profile_url?: string | null;
  public_profile?: Record<string, unknown> | null;
}

/** Person for (project, platform, handle): found by identity, else created. Returns person_id. */
export async function upsertPerson(projectId: string, platform: string, who: IdentityIn): Promise<string> {
  const db = admin();
  const handle = who.handle.replace(/^@/, "");
  const find = async () => (await db.from("identities").select("id, person_id")
    .eq("project_id", projectId).eq("platform", platform).eq("handle", handle).maybeSingle()).data;
  const found = await find();
  if (found) {
    const patch: Record<string, unknown> = { profile_fetched_at: new Date().toISOString() };
    if (who.external_id) patch.external_id = who.external_id;
    if (who.profile_url) patch.profile_url = who.profile_url;
    if (who.public_profile) patch.public_profile = who.public_profile;
    await db.from("identities").update(patch).eq("id", found.id);
    const pp: Record<string, unknown> = {};
    if (who.display_name) pp.display_name = who.display_name;
    if (who.avatar_url) pp.avatar_url = who.avatar_url;
    if (Object.keys(pp).length) {
      // Only fill blanks: the founder may have renamed the person.
      const { data: p } = await db.from("people").select("display_name, avatar_url").eq("id", found.person_id).single();
      const fill: Record<string, unknown> = {};
      if (!p?.display_name && pp.display_name) fill.display_name = pp.display_name;
      if (pp.avatar_url && p?.avatar_url !== pp.avatar_url) fill.avatar_url = pp.avatar_url;
      if (Object.keys(fill).length) await db.from("people").update(fill).eq("id", found.person_id);
    }
    return found.person_id;
  }
  const { data: person, error } = await db.from("people").insert({
    project_id: projectId, display_name: who.display_name || handle, avatar_url: who.avatar_url ?? null,
  }).select("id").single();
  if (error) throw error;
  const { error: e2 } = await db.from("identities").insert({
    project_id: projectId, person_id: person.id, platform, handle, external_id: who.external_id ?? null,
    profile_url: who.profile_url ?? null, public_profile: who.public_profile ?? null, profile_fetched_at: new Date().toISOString(),
  });
  if (e2) {
    // Lost a race with another collector: use the winner's person.
    await db.from("people").delete().eq("id", person.id);
    const again = await find();
    if (again) return again.person_id;
    throw e2;
  }
  return person.id;
}

export interface ItemIn {
  project_id: string;
  account_id: string | null;
  person_id: string;
  platform: string;
  kind: "reply" | "mention" | "quote" | "comment" | "post";
  external_id: string;
  url: string | null;
  text: string;
  posted_at: string;
  root_ref?: unknown;
  parent_ref?: unknown;
  my_post?: unknown;
  thread?: unknown;
  status?: "new" | "draft_ready" | "answered" | "skipped";
  origin?: "inbox" | "discover";
  discovery?: unknown;
  triaged_at?: string | null;
}

/** Inserts unless (project, platform, external_id) exists. Returns the id and whether it is new. */
export async function insertItem(row: ItemIn): Promise<{ id: string; inserted: boolean }> {
  const db = admin();
  const { data, error } = await db.from("items").upsert(row, { onConflict: "project_id,platform,external_id", ignoreDuplicates: true })
    .select("id");
  if (error) throw error;
  if (data && data.length) {
    if ((row.origin ?? "inbox") === "inbox") {
      await addTouch({
        project_id: row.project_id, person_id: row.person_id, direction: "in", platform: row.platform, kind: row.kind,
        occurred_at: row.posted_at, url: row.url, text: row.text, item_id: data[0].id,
      });
    }
    return { id: data[0].id, inserted: true };
  }
  const { data: ex, error: e2 } = await db.from("items").select("id, thread, my_post").eq("project_id", row.project_id)
    .eq("platform", row.platform).eq("external_id", row.external_id).single();
  if (e2) throw e2;
  // Seen before, maybe with less context (the phone's cut parent comment, no
  // article body): keep whichever thread and post say more.
  const patch = richerContext(ex, row);
  if (patch) await db.from("items").update(patch).eq("id", ex.id);
  return { id: ex.id, inserted: false };
}

/** Pure: the thread / my_post update for a re-read item, or null when the stored ones say as much. Exported for tests. */
export function richerContext(stored: { thread?: unknown; my_post?: unknown }, fresh: { thread?: unknown; my_post?: unknown }): Record<string, unknown> | null {
  const size = (t: unknown) => Array.isArray(t) ? t.reduce((n, m) => n + String((m as { text?: unknown })?.text ?? "").length, 0) : 0;
  const body = (p: unknown) => String((p as { text?: unknown } | null)?.text ?? "").length;
  const patch: Record<string, unknown> = {};
  if (size(fresh.thread) > size(stored.thread)) patch.thread = fresh.thread;
  if (fresh.my_post && body(fresh.my_post) > body(stored.my_post)) patch.my_post = fresh.my_post;
  return Object.keys(patch).length ? patch : null;
}

export async function addTouch(t: {
  project_id: string; person_id: string; direction: "in" | "out"; platform: string; kind: string;
  occurred_at: string; url?: string | null; text?: string | null; item_id?: string | null; meta?: Record<string, unknown>;
}) {
  const db = admin();
  const ext = t.meta?.external_id as string | undefined;
  if (ext) {
    const { data } = await db.from("touches").select("id").eq("person_id", t.person_id).eq("meta->>external_id", ext).limit(1);
    if (data?.length) return;
  }
  // people.first_touch_at / last_touch_at follow from a trigger on touches.
  await db.from("touches").insert({ ...t, source: "collector", meta: t.meta ?? {} });
}
