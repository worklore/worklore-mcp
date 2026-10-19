// Triage one stored item and route it (docs/API.md › triage):
//   feedback  → stays "Needs you" (status new), filed under an idea, person → gave_feedback
//   draft       → full default draft → draft_ready
//   short_draft → one-line draft → draft_ready
//   skip        → skipped, skip_reason "auto: …" (decider said skip, emoji-only, bare thanks, ignore)
// Items she already answered keep their status; triage is still stored.

import { triageItem, TriageInput, TriageResult } from "../draft/mod.ts";
import { admin, projectFounder } from "../server/ctx.ts";
import { tagUsage } from "../server/usage.ts";
import { HttpError } from "../server/http.ts";
import { decider, utilityProvider } from "../server/models.ts";
import { makeDraft } from "./draft_run.ts";
import { fileFeedback } from "./ideas.ts";

export interface TriageOut {
  item_id: string;
  triage: TriageResult;
  status: string;
  idea_id: string | null;
  draft_id: string | null;
  draft_error?: string;
}

const EARLY_STAGES = ["noticed", "talking", "engaged"];

/**
 * Pure: a discovered post's triage, from the relevance decision Discover
 * already made (no model call). Discovered posts are not addressed to her, so
 * they are never auto-drafted ("Join" drafts one); the triage makes them
 * sortable and stops the catch-up job from treating them as untriaged.
 */
export function discoveryTriage(discovery: Record<string, unknown> | null): Record<string, unknown> {
  const d = discovery ?? {};
  const action = String(d.action ?? "leave");
  const route = action === "comment_to_engage" ? "draft" : action === "flag_for_founder" ? "decide_queue" : "skip";
  const p = typeof d.p_relevant === "number" ? d.p_relevant : null;
  return {
    kind: "engagement", code: "b", route, not_sure: p !== null && p < 0.6,
    summary: String(d.why ?? d.title ?? "").slice(0, 200),
    suggested_action: route === "decide_queue" ? "not_now" : null,
    confidence: p ?? 0, probabilities: { kind: { engagement: 1 }, action: { [route]: 1 } },
    decider_action: route, policy: "discover: relevance decision; drafted only when she joins",
    decider: String(d.decider ?? "discover"), model: "discover", usage: { tokens_in: null, tokens_out: null }, latency_ms: 0,
  };
}

