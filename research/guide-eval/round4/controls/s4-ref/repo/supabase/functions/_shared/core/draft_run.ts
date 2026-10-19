// One draft for one item, end to end: load the context (load.ts), retrieve her
// published work (match_document_chunks → MMR re-rank), shape by intent, call
// the model (prompt v4), enforce the platform's reply limit (from its
// connector), store a drafts row. Never posts anything.

import {
  CheckSpan, draftReply, DRAFT_KIND, draftRow, EmbeddedChunk, factContext, ItemKind, KnowledgeChunk, lint, loadDraftRequest, parseChecks, Point, Resolution,
  ResolvedCheck, resolveChecks, ResolveError, retrieve, suggestPoints, TriageKind, Variant,
} from "../draft/mod.ts";
import { admin, projectFounder } from "../server/ctx.ts";
import { tagUsage } from "../server/usage.ts";
import { HttpError } from "../server/http.ts";
import { draftProvider, embedder, fromVector, modelForUser, modelFounderFor, toVector } from "../server/models.ts";
import { clampGraphemes, firstSentence, graphemeLength } from "../server/text.ts";
import { replyLimit } from "./registry.ts";

/** "one_line" when triage routed the item to short_draft (the decider said a short reply is enough). */
export type DraftLength = "full" | "one_line";

/**
 * Pure: the length of a new version. Asked for → that; else the version it
 * replaces keeps its length (a chip tap no longer turns one line into 130
 * words); else what triage routed (short_draft → one line).
 */
export function draftLength(asked: DraftLength | null | undefined, previous: unknown, triageRoute: string | null | undefined): DraftLength {
  if (asked) return asked;
  if (previous === "one_line" || previous === "full") return previous;
  return triageRoute === "short_draft" ? "one_line" : "full";
}

/** Pure: her point for a new version. A new one wins; otherwise the version it replaces keeps its point. */
export function carriedGist(asked: string | null | undefined, previousMeta: unknown): { gist: string | null; newGist: string | null } {
  const newGist = asked?.trim() || null;
  const prev = (previousMeta as { gist?: unknown } | null | undefined)?.gist;
  return { gist: newGist ?? (typeof prev === "string" && prev.trim() ? prev.trim() : null), newGist };
}

export type Intent = "discuss" | "just_answer" | "invite_to_try" | "ask_feedback" | "ask_price" | "share_result" | "auto";
/**
 * ask_feedback: no longer offered (vague: feedback on what). ask_price is not a fixed chip; the app offers it when the
 * person wants to try (intent suggestion). share_result: the follow-up once their idea's issue is done (github-results).
 */
export const INTENTS: Intent[] = ["discuss", "just_answer", "invite_to_try", "ask_feedback", "ask_price", "share_result", "auto"];

/** The intent chip → an instruction the prompt carries as "her note". Pure; tested. */
export function intentNote(
  intent: Intent, project: { name: string; url?: string | null }, gist?: string | null, length: DraftLength = "full",
  /** share_result: what was done and the links (connectors/github/boards.ts › resultForDraft). */
  result?: string | null,
): string | null {
  const link = project.url ? ` (link: ${project.url})` : "";
  const goal: Record<Intent, string | null> = {
    auto: null,
    discuss: "Goal: keep the discussion going. Answer their point with her own view, taken from what she said in this thread or her published work (one concrete thing), then ask ONE open question about their experience that invites them to answer. A normal-size reply, not a closing one.",
    just_answer: "Goal: just answer what they said. Don't invite them to anything and don't ask about the product.",
    invite_to_try: `Goal: answer their point first, then invite them to try ${project.name} in one plain sentence${link}. No hype, no pressure.`,
    ask_feedback: `Goal: answer briefly, then ask them ONE specific question that would give her feedback on ${project.name}, tied to what they said.`,
    ask_price: `Goal: answer briefly, then ask ONE honest question about whether ${project.name} doing this for them would be worth paying for, or what they use or pay for today. Name the problem in their words. No sales tone, no price offer.`,
    share_result: "Goal: a follow-up, some time after their message. What they asked for or talked about is now done (built, fixed or researched). Tell them so in plain words, say what changed in one or two concrete sentences taken ONLY from the result below, and point to the one link that shows it best. Don't claim more than the result says; where a fact is missing, leave a [check: …] gap. No hype, no thanks-for-the-feedback opener, no question unless trying it needs one.",
  };
  const parts = [
    goal[intent],
    intent === "share_result" && result?.trim() ? `The result:\n${result.trim()}` : null,
    length === "one_line" ? "Length: ONE short sentence (at most 20 words). No question back unless they asked one." : null,
    gist?.trim() ? `What she wants to say: ${gist.trim()}` : null,
  ].filter(Boolean);
  return parts.length ? parts.join("\n") : null;
}

