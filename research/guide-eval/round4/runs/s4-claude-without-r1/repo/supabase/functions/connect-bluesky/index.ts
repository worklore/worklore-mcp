// POST /functions/v1/connect-bluesky  {project_id, handle, app_password}
// Verifies the app password with createSession, keeps it in Vault (never
// returned), upserts the account, starts a first poll in the background.
// docs/API.md › connect-bluesky

import "../_shared/connectors/mod.ts";
import { createSession, normaliseHandle, resolveAccount } from "../_shared/connectors/bluesky/client.ts";
import { blueskyConnector } from "../_shared/connectors/bluesky/connector.ts";
import { applyAccountPatch, knownExternalIds, storeBatch } from "../_shared/core/pipeline.ts";
import { triagePending } from "../_shared/core/triage_run.ts";
import type { AccountRow } from "../_shared/core/types.ts";
import { admin, background, requireMember, requireUser } from "../_shared/server/ctx.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";

serve(async (req, body) => {
  const c = await requireUser(req);
  if (!blueskyConnector.enabled()) throw new HttpError(422, "connector_disabled", "Bluesky is coming later.");
  const projectId = uuid(body.project_id, "project_id")!;
  await requireMember(c, projectId);
  const handle = normaliseHandle(str(body.handle, "handle", { required: true, max: 253 })!);
  const password = str(body.app_password, "app_password", { required: true, max: 200 })!.trim();
  if (!/^[a-z0-9.-]+$/.test(handle)) throw bad("That doesn't look like a Bluesky handle.");

  const { did, pds } = await resolveAccount(handle);
  const session = await createSession(pds, did, password);

  const db = admin();
  const { data: acct, error } = await db.from("accounts").upsert({
    project_id: projectId, platform: "bluesky", handle: session.handle.toLowerCase(), external_id: session.did,
    auth: "app_password", connected_by: c.userId, active: true, last_error: null, settings: { pds },
  }, { onConflict: "project_id,platform,handle" }).select("id, project_id, platform, handle, external_id, auth, active, last_polled_at, cursor, settings").single();
  if (error) throw error;
  const { error: e1 } = await db.rpc("store_account_secret", { p_account: acct.id, p_secret: password });
  if (e1) throw e1;
  const { error: e2 } = await db.rpc("store_account_session", { p_account: acct.id, p_session: JSON.stringify(session) });
  if (e2) throw e2;

  background((async () => {
    const a = { ...acct, project_id: projectId } as AccountRow;
    const batch = await blueskyConnector.sync!(a, { run: undefined, known: (p, ids) => knownExternalIds(p, "bluesky", ids) });
    await storeBatch(projectId, a, batch);
    await applyAccountPatch(a, batch.account, !batch.skipped);
    await triagePending({ projectId, limit: 6, deadlineMs: 100_000 });
  })());
  const { cursor: _c, settings: _s, ...pub } = acct;
  return { account: pub };
});