export async function triageAndRoute(itemId: string, opts: { draft?: boolean } = {}): Promise<TriageOut> {
  const db = admin();
  const { data: item, error } = await db.from("items").select("*").eq("id", itemId).maybeSingle();
  if (error) throw error;
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  tagUsage({ project_id: item.project_id, item_id: itemId });
  if (item.origin === "discover") {
    const t = discoveryTriage(item.discovery) as unknown as TriageResult;
    await db.from("items").update({ triage: t, triaged_at: item.triaged_at ?? new Date().toISOString() }).eq("id", itemId);
    return { item_id: itemId, triage: t, status: item.status, idea_id: null, draft_id: null };
  }
  const founderId = await projectFounder(item.project_id);
  const [{ data: project }, { data: founder }, { data: ident }, { data: acct }] = await Promise.all([
    db.from("projects").select("name, one_liner").eq("id", item.project_id).single(),
    db.from("founders").select("display_name").eq("id", founderId ?? "00000000-0000-0000-0000-000000000000").maybeSingle(),
    db.from("identities").select("handle").eq("person_id", item.person_id).eq("platform", item.platform).limit(1).maybeSingle(),
    item.account_id ? db.from("accounts").select("handle").eq("id", item.account_id).maybeSingle() : Promise.resolve({ data: null }),
  ]);
  const own = (acct as { handle?: string } | null)?.handle ?? "";
  const input: TriageInput = {
    project: { name: project!.name, one_liner: project!.one_liner, founder_name: founder?.display_name ?? null, founder_handle: own || null },
    context: {
      platform: item.platform,
      kind: item.kind === "post" ? "mention" : item.kind,
      post: item.my_post ? { title: item.my_post.title, url: item.my_post.url, text: item.my_post.text ?? "", author: item.my_post.author ?? own, is_owner: item.my_post.is_owner ?? true } : null,
      chain: (item.thread ?? []).map((m: Record<string, unknown>) => ({ author: m.author as string, text: m.text as string, is_owner: (m.is_owner as boolean) ?? m.author === own })),
      item: { author: ident?.handle ?? "someone", text: item.text, posted_at: item.posted_at },
    },
  };
  const dec = decider();
  const open = item.status === "new" || item.status === "draft_ready";
  // The one-line summary costs a Gemini call: only for items still waiting on her.
  const t = await triageItem(input, dec, open ? { summarizer: utilityProvider(undefined, "triage_summary") } : {}).catch((e) => {
    // The summariser (Gemini) may be out of budget; triage itself must not fail for that.
    if (String((e as Error).message).includes("budget")) return triageItem(input, dec);
    throw e;
  });
  const now = new Date().toISOString();
  await db.from("items").update({ triage: t, triaged_at: now }).eq("id", itemId);

  const out: TriageOut = { item_id: itemId, triage: t, status: item.status, idea_id: null, draft_id: null };

  if (t.route === "decide_queue") {
    out.idea_id = await fileFeedback(dec, { id: itemId, project_id: item.project_id, person_id: item.person_id, text: item.text, summary: t.summary });
    await db.from("people").update({ stage: "gave_feedback" }).eq("id", item.person_id).in("stage", EARLY_STAGES);
    if (item.status === "draft_ready") {
      // Re-triaged into Decide: an earlier auto-draft no longer applies (kept, superseded).
      await db.from("drafts").update({ outcome: "superseded", decided_at: now }).eq("item_id", itemId).is("outcome", null);
      await db.from("items").update({ status: "new" }).eq("id", itemId).eq("status", "draft_ready");
      out.status = "new";
    }
  } else if (t.route === "spam_check") {
    // Looks like a plug: no draft until she decides (hide as spam / not spam).
    if (item.status === "draft_ready") {
      await db.from("drafts").update({ outcome: "superseded", decided_at: now }).eq("item_id", itemId).is("outcome", null);
      await db.from("items").update({ status: "new" }).eq("id", itemId).eq("status", "draft_ready");
      out.status = "new";
    }
  } else if (t.route === "skip") {
    if (open) {
      await db.from("items").update({ status: "skipped", skip_reason: `auto: ${t.policy ?? t.kind}` }).eq("id", itemId).in("status", ["new", "draft_ready"]);
      // Any undecided auto-draft stays in history, superseded.
      await db.from("drafts").update({ outcome: "superseded", decided_at: now }).eq("item_id", itemId).is("outcome", null);
      out.status = "skipped";
    }
  } else if (open && opts.draft !== false) {
    try {
      const d = await makeDraft(itemId, { founderId, intent: "auto", length: t.route === "short_draft" ? "one_line" : "full" });
      out.draft_id = d.draft_id;
      out.status = "draft_ready";
    } catch (e) {
      out.draft_error = (e as Error).message.slice(0, 200);
      console.error("default draft failed:", out.draft_error);
    }
  }
  return out;
}

/**
 * Untriaged items (no triage stored), oldest first: cron + after ingest/poll.
 * Inbox and discovered items both (2026-10-09: discovered posts were stored
 * with triaged_at set and no triage, so this job never saw them).
 */
export async function triagePending(opts: { projectId?: string; limit?: number; deadlineMs?: number } = {}) {
  const db = admin();
  let q = db.from("items").select("id").is("triage", null).in("origin", ["inbox", "discover"]).order("fetched_at", { ascending: true }).limit(opts.limit ?? 8);
  if (opts.projectId) q = q.eq("project_id", opts.projectId);
  const { data, error } = await q;
  if (error) throw error;
  const t0 = Date.now();
  const results: { item_id: string; route?: string; error?: string }[] = [];
  for (const r of data ?? []) {
    if (opts.deadlineMs && Date.now() - t0 > opts.deadlineMs) break;
    try {
      const o = await triageAndRoute(r.id);
      results.push({ item_id: r.id, route: o.triage.route });
    } catch (e) {
      results.push({ item_id: r.id, error: (e as Error).message.slice(0, 160) });
      // Model quota exhausted: stop for now, the cron will come back.
      if (/budget|429|quota/i.test((e as Error).message)) break;
    }
  }
  return results;
}