/** "[check: did you try X?]" → "did you try X?" */
export function checksOf(placeholders: string[]): string[] {
  return placeholders.map((p) => p.replace(/^\[\s*check:\s*/i, "").replace(/\]\s*$/, "").trim()).filter(Boolean);
}

export interface DraftOut {
  draft_id: string;
  version: number;
  text: string;
  intent: Intent;
  variant: Variant | "resolve";
  checks: string[];
  /** The same gaps with an id and their exact place in `text` (draft/checks.ts). */
  check_spans: CheckSpan[];
  sources: { title: string; url: string | null; kind: string; published_at: string }[];
  length: DraftLength;
  model: string;
  provider: string;
  /** Why this model: "override" (her pick), "plan default", "env" (DRAFT_MODEL). */
  model_reason: string;
  limit: { unit: "graphemes"; max: number; length: number } | null;
  lint: unknown;
}

async function knowledgeFor(projectId: string, query: string): Promise<KnowledgeChunk[]> {
  try {
    const [vec] = await embedder().embed([query.slice(0, 6000)], "query");
    const { data, error } = await admin().rpc("match_document_chunks", {
      p_project: projectId, p_query: toVector(vec), p_before: new Date().toISOString(), p_count: 40, p_labels: ["quotable"],
    });
    if (error) throw error;
    const pool: EmbeddedChunk[] = (data ?? []).map((r: Record<string, unknown>) => ({
      id: r.id as string, kind: r.kind as KnowledgeChunk["kind"], title: r.title as string, source_url: r.source_url as string | null,
      source_ref: (r.source_ref as string) ?? undefined, published_at: new Date(r.published_at as string).toISOString(),
      text: r.content as string, tokens: r.tokens as number, lang: r.lang as string, embedding: fromVector(r.embedding),
    }));
    return retrieve(vec, pool, { k: 6 });
  } catch (e) {
    console.error("knowledge retrieval skipped:", (e as Error).message.slice(0, 200));
    return [];
  }
}

