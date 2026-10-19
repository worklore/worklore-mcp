// POST /functions/v1/triage  {item_id}  → re-triage one item (founder or service)
//                            {pending: true, project_id?} → triage untriaged items (cron)
// docs/API.md › triage

import "../_shared/connectors/mod.ts";
import { triageAndRoute, triagePending } from "../_shared/core/triage_run.ts";
import { admin, caller, requireMember } from "../_shared/server/ctx.ts";
import { HttpError, serve, uuid } from "../_shared/server/http.ts";

serve(async (req, body) => {
  const c = await caller(req);
  if (body.pending === true) {
    const projectId = uuid(body.project_id, "project_id", c.kind === "user");
    if (projectId) await requireMember(c, projectId);
    const results = await triagePending({ projectId, limit: 8, deadlineMs: 100_000 });
    return { triaged: results.filter((r) => r.route).length, results };
  }
  const itemId = uuid(body.item_id, "item_id")!;
  const { data: item } = await admin().from("items").select("project_id").eq("id", itemId).maybeSingle();
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  await requireMember(c, item.project_id).catch(() => { throw new HttpError(404, "not_found", "No such item."); });
  return await triageAndRoute(itemId);
});
