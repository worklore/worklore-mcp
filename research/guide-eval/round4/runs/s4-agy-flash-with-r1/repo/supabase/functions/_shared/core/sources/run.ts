// The sources pipeline for one project (docs/ARCHITECTURE.md › Sources: voice
// and knowledge). Platform-free: it asks the registry's connectors for
//   ownWriting(account)      → voice-sample candidates of the account's founder
//   publishedWork(account)   → knowledge documents
//   projectSource(project)   → both (GitHub: the linked repo's folder)
// plus the product's site (site.ts) and the replies she posted through
// Hearback, then judges candidates (voice.ts) and refreshes each founder's
// active set. Every run is idempotent: candidates dedupe by (founder,
// platform, external_id) and by text hash; documents by URL + content hash.
// Runs: on account connect (the app), daily (cron), after each posted draft
// (trigger → candidate; the judge cron decides within minutes), "Sync now".

import { admin } from "../../server/ctx.ts";
import { tagUsage } from "../../server/usage.ts";
import { embedPending, markSeed, storeDocs, StoreReport } from "../../server/knowledge.ts";
import { decider } from "../../server/models.ts";
import { connector, connectors } from "../registry.ts";
import type { AccountRow, Connector, OwnWriting, ProjectSourceRow, SourceBatch, SourceContext, SourceDocument } from "../types.ts";
import { readSite } from "./site.ts";
import { judgeCandidate, normalizeText, selectActive, textSha } from "./voice.ts";

export type Phase = "all" | "voice" | "knowledge" | "judge";

export interface SourceStatus { source: string; status: string; message?: string | null; stats?: Record<string, number> }

export interface ProjectSyncReport {
  project_id: string;
  voice: { found: number; new: number };
  judged: { judged: number; accepted: number; rejected: number; pending: number };
  active: Record<string, number>;
  knowledge: (StoreReport & { by_source: Record<string, number>; seed_marked: number }) | null;
  embedded: number;
  pending_chunks: number | null;
  sources: SourceStatus[];
}

interface ProjectRow extends ProjectSourceRow { created_by: string | null }

const MAX_TEXT = 5000;

async function loadStates(projectId: string): Promise<Map<string, Record<string, unknown>>> {
  const { data, error } = await admin().from("source_syncs").select("source, state").eq("project_id", projectId);
  if (error) throw error;
  return new Map((data ?? []).map((r) => [r.source as string, (r.state ?? {}) as Record<string, unknown>]));
}

async function saveState(projectId: string, source: string, b: SourceBatch, extra: Record<string, number> = {}) {
  const row = {
    project_id: projectId, source, status: b.status ?? "ok", message: b.message ?? null,
    stats: { ...(b.stats ?? {}), ...extra }, last_synced_at: new Date().toISOString(),
    ...(b.state ? { state: b.state } : {}),
  };
  const { error } = await admin().from("source_syncs").upsert(row, { onConflict: "project_id,source" });
  if (error) console.error(`source_syncs ${source}: ${error.message}`);
}

/** Which of these external ids a founder already has as voice samples. */
export async function knownWriting(founderId: string, platform: string, ids: string[]): Promise<Set<string>> {
  if (!ids.length) return new Set();
  const { data } = await admin().from("voice_samples").select("external_id").eq("founder_id", founderId).eq("platform", platform).in("external_id", ids);
  return new Set((data ?? []).map((r) => r.external_id as string));
}