export async function makeDraft(itemId: string, opts: {
  /** The founder whose voice the draft is in (default: the project founder). */
  founderId?: string | null;
  /** The signed-in founder who asked for it in the app (null for automatic drafts); picks the model. */
  requestedBy?: string | null;
  intent?: Intent; variant?: Variant; gist?: string | null; length?: DraftLength | null;
  /** share_result: the result text the note carries (kept on the draft so Shorter/Longer still have it). */
  result?: string | null;
}): Promise<DraftOut> {
  const db = admin();
  const { data: item, error } = await db.from("items")
    .select("id, project_id, platform, kind, text, origin, status, triage, triage_route, my_post, assigned_to").eq("id", itemId).maybeSingle();
  if (error) throw error;
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  tagUsage({ project_id: item.project_id, item_id: itemId });
  const founderId = opts.founderId ?? await projectFounder(item.project_id);
  if (!founderId) throw new HttpError(409, "no_founder", "The project has no founder.");
  const intent = opts.intent ?? "auto";
  const variant = opts.variant ?? "first";
  const { data: prevRow } = await db.from("drafts").select("meta").eq("item_id", itemId).order("version", { ascending: false }).limit(1).maybeSingle();
  // Her point stays with every later version (Longer, Shorter, a chip) until she gives a new one.
  const { gist, newGist } = carriedGist(opts.gist, prevRow?.meta);
  // Discuss is a normal-size reply by definition, and a new point of hers is
  // a seed to grow, not to squeeze: neither inherits one line.
  const length = draftLength(opts.length ?? (intent === "discuss" || newGist ? "full" : null), prevRow?.meta?.length, item.triage_route);

  const { data: project } = await db.from("projects").select("name, url, settings").eq("id", item.project_id).single();
  // A share_result redraft without a new result keeps the one the version before had.
  const resultText = intent === "share_result" ? (opts.result?.trim() || (typeof prevRow?.meta?.result === "string" ? prevRow.meta.result : null)) : null;
  const { req, nextVersion } = await loadDraftRequest(db, itemId, founderId, { variant, note: intentNote(intent, project!, gist, length, resultText) });
  req.gist = gist;
  // Longer: a one-line version grown into a full reply, same point.
  req.expand = variant === "redraft" && length === "full" && prevRow?.meta?.length === "one_line";
  if (variant !== "first" && !req.previous_draft) throw new HttpError(400, "bad_request", `variant '${variant}' needs an earlier draft`);
  const tk = item.triage?.kind as TriageKind | undefined;
  req.item_kind = (tk ? DRAFT_KIND[tk] : null) ?? (item.origin === "discover" ? "engagement" : null) as ItemKind | null;
  if (req.item_kind === "feedback") req.item_kind = "engagement"; // she asked for a draft: answer it like a discussion
  req.knowledge = await knowledgeFor(item.project_id, [item.my_post?.title, item.text].filter(Boolean).join("\n\n"));

  // The model is personal: the requester's, else the item's assignee's, else the owner's (founderId).
  const choice = await modelForUser(modelFounderFor({ requestedBy: opts.requestedBy, assignedTo: item.assigned_to, owner: founderId }));
  const provider = draftProvider(choice.spec, project?.settings?.draft_effort);
  let result = await draftReply(req, provider, { promptVersion: "v4" });
  let text = result.text;
  // A one-line draft is one line, even when the model wrote more.
  if (length === "one_line" && text.split(/\s+/).length > 30) text = firstSentence(text, 220);
  const max = replyLimit(item.platform);
  if (max && graphemeLength(text) > max) {
    try {
      const shorter = await draftReply({ ...req, variant: "shorter", previous_draft: text }, provider, { promptVersion: "v4" });
      if (graphemeLength(shorter.text) < graphemeLength(text)) { result = { ...shorter, instruction: result.instruction }; text = shorter.text; }
    } catch (e) {
      console.error("shorten failed:", (e as Error).message.slice(0, 120));
    }
    text = clampGraphemes(text, max);
  }

  const used = new Set(result.context_report.knowledge_ids ?? []);
  const sources = (req.knowledge ?? []).filter((k) => used.has(k.id))
    .map((k) => ({ title: k.title, url: k.source_url, kind: k.kind, published_at: k.published_at }));
  const checks = checksOf(text.match(/\[check:[^\]]*\]/gi) ?? []);
  const base = draftRow(itemId, nextVersion, { ...result, text });
  const row = {
    ...base,
    // model = who actually wrote it (a Claude failure falls back to Gemini); model_choice = what was asked for and why.
    tokens: { ...(base.tokens ?? {}), model_choice: { requested: choice.spec, reason: choice.reason, founder_id: choice.founder_id, plan_id: choice.plan_id } },
    intent, variant, checks, sources, lint: result.lint,
    meta: { length, ...(req.gist ? { gist: req.gist } : {}), ...(resultText ? { result: resultText } : {}) },
  };
  // A follow-up brings an answered conversation back to the inbox.
  const ins = await storeDraft(itemId, row, item.status, intent === "share_result" ? ["new", "answered"] : ["new"]);
  return {
    draft_id: ins.id, version: ins.version, text, intent, variant, checks, check_spans: parseChecks(text), sources, length,
    model: result.model, provider: result.provider, model_reason: choice.reason,
    limit: max ? { unit: "graphemes", max, length: graphemeLength(text) } : null,
    lint: result.lint,
  };
}

