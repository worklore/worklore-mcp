// Mapping from the v1 schema to a DraftRequest, and from a DraftResult to a
// drafts row. Written against a minimal query interface (satisfied by
// supabase-js) so it has no import of its own. Used by the draft and triage
// Edge Functions (supabase/functions/_shared/core/draft_run.ts).

import type { DraftRequest, DraftResult, MemorySnippet, Variant, VoiceSample } from "./types.ts";

// deno-lint-ignore no-explicit-any
type Row = Record<string, any>;
// deno-lint-ignore no-explicit-any
export type Db = { from(table: string): any };

const VOICE_POOL_LIMIT = 200;
const MEMORY_POOL_LIMIT = 300;

export async function loadDraftRequest(db: Db, itemId: string, founderId: string, opts: {
  variant?: Variant; note?: string | null;
  /** Evals only: use voice samples written strictly before this time. */
  voiceBefore?: string | null;
} = {}): Promise<{ req: DraftRequest; nextVersion: number }> {
  const one = async (q: Promise<{ data: Row | null; error: unknown }>) => {
    const { data, error } = await q;
    if (error) throw error;
    return data!;
  };
  const many = async (q: Promise<{ data: Row[] | null; error: unknown }>) => {
    const { data, error } = await q;
    if (error) throw error;
    return data ?? [];
  };

  const item = await one(db.from("items").select("*").eq("id", itemId).single());
  const [project, founder, person, identity] = await Promise.all([
    one(db.from("projects").select("*").eq("id", item.project_id).single()),
    one(db.from("founders").select("display_name, voice_notes").eq("id", founderId).single()),
    one(db.from("people").select("*").eq("id", item.person_id).single()),
    one(db.from("identities").select("handle").eq("person_id", item.person_id).eq("platform", item.platform).limit(1).single()),
  ]);
  // Discovered posts have no account; use the project's account on that platform for her handle.
  const account = item.account_id
    ? await one(db.from("accounts").select("handle").eq("id", item.account_id).single())
    : (await many(db.from("accounts").select("handle").eq("project_id", item.project_id).eq("platform", item.platform).limit(1)))[0] ?? { handle: founder.display_name ?? "" };
  const themeIds = (await many(db.from("item_themes").select("theme_id").eq("item_id", itemId))).map((r) => r.theme_id);

  // Voice pool: the drafting founder's ACTIVE voice samples (core/sources:
  // her own comments, replies she posted through Hearback, her GitHub folder;
  // judged by Jev, capped and diversified). In production every accepted
  // sample is fair to use, whenever she wrote it; the engine picks the most
  // similar ones (context.ts › rankVoice). Evals pass `voiceBefore` (the
  // leakage rule: nothing written after the item).
  let vq = db.from("voice_samples").select("id, text, context, posted_at, platform")
    .eq("founder_id", founderId).eq("status", "accepted").eq("active", true);
  if (opts.voiceBefore) vq = vq.lt("posted_at", opts.voiceBefore);
  const samples = await many(vq.order("posted_at", { ascending: false }).limit(VOICE_POOL_LIMIT));
  const voice_pool: VoiceSample[] = voicePool(samples, item.text ?? null);

  const mem = await many(db.from("project_memory").select("id, kind, text, source_url, theme_id")
    .eq("project_id", item.project_id).eq("active", true).neq("kind", "voice_sample").limit(MEMORY_POOL_LIMIT));
  const memory_pool: MemorySnippet[] = mem
    .filter((m) => !m.theme_id || themeIds.includes(m.theme_id))
    .map((m) => ({ id: m.id, kind: m.kind, text: m.text, source_url: m.source_url, theme: m.theme_id }));

  const touches = await many(db.from("touches").select("direction, text, occurred_at, url")
    .eq("person_id", item.person_id).lt("occurred_at", item.posted_at).not("text", "is", null)
    .order("occurred_at", { ascending: false }).limit(8));

  const prev = await many(db.from("drafts").select("version, text").eq("item_id", itemId).order("version", { ascending: false }).limit(1));
  const ownHandle = account.handle as string;

  const req: DraftRequest = {
    project: {
      name: project.name, one_liner: project.one_liner,
      audience: Array.isArray(project.audience) ? project.audience.join("; ") : project.audience,
      aims: project.aims, views: project.views,
      red_lines: project.red_lines, tone: project.tone, links: project.links ?? [],
      founder_name: founder.display_name, founder_handle: ownHandle, voice_notes: founder.voice_notes,
    },
    context: {
      platform: item.platform,
      kind: item.kind,
      post: item.my_post ? {
        title: item.my_post.title, url: item.my_post.url, text: item.my_post.text ?? "",
        author: item.my_post.author ?? ownHandle, is_owner: item.my_post.is_owner ?? true,
      } : null,
      chain: (item.thread ?? []).map((m: Row) => ({ author: m.author, text: m.text, posted_at: m.posted_at, is_owner: m.is_owner ?? m.author === ownHandle })),
      item: { author: identity.handle, text: item.text, posted_at: item.posted_at },
    },
    person: {
      handle: identity.handle, display_name: person.display_name, summary: person.summary, builds: person.builds,
      cares_about: person.cares_about, stage: person.stage, notes: person.notes,
      touches: touches.map((t) => ({ direction: t.direction, text: t.text, occurred_at: t.occurred_at, url: t.url })),
    },
    voice_pool, memory_pool,
    variant: opts.variant ?? "first",
    // The draft being revised: the newest version, or the one she named.
    previous_draft: prev[0]?.text ?? null,
    note: opts.note ?? null,
  };
  return { req, nextVersion: (prev[0]?.version ?? 0) + 1 };
}

/** Pure. voice_samples rows → the engine's pool; her reply TO this very item (its context quotes the item) is left out. */
export function voicePool(rows: Row[], itemText: string | null): VoiceSample[] {
  const norm = (t: string) => t.replace(/\s+/g, " ").trim().slice(0, 120);
  const key = itemText ? norm(itemText) : "";
  return rows.filter((s) => !key || key.length < 20 || !norm(String(s.context ?? "")).length || !String(s.context ?? "").replace(/\s+/g, " ").includes(key)).map((s) => ({
    id: `voice:${s.id}`, text: s.text, posted_at: s.posted_at ?? undefined,
    in_reply_to: s.context ? String(s.context).slice(0, 300) : undefined,
  }));
}

/** The drafts row for a result. outcome/final_text/posted_* are filled when she posts or skips. */
export function draftRow(itemId: string, version: number, r: DraftResult) {
  return {
    item_id: itemId, version, instruction: r.instruction, text: r.text,
    provider: r.provider, model: r.model, latency_ms: r.latency_ms,
    // tokens_in / tokens_out are generated from this breakdown.
    tokens: r.usage.detail ?? { input: r.usage.tokens_in, output: r.usage.tokens_out },
  };
}
