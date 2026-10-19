// One scheduled worker per connector (poll-devto-public, poll-bluesky): each
// is a thin function over pollConnector(id). The connector brings its own
// rate rules (beginRun → a rate-limited client shared by the run's accounts).

import { admin, caller, requireMember } from "../server/ctx.ts";
import { HttpError, uuid } from "../server/http.ts";
import { applyAccountPatch, knownExternalIds, storeBatch } from "./pipeline.ts";
import { connector } from "./registry.ts";
import { triagePending } from "./triage_run.ts";
import type { AccountRow } from "./types.ts";

export const RUN_BUDGET_MS = 110_000;

export async function pollConnector(id: string, req: Request, body: Record<string, unknown>) {
  const conn = connector(id);
  if (!conn?.sync) throw new HttpError(404, "not_found", `No connector ${id}.`);
  const c = await caller(req);
  const projectId = uuid(body.project_id, "project_id", c.kind === "user");
  if (projectId) await requireMember(c, projectId);
  if (!conn.enabled()) return { disabled: true, accounts: 0, new_items: 0, triaged: 0, errors: [] };

  let q = admin().from("accounts").select("id, project_id, platform, handle, external_id, cursor, settings, secret_id")
    .eq("platform", id).eq("active", true);
  if (conn.needsSecret) q = q.not("secret_id", "is", null);
  if (projectId) q = q.eq("project_id", projectId);
  const { data: accounts, error } = await q;
  if (error) throw error;

  const t0 = Date.now();
  const ctx = { run: conn.beginRun?.(), known: (p: string, ids: string[]) => knownExternalIds(p, id, ids) };
  let newItems = 0;
  const stats: Record<string, number> = {};
  const errors: string[] = [];
  for (const a of (accounts ?? []) as AccountRow[]) {
    try {
      const batch = await conn.sync(a, ctx);
      const r = await storeBatch(a.project_id, a, batch);
      newItems += r.inserted.length;
      for (const [k, v] of Object.entries(batch.stats ?? {})) stats[k] = (stats[k] ?? 0) + v;
      await applyAccountPatch(a, batch.account, !batch.skipped);
    } catch (e) {
      const msg = (e as Error).message.slice(0, 200);
      errors.push(`${a.handle}: ${msg}`);
      await admin().from("accounts").update({ last_error: msg }).eq("id", a.id);
    }
  }
  const left = RUN_BUDGET_MS - (Date.now() - t0);
  const triaged = left > 15_000 ? await triagePending({ projectId, limit: 6, deadlineMs: left - 15_000 }) : [];
  return { accounts: accounts?.length ?? 0, ...stats, new_items: newItems, triaged: triaged.filter((t) => t.route).length, errors };
}