/**
 * Inserts a new drafts version (renumbering once if a parallel draft took the
 * number), supersedes the older undecided ones, and marks the item
 * draft_ready when its status is one of `reopen` (a `new` one; for a
 * follow-up also an answered one).
 */
// deno-lint-ignore no-explicit-any
async function storeDraft(itemId: string, row: Record<string, any>, itemStatus: string, reopen = ["new"]): Promise<{ id: string; version: number }> {
  const db = admin();
  let ins = await db.from("drafts").insert(row).select("id, version").single();
  if (ins.error?.code === "23505") {
    // A parallel draft took this version number.
    const { data: top } = await db.from("drafts").select("version").eq("item_id", itemId).order("version", { ascending: false }).limit(1);
    ins = await db.from("drafts").insert({ ...row, version: (top?.[0]?.version ?? 0) + 1 }).select("id, version").single();
  }
  if (ins.error) throw ins.error;
  await db.from("drafts").update({ outcome: "superseded", decided_at: new Date().toISOString() })
    .eq("item_id", itemId).lt("version", ins.data.version).is("outcome", null);
  if (reopen.includes(itemStatus)) await db.from("items").update({ status: "draft_ready" }).eq("id", itemId).eq("status", itemStatus);
  return ins.data;
}

/** The undecided draft of this item, or a clear error. */
async function openDraft(itemId: string, draftId: string) {
  const { data: d, error } = await admin().from("drafts")
    .select("id, item_id, version, text, intent, sources, lint, outcome, meta").eq("id", draftId).maybeSingle();
  if (error) throw error;
  if (!d || d.item_id !== itemId) throw new HttpError(404, "not_found", "No such draft for this item.");
  return d;
}

/** Read-only: a draft's gaps with ids and spans (nothing is written). */
export async function draftChecks(itemId: string, draftId: string) {
  const d = await openDraft(itemId, draftId);
  const spans = parseChecks(d.text);
  return { draft_id: d.id, version: d.version, text: d.text, outcome: d.outcome, checks: spans.map((c) => c.question), check_spans: spans };
}

export interface ResolveOut extends DraftOut {
  /** What was resolved, and how (model edit or the deterministic fallback). */
  resolved: ResolvedCheck[];
  /** The version it was made from. */
  based_on: { draft_id: string; version: number };
}

/**
 * She answered or dropped [check: …] gaps: a new version that changes the
 * draft only where those gaps were (draft/resolve.ts), stored like any other
 * version (the old one superseded). Her answers are kept in drafts.meta.
 */
