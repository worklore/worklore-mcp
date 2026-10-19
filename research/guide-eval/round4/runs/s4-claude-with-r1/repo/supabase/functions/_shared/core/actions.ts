// Core actions on an item. Reply on the server = the item's connector posts
// (reply mode "server"), then record_draft_outcome records it as the founder
// (RLS and decided_by apply). Replies in mode "device" are posted by the phone,
// which then calls record_draft_outcome itself. Never posts without her tap.

import { admin, Caller } from "../server/ctx.ts";
import { HttpError } from "../server/http.ts";
import { hasUnresolvedCheck } from "../draft/checks.ts";
import { graphemeLength } from "../server/text.ts";
import { connector } from "./registry.ts";
import type { AccountRow, ItemRow } from "./types.ts";

export const STAGES = ["noticed", "talking", "gave_feedback", "would_try", "would_pay", "engaged", "supporter", "customer", "not_a_fit"];

export async function replyOnServer(c: Extract<Caller, { kind: "user" }>, opts: {
  draftId: string; text: string; moveStage?: string | null; platform: string;
}) {
  // Never post a gap, whatever the network.
  if (hasUnresolvedCheck(opts.text)) throw new HttpError(422, "unfilled_check", "Answer or drop the [check: …] parts first.");
  const conn = connector(opts.platform);
  if (!conn?.postReply || conn.reply.mode !== "server") throw new HttpError(422, "bad_request", `Replies on ${opts.platform} are not posted by the server.`);
  if (!conn.enabled()) throw new HttpError(422, "connector_disabled", `${conn.label} is not available yet.`);
  const text = opts.text.trim();
  if (opts.moveStage && !STAGES.includes(opts.moveStage)) throw new HttpError(400, "bad_request", "Unknown stage.");
  if (!text) throw new HttpError(400, "bad_request", "final_text is empty");
  const max = conn.reply.maxGraphemes;
  const len = graphemeLength(text);
  if (max && len > max) throw new HttpError(422, "too_long", `${conn.label} allows ${max} characters; this is ${len}.`, { length: len, max });

  // Read through the founder's own client: RLS decides whether she may see it.
  const { data: draft } = await c.db.from("drafts").select("id, text, outcome, item_id").eq("id", opts.draftId).maybeSingle();
  if (!draft) throw new HttpError(404, "not_found", "No such draft.");
  if (draft.outcome) throw new HttpError(409, "already_decided", "This draft was already posted or skipped.");
  const { data: item } = await c.db.from("items").select("id, project_id, platform, account_id, kind, external_id, root_ref, parent_ref")
    .eq("id", draft.item_id).maybeSingle();
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  if (item.platform !== conn.id) throw new HttpError(422, `not_${conn.id}`, `This item is not on ${conn.label}.`);

  const db = admin();
  let q = db.from("accounts").select("id, project_id, platform, handle, external_id, cursor, settings, secret_id")
    .eq("project_id", item.project_id).eq("platform", conn.id).eq("active", true);
  if (conn.needsSecret) q = q.not("secret_id", "is", null);
  const { data: accts } = await q;
  const account = ((accts ?? []) as AccountRow[]).find((a) => a.id === item.account_id) ?? (accts ?? [])[0] as AccountRow | undefined;
  if (!account) throw new HttpError(422, `${conn.id}_not_connected`, `Connect ${conn.label} first.`);

  const posted = await conn.postReply(account, item as ItemRow, text);
  const outcome = text === draft.text.trim() ? "posted_as_is" : "posted_edited";
  const { data: decided, error } = await c.db.rpc("record_draft_outcome", {
    p_draft_id: opts.draftId, p_outcome: outcome, p_final_text: text, p_posted_url: posted.url, p_move_stage: opts.moveStage ?? null,
  });
  if (error) {
    // Posted, but recording failed (e.g. a teammate decided meanwhile): say so, don't hide the post.
    return { uri: posted.external_id, url: posted.url, draft: null, warning: `Posted, but not recorded: ${error.message}` };
  }
  return { uri: posted.external_id, url: posted.url, draft: decided };
}
