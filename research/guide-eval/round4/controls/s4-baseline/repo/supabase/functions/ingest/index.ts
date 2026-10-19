// POST /functions/v1/ingest  {project_id, source, account_handle, items:[…]}
// The phone reads a network with the founder's own session (which never leaves
// the phone) and sends what it read here. `source` is the connector id; the
// connector normalizes the items, the core stores and triages them.
// docs/API.md › ingest

import "../_shared/connectors/mod.ts";
import { applyAccountPatch, storeBatch } from "../_shared/core/pipeline.ts";
import { connector } from "../_shared/core/registry.ts";
import { triageAndRoute } from "../_shared/core/triage_run.ts";
import type { AccountRow } from "../_shared/core/types.ts";
import { admin, requireMember, requireUser } from "../_shared/server/ctx.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";

serve(async (req, body) => {
  const c = await requireUser(req);
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  const source = str(body.source, "source", { required: true, max: 40 })!;
  const conn = connector(source);
  if (!conn?.normalizeIngest) throw bad(`source must be one of the connectors that read on the phone`);
  if (!conn.enabled()) throw new HttpError(422, "connector_disabled", `${conn.label} is not available yet.`);
  const handle = str(body.account_handle, "account_handle", { required: true, max: 60 })!.replace(/^@/, "");
  if (!Array.isArray(body.items)) throw bad("items must be an array");
  if (body.items.length > 50) throw bad("at most 50 items per call");

  const { data: acct, error } = await admin().from("accounts").upsert(
    { project_id: projectId, platform: conn.id, handle, auth: conn.accountAuth, connected_by: c.userId },
    { onConflict: "project_id,platform,handle", ignoreDuplicates: false },
  ).select("id, project_id, platform, handle, external_id, cursor, settings").single();
  if (error) throw error;

  const { batch, rejected } = await conn.normalizeIngest(body.items, acct as AccountRow);
  const r = await storeBatch(projectId, acct, batch);
  if (batch.account) await applyAccountPatch(acct as AccountRow, batch.account, false);

  const t0 = Date.now();
  let triaged = 0;
  for (const id of r.inserted.slice(0, 10)) {
    if (Date.now() - t0 > 90_000) break;
    try { await triageAndRoute(id); triaged++; } catch (e) { console.error("triage:", (e as Error).message.slice(0, 160)); }
  }
  return { received: body.items.length, inserted: r.inserted.length, duplicates: r.duplicates, own_replies: r.own_replies, rejected, item_ids: r.inserted, triaged };
});
