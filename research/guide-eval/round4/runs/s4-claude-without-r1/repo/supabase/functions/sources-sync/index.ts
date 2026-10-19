// POST /functions/v1/sources-sync
//   {project_id?, phase?: 'all'|'voice'|'knowledge'|'judge', own_writing?: {platform, account_handle, refs: [...]}}
// The sources pipeline (docs/ARCHITECTURE.md › Sources: voice and knowledge):
// the founder's own writing → voice-sample candidates → Jev → active set; her
// published work, the GitHub folder and the site → knowledge documents.
//   - a founder (app: on connect, "Sync now", the phone's dev.to comment list): her project;
//   - the service role with project_id: that project (scripts);
//   - the service role without project_id: phase 'all' = every project, least
//     recently synced first, while time allows (daily cron); phase 'judge' =
//     pending candidates of everyone + new chunks' embeddings (cron, every 10 min).
// docs/API.md › sources-sync

import "../_shared/connectors/mod.ts";
import { judgePending, Phase, syncProject } from "../_shared/core/sources/run.ts";
import { admin, caller, requireMember } from "../_shared/server/ctx.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";
import { embedPending } from "../_shared/server/knowledge.ts";

const BUDGET_MS = 125_000;

serve(async (req, body) => {
  const t0 = Date.now();
  const deadline = t0 + BUDGET_MS;
  const c = await caller(req);
  const projectId = uuid(body.project_id, "project_id", c.kind === "user");
  if (projectId) await requireMember(c, projectId);
  const phase = (str(body.phase, "phase", { max: 20 }) ?? "all") as Phase;
  if (!["all", "voice", "knowledge", "judge"].includes(phase)) throw bad("phase must be all, voice, knowledge or judge");

  let device: { platform: string; account_handle: string; refs: unknown[] } | null = null;
  if (body.own_writing !== undefined) {
    const o = body.own_writing as Record<string, unknown>;
    if (!o || typeof o !== "object" || !Array.isArray(o.refs)) throw bad("own_writing must be {platform, account_handle, refs: []}");
    if (o.refs.length > 200) throw bad("at most 200 refs");
    device = {
      platform: str(o.platform, "own_writing.platform", { required: true, max: 40 })!,
      account_handle: str(o.account_handle, "own_writing.account_handle", { required: true, max: 60 })!.replace(/^@/, ""),
      refs: o.refs,
    };
    if (!projectId) throw bad("own_writing needs project_id");
  }

  if (projectId) {
    if (phase === "judge") {
      const { data: p } = await admin().from("projects").select("created_by").eq("id", projectId).single();
      const founders = [c.kind === "user" ? c.userId : null, p?.created_by].filter(Boolean) as string[];
      return { project_id: projectId, judged: await judgePending({ founderIds: founders, deadline }) };
    }
    return await syncProject(projectId, { phase: device && body.phase === undefined ? "voice" : phase, deadline, device });
  }
  if (c.kind !== "service") throw new HttpError(403, "forbidden", "project_id is required.");

  if (phase === "judge") {
    const judged = await judgePending({ limit: 30, deadline: deadline - 40_000 });
    // New chunks of any project (e.g. a GitHub file synced on demand) get embedded here.
    const { data: one } = await admin().from("document_chunks").select("project_id").is("embedding", null).limit(1);
    const emb = one?.[0] ? await embedPending(one[0].project_id, deadline) : null;
    return { judged, embedded: emb };
  }
  // Daily: every project with something to read, least recently synced first.
  const { data: projects } = await admin().from("projects").select("id, url, github_repo").is("duplicate_of", null);
  const { data: last } = await admin().from("source_syncs").select("project_id, last_synced_at");
  const lastBy = new Map<string, string>();
  for (const r of last ?? []) if (!lastBy.has(r.project_id) || r.last_synced_at > lastBy.get(r.project_id)!) lastBy.set(r.project_id, r.last_synced_at);
  const order = (projects ?? []).sort((a, b) => (lastBy.get(a.id) ?? "").localeCompare(lastBy.get(b.id) ?? ""));
  const done = [];
  for (const p of order) {
    if (Date.now() > deadline - 30_000) break;
    try {
      const r = await syncProject(p.id, { phase, deadline: Math.min(deadline, Date.now() + 60_000) });
      done.push({ project_id: p.id, new_writing: r.voice.new, documents: r.knowledge?.written ?? 0, sources: r.sources.map((s) => `${s.source}:${s.status}`) });
    } catch (e) {
      done.push({ project_id: p.id, error: (e as Error).message.slice(0, 200) });
    }
  }
  return { projects: order.length, synced: done.length, results: done };
});
