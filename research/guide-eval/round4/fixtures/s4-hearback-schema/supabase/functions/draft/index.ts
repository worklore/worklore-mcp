// POST /functions/v1/draft
//   {item_id, intent?, variant?, gist?, length?}             → a new draft version (redraft + gist: built on her point;
//                                                              no length: the previous version's)
//   {item_id, draft_id, text?, resolve: [{check_id, answer} | {check_id, drop: true}]}
//                                                            → a new version with those [check: …] gaps resolved
//   {item_id, draft_id, checks_only: true}                   → the draft's gaps with ids and spans (read-only)
//   {item_id, points: true}                                  → {points: [{text, source}]}: 2–3 points from what she
//                                                              already said, for the redraft prompt (read-only)
// → {draft_id, version, text, intent, variant, checks, check_spans, sources, model, provider, limit, lint, …}
// Stores a new drafts version (older undecided ones are superseded) and marks
// the item draft_ready. Never posts. docs/API.md › draft

import "../_shared/connectors/mod.ts";
import { draftChecks, draftPoints, INTENTS, Intent, makeDraft, resolveDraft } from "../_shared/core/draft_run.ts";
import type { Resolution } from "../_shared/draft/mod.ts";
import { admin, caller, projectFounder, requireMember } from "../_shared/server/ctx.ts";
import { bad, HttpError, serve, str, uuid } from "../_shared/server/http.ts";

serve(async (req, body) => {
  const c = await caller(req); // a founder, or the service role (scripts): then the draft is in the project founder's voice
  const itemId = uuid(body.item_id, "item_id")!;
  const { data: item } = await admin().from("items").select("project_id").eq("id", itemId).maybeSingle();
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  await requireMember(c, item.project_id).catch(() => { throw new HttpError(404, "not_found", "No such item."); });
  const founderId = c.kind === "user" ? c.userId : await projectFounder(item.project_id);
  if (!founderId) throw new HttpError(409, "no_founder", "The project has no founder.");
  const requestedBy = c.kind === "user" ? c.userId : null;

  if (body.checks_only === true) return await draftChecks(itemId, uuid(body.draft_id, "draft_id")!);
  if (body.points === true) return await draftPoints(itemId, { founderId, requestedBy });

  if (body.resolve !== undefined) {
    const draftId = uuid(body.draft_id, "draft_id")!;
    const text = str(body.text, "text", { max: 20000 }) ?? null;
    if (!Array.isArray(body.resolve) || !body.resolve.length || body.resolve.length > 20) throw bad("resolve must be a list of 1–20 {check_id, answer} or {check_id, drop: true}");
    const resolutions: Resolution[] = body.resolve.map((r: unknown, i: number) => {
      if (!r || typeof r !== "object") throw bad(`resolve[${i}] must be an object`);
      const o = r as Record<string, unknown>;
      const checkId = str(o.check_id, `resolve[${i}].check_id`, { required: true, max: 10 })!;
      if (!/^c\d+$/.test(checkId)) throw bad(`resolve[${i}].check_id must look like c1`);
      const drop = o.drop === true;
      const answer = str(o.answer, `resolve[${i}].answer`, { max: 2000 }) ?? null;
      if (!drop && !answer?.trim()) throw bad(`resolve[${i}] needs an answer, or drop: true`);
      if (drop && answer) throw bad(`resolve[${i}]: answer or drop, not both`);
      return { check_id: checkId, answer, drop };
    });
    return await resolveDraft(itemId, { draftId, text, resolutions, founderId, requestedBy });
  }

  const intent = (str(body.intent, "intent") ?? "auto") as Intent;
  if (!INTENTS.includes(intent)) throw bad(`intent must be one of ${INTENTS.join(", ")}`);
  const variant = str(body.variant, "variant") ?? "first";
  if (!["first", "shorter", "redraft"].includes(variant)) throw bad("variant must be first, shorter or redraft");
  const gist = str(body.gist, "gist", { max: 2000 }) ?? null;
  // No length: the version it replaces keeps its own (else triage's route decides).
  const length = str(body.length, "length") ?? null;
  if (length !== null && !["full", "one_line"].includes(length)) throw bad("length must be full or one_line");
  return await makeDraft(itemId, { founderId, requestedBy, intent, variant: variant as "first" | "shorter" | "redraft", gist, length: length as "full" | "one_line" | null });
});