/** Stores new candidates; skips ones the founder already has (same id or same text). Returns how many were new. */
export async function addCandidates(founderId: string, projectId: string | null, source: "own_writing" | "github" | "hearback", items: OwnWriting[]): Promise<number> {
  const rows = [];
  const seen = new Set<string>();
  for (const w of items) {
    const text = w.text.trim().slice(0, MAX_TEXT);
    if (!text) continue;
    const sha = await textSha(text);
    const key = `${w.platform}:${w.external_id}`;
    if (seen.has(sha) || seen.has(key)) continue;
    seen.add(sha); seen.add(key);
    rows.push({
      founder_id: founderId, project_id: projectId, platform: w.platform, source, external_id: w.external_id,
      source_url: w.url, text, context: w.context?.slice(0, 1000) ?? null, posted_at: w.posted_at, text_sha256: sha,
    });
  }
  if (!rows.length) return 0;
  const db = admin();
  const fresh = [];
  for (let i = 0; i < rows.length; i += 100) {
    const part = rows.slice(i, i + 100);
    const [{ data: byId }, { data: bySha }] = await Promise.all([
      db.from("voice_samples").select("platform, external_id").eq("founder_id", founderId).in("external_id", part.map((r) => r.external_id)),
      db.from("voice_samples").select("text_sha256").eq("founder_id", founderId).in("text_sha256", part.map((r) => r.text_sha256)),
    ]);
    const ids = new Set((byId ?? []).map((r) => `${r.platform}:${r.external_id}`));
    const shas = new Set((bySha ?? []).map((r) => r.text_sha256));
    fresh.push(...part.filter((r) => !ids.has(`${r.platform}:${r.external_id}`) && !shas.has(r.text_sha256)));
  }
  if (!fresh.length) return 0;
  const { error } = await db.from("voice_samples").upsert(fresh, { onConflict: "founder_id,platform,external_id", ignoreDuplicates: true });
  if (error) throw error;
  return fresh.length;
}

/** Replies she posted through Hearback that have no sample yet (the trigger covers new ones; this backfills). */
async function backfillPosted(projectId: string): Promise<number> {
  const { data, error } = await admin().from("drafts")
    .select("id, final_text, posted_at, posted_url, posted_by, decided_by, items!inner(project_id, platform, text)")
    .eq("items.project_id", projectId).in("outcome", ["posted_as_is", "posted_edited"]).not("final_text", "is", null).limit(500);
  if (error) throw error;
  let n = 0;
  const byFounder = new Map<string, OwnWriting[]>();
  for (const d of data ?? []) {
    const f = (d.posted_by ?? d.decided_by) as string | null;
    if (!f) continue;
    // deno-lint-ignore no-explicit-any
    const it = d.items as any;
    byFounder.set(f, [...(byFounder.get(f) ?? []), {
      platform: it.platform, external_id: `draft:${d.id}`, url: d.posted_url, text: d.final_text, posted_at: d.posted_at,
      context: String(it.text ?? "").slice(0, 600),
    }]);
  }
  for (const [f, items] of byFounder) n += await addCandidates(f, projectId, "hearback", items);
  return n;
}

/** Judges up to `limit` pending candidates (optionally only these founders') until the deadline; refreshes active sets. */
export async function judgePending(opts: { founderIds?: string[]; limit?: number; deadline: number }) {
  let q = admin().from("voice_samples").select("id, founder_id, platform, text, context").eq("status", "candidate")
    .order("created_at", { ascending: true }).limit(opts.limit ?? 40);
  if (opts.founderIds?.length) q = q.in("founder_id", opts.founderIds);
  const { data, error } = await q;
  if (error) throw error;
  const d = decider();
  let judged = 0, accepted = 0, rejected = 0;
  const touched = new Set<string>();
  for (const c of data ?? []) {
    if (Date.now() > opts.deadline) break;
    try {
      const v = await judgeCandidate(d, { text: c.text, context: c.context, platform: c.platform });
      await admin().from("voice_samples").update({
        status: v.status, reason: v.reason, quality: v.quality, scores: v.scores, decided_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      }).eq("id", c.id);
      judged++;
      if (v.status === "accepted") accepted++; else rejected++;
      touched.add(c.founder_id);
    } catch (e) {
      console.error(`judge ${c.id}: ${(e as Error).message.slice(0, 200)}`);
      break; // the decider is down; the next run retries
    }
  }
  const active: Record<string, number> = {};
  for (const f of touched) active[f] = await refreshActive(f);
  let pq = admin().from("voice_samples").select("id", { count: "exact", head: true }).eq("status", "candidate");
  if (opts.founderIds?.length) pq = pq.in("founder_id", opts.founderIds);
  const { count } = await pq;
  return { judged, accepted, rejected, pending: count ?? 0, active };
}

