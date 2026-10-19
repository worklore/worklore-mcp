// POST /functions/v1/knowledge-ingest  {project_id, phase?: 'all'|'fetch'|'embed'}
// Kept for scripts and older callers: the knowledge half of the sources
// pipeline (sources-sync phase 'knowledge'). Sources are no longer configured
// per project (projects.knowledge_sources is ignored): the landing site, the
// connected accounts' published work, the GitHub folder. phase 'embed' only
// embeds pending chunks. docs/API.md › knowledge-ingest

import "../_shared/connectors/mod.ts";
import { syncProject } from "../_shared/core/sources/run.ts";
import { caller, requireMember } from "../_shared/server/ctx.ts";
import { bad, serve, uuid } from "../_shared/server/http.ts";
import { embedPending } from "../_shared/server/knowledge.ts";

serve(async (req, body) => {
  const t0 = Date.now();
  const c = await caller(req);
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  const phase = (body.phase as string) ?? "all";
  if (!["all", "fetch", "embed"].includes(phase)) throw bad("phase must be all, fetch or embed");
  if (phase === "embed") return await embedPending(projectId, t0 + 135_000);
  const r = await syncProject(projectId, { phase: "knowledge", deadline: t0 + 110_000 });
  return { ...(r.knowledge ?? {}), embedded: r.embedded, pending: r.pending_chunks, sources: r.sources };
});