export async function resolveDraft(itemId: string, opts: {
  draftId: string;
  /** The text as she has it in the editor (her edits); default: the draft's text. Check ids refer to it. */
  text?: string | null;
  resolutions: Resolution[];
  founderId: string;
  requestedBy?: string | null;
}): Promise<ResolveOut> {
  const db = admin();
  const { data: item, error } = await db.from("items").select("id, project_id, platform, status, assigned_to, text").eq("id", itemId).maybeSingle();
  if (error) throw error;
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  tagUsage({ project_id: item.project_id, item_id: itemId });
  const base = await openDraft(itemId, opts.draftId);
  if (base.outcome) throw new HttpError(409, "already_decided", "This draft was already posted, skipped or replaced by a newer version.");
  const text = opts.text?.trim() ? opts.text.trim() : base.text;

  const { req, nextVersion } = await loadDraftRequest(db, itemId, opts.founderId, {});
  const choice = await modelForUser(modelFounderFor({ requestedBy: opts.requestedBy, assignedTo: item.assigned_to, owner: opts.founderId }));
  const { data: project } = await db.from("projects").select("settings").eq("id", item.project_id).single();
  // A small edit: low effort is enough, and it keeps the answer quick.
  const provider = draftProvider(choice.spec, project?.settings?.resolve_effort ?? "low", "resolve");
  let r;
  try {
    r = await resolveChecks({
      text, resolutions: opts.resolutions,
      founder_name: req.project.founder_name, voice_notes: req.project.voice_notes,
      replying_to: item.text, fact_context: factContext(req),
    }, provider);
  } catch (e) {
    if (e instanceof ResolveError) throw new HttpError(422, e.code, e.message, e.checkId ? { check_id: e.checkId } : undefined);
    throw e;
  }

  const spans = parseChecks(r.text);
  const target = (base.lint?.target_words ?? [0, 0]) as [number, number];
  const report = { ...lint(r.text, item.text ?? "", target, factContext(req)), invented_facts: r.invented };
  const summary = r.resolved.map((x) => `${x.action === "drop" ? "dropped" : "answered"} ${x.check_id}`).join(", ");
  const row = {
    item_id: itemId, version: nextVersion, instruction: `resolve: ${summary}`, text: r.text,
    provider: r.provider, model: r.model, latency_ms: r.latency_ms,
    tokens: { ...r.usage, model_choice: { requested: choice.spec, reason: choice.reason, founder_id: choice.founder_id, plan_id: choice.plan_id } },
    intent: base.intent, variant: "resolve", checks: spans.map((c) => c.question), sources: base.sources ?? [], lint: report,
    meta: {
      length: draftLength(null, base.meta?.length, null),
      // A follow-up's result stays with it (a later Shorter / Longer still has it).
      ...(typeof base.meta?.result === "string" ? { result: base.meta.result } : {}),
      based_on: { draft_id: base.id, version: base.version },
      edited_before: text !== base.text, // she had edited the text herself first
      // Her answers in her words: a fact / voice signal for later drafts.
      resolved: r.resolved.map((x) => ({ ...x, by: opts.requestedBy ?? null, at: new Date().toISOString() })),
    },
  };
  const ins = await storeDraft(itemId, row, item.status);
  const max = replyLimit(item.platform);
  return {
    draft_id: ins.id, version: ins.version, text: r.text, intent: (base.intent ?? "auto") as Intent, variant: "resolve",
    checks: row.checks, check_spans: spans, sources: base.sources ?? [], length: row.meta.length,
    model: r.model, provider: r.provider, model_reason: choice.reason,
    limit: max ? { unit: "graphemes", max, length: graphemeLength(r.text) } : null, lint: report,
    resolved: r.resolved, based_on: { draft_id: base.id, version: base.version },
  };
}

/**
 * Read-only: 2–3 points she could make, each taken from what she already
 * said (her comment in this thread, earlier messages to this person, her
 * published work). The app shows them when she taps Redraft (draft/points.ts).
 */
export async function draftPoints(itemId: string, opts: { founderId: string; requestedBy?: string | null }): Promise<{ points: Point[]; model: string | null }> {
  const db = admin();
  const { data: item, error } = await db.from("items").select("id, project_id, text, my_post, assigned_to").eq("id", itemId).maybeSingle();
  if (error) throw error;
  if (!item) throw new HttpError(404, "not_found", "No such item.");
  tagUsage({ project_id: item.project_id, item_id: itemId });
  const { req } = await loadDraftRequest(db, itemId, opts.founderId, {});
  req.knowledge = await knowledgeFor(item.project_id, [item.my_post?.title, item.text].filter(Boolean).join("\n\n"));
  const choice = await modelForUser(modelFounderFor({ requestedBy: opts.requestedBy, assignedTo: item.assigned_to, owner: opts.founderId }));
  const { data: project } = await db.from("projects").select("settings").eq("id", item.project_id).single();
  return await suggestPoints(req, draftProvider(choice.spec, project?.settings?.resolve_effort ?? "low", "points"));
}