/** Recomputes a founder's active set (selectActive over her accepted samples). Returns its size. */
export async function refreshActive(founderId: string): Promise<number> {
  const db = admin();
  const { data, error } = await db.from("voice_samples").select("id, text, platform, source, quality, posted_at, active")
    .eq("founder_id", founderId).eq("status", "accepted");
  if (error) throw error;
  const chosen = new Set(selectActive(data ?? []));
  const on = (data ?? []).filter((s) => chosen.has(s.id) && !s.active).map((s) => s.id);
  const off = (data ?? []).filter((s) => !chosen.has(s.id) && s.active).map((s) => s.id);
  if (on.length) await db.from("voice_samples").update({ active: true }).in("id", on);
  if (off.length) await db.from("voice_samples").update({ active: false }).in("id", off);
  // Rejected or still-pending samples are never active.
  await db.from("voice_samples").update({ active: false }).eq("founder_id", founderId).neq("status", "accepted").eq("active", true);
  return chosen.size;
}

export async function syncProject(projectId: string, opts: {
  phase?: Phase; deadline: number;
  /** What the phone read with its own session: {platform, account_handle, refs}. */
  device?: { platform: string; account_handle: string; refs: unknown[] } | null;
}): Promise<ProjectSyncReport> {
  const phase = opts.phase ?? "all";
  tagUsage({ project_id: projectId, item_id: null });
  const db = admin();
  const { data: project, error } = await db.from("projects").select("id, url, github_repo, github_folder, created_by").eq("id", projectId).single();
  if (error) throw error;
  const p = project as ProjectRow;
  const { data: accts } = await db.from("accounts").select("id, project_id, platform, handle, external_id, cursor, settings, secret_id, connected_by")
    .eq("project_id", projectId).eq("active", true);
  const accounts = (accts ?? []) as (AccountRow & { connected_by: string | null })[];
  const states = await loadStates(projectId);
  const report: ProjectSyncReport = {
    project_id: projectId, voice: { found: 0, new: 0 }, judged: { judged: 0, accepted: 0, rejected: 0, pending: 0 },
    active: {}, knowledge: null, embedded: 0, pending_chunks: null, sources: [],
  };
  const founders = new Set<string>();
  const ctxFor = (source: string, founderId: string | null, deviceRefs?: unknown[]): SourceContext => ({
    state: states.get(source) ?? {}, deadline: opts.deadline, deviceRefs,
    knownWriting: (platform, ids) => founderId ? knownWriting(founderId, platform, ids) : Promise.resolve(new Set()),
  });
  const record = async (source: string, b: SourceBatch, extra: Record<string, number> = {}) => {
    await saveState(projectId, source, b, extra);
    report.sources.push({ source, status: b.status ?? "ok", message: b.message ?? null, stats: { ...(b.stats ?? {}), ...extra } });
  };
  const run = async (source: string, f: () => Promise<SourceBatch>): Promise<SourceBatch> => {
    try { return await f(); } catch (e) {
      console.error(`source ${source}: ${(e as Error).message.slice(0, 200)}`);
      return { status: "error", message: (e as Error).message.slice(0, 200) };
    }
  };

  // ---------------------------------------------------------------- voice
  if (phase === "all" || phase === "voice") {
    for (const a of accounts) {
      const conn = connector(a.platform);
      if (!conn?.ownWriting || !conn.enabled() || Date.now() > opts.deadline) continue;
      const founder = a.connected_by ?? p.created_by;
      if (!founder) continue;
      founders.add(founder);
      const source = `${a.platform}:writing:${a.handle.toLowerCase()}`;
      const dev = opts.device && opts.device.platform === a.platform && opts.device.account_handle.toLowerCase() === a.handle.toLowerCase()
        ? opts.device.refs : undefined;
      const b = await run(source, () => conn.ownWriting!(a, ctxFor(source, founder, dev)));
      const added = b.writing?.length ? await addCandidates(founder, projectId, "own_writing", b.writing) : 0;
      report.voice.found += b.writing?.length ?? 0;
      report.voice.new += added;
      await record(source, b, { found: b.writing?.length ?? 0, new: added });
    }
    report.voice.new += await backfillPosted(projectId);
  }

  // ---------------------------------------------------------------- knowledge (+ project sources' writing)
  if (phase === "all" || phase === "knowledge" || phase === "voice") {
    const docs: { doc: SourceDocument; source: string }[] = [];
    const wantDocs = phase !== "voice";
    if (wantDocs && p.url && Date.now() < opts.deadline) {
      const b = await run("landing", () => readSite(p.url!, states.get("landing") ?? {}, opts.deadline - 20_000));
      for (const d of b.documents ?? []) docs.push({ doc: d, source: "landing" });
      await record("landing", b);
    }
    if (wantDocs) {
      for (const a of accounts) {
        const conn = connector(a.platform);
        if (!conn?.publishedWork || !conn.enabled() || Date.now() > opts.deadline) continue;
        const source = `${a.platform}:articles:${a.handle.toLowerCase()}`;
        const b = await run(source, () => conn.publishedWork!(a, ctxFor(source, null)));
        for (const d of b.documents ?? []) docs.push({ doc: d, source: a.platform });
        await record(source, b);
      }
    }
    // Project-level sources (GitHub folder) bring documents AND writing; run them in the voice phase too.
    for (const conn of connectors().filter((c: Connector) => c.projectSource && c.enabled())) {
      if (Date.now() > opts.deadline) break;
      const key = conn.id === "github" ? `github:${(p.github_repo ?? "").toLowerCase()}` : conn.id;
      if (conn.id === "github" && !p.github_repo) continue;
      const founder = p.created_by;
      const b = await run(key, () => conn.projectSource!(p, ctxFor(key, founder)));
      for (const d of b.documents ?? []) docs.push({ doc: d, source: conn.id });
      let added = 0;
      if (founder && b.writing?.length) {
        founders.add(founder);
        added = await addCandidates(founder, projectId, "github", b.writing);
        report.voice.found += b.writing.length;
        report.voice.new += added;
      }
      await record(key, b, { documents: b.documents?.length ?? 0, writing: b.writing?.length ?? 0, new_writing: added });
    }
    if (docs.length || wantDocs) {
      const stored = await storeDocs(projectId, docs);
      const by_source: Record<string, number> = {};
      for (const d of docs) by_source[d.source] = (by_source[d.source] ?? 0) + 1;
      const seed_marked = wantDocs ? await markSeed(projectId) : 0;
      report.knowledge = { ...stored, by_source, seed_marked };
    }
  }

  // ---------------------------------------------------------------- judge + active set
  if (phase !== "knowledge") {
    if (p.created_by) founders.add(p.created_by);
    const j = await judgePending({ founderIds: [...founders], limit: 60, deadline: opts.deadline });
    report.judged = { judged: j.judged, accepted: j.accepted, rejected: j.rejected, pending: j.pending };
    for (const f of founders) report.active[f] = j.active[f] ?? await refreshActive(f);
  }

  // ---------------------------------------------------------------- embeddings
  if (phase === "all" || phase === "knowledge") {
    const e = await embedPending(projectId, opts.deadline + 25_000);
    report.embedded = e.embedded;
    report.pending_chunks = e.pending;
  }
  return report;
}
