// Triage: before anything is drafted, decide what the founder has to DO with
// an incoming item. Decision 2026-10-08 (Yahhi/hearback#5): feedback on her own
// product is not drafted at all. It goes to a "Decide" queue with a one-line
// summary and a suggested action, and the reply is written later from what she
// actually did (eval/REPORT.md: in 8 of 12 real replies the substance was an
// action she took after the comment, which no draft can know).
//
//   (a) feedback_for_founder  request / bug / idea / critique of HER product → Decide queue, no draft
//   (b) engagement            discussion, curiosity, opinion (often on others' posts) → draft
//   (c) product_question      a question her published work answers → draft with sources
//   (d) thanks                thanks / short reaction → one-line draft, or skip
//   The decider's action is respected (2026-10-09): "skip" → no draft (Done ›
//   No reply needed), "short_draft" → one line, only "draft" → a full draft.
//   (-) ignore                spam, off-topic, bots → skip
//
// The decision is a set of typed questions asked of a Decider (decide/decider.ts),
// so the model behind it is swappable: an LLM today (LlmDecider), TypeSafe's
// "Jev" decision model later. Probabilities and confidence are kept in the
// result; below CONFIDENCE_FLOOR the app shows the item as "not sure".
//
// A second question set decides about a found ARTICLE (not a comment): is it
// relevant to the project's aims, and should she comment, flag it, or leave it.

import { Answer, Decider, Decision, Questions } from "./decide/decider.ts";
import type { Provider } from "./providers/provider.ts";
import { truncateToTokens } from "./text.ts";
import type { ItemContext, ItemKind, ProjectProfile } from "./types.ts";

export type TriageKind = "feedback_for_founder" | "engagement" | "product_question" | "thanks" | "ignore";
/** spam_check: looks like a plug (spamSignals / the promotion question); no draft until she says hide or not spam. */
export type TriageRoute = "decide_queue" | "draft" | "short_draft" | "skip" | "spam_check";
export type SuggestedAction = "act" | "open_issue" | "not_now" | "just_thank";

/** Below this, the app labels the triage "not sure" and lets her re-sort it. */
export const CONFIDENCE_FLOOR = 0.6;
/** When the kind is not sure and feedback is at least this likely, route to Decide anyway: a missed draft costs less than a draft that invents what she did. */
export const FEEDBACK_SAFETY_P = 0.3;

export const KIND_CODE: Record<TriageKind, "a" | "b" | "c" | "d" | "-"> = {
  feedback_for_founder: "a", engagement: "b", product_question: "c", thanks: "d", ignore: "-",
};
/** Triage kind → the draft engine's item_kind (prompt v4 shapes the draft by it). */
export const DRAFT_KIND: Record<TriageKind, ItemKind | null> = {
  feedback_for_founder: "feedback", engagement: "engagement", product_question: "question", thanks: "reaction", ignore: null,
};

export interface TriageResult {
  kind: TriageKind;
  code: "a" | "b" | "c" | "d" | "-";
  route: TriageRoute;
  /** Confidence in `kind` is below CONFIDENCE_FLOOR. */
  not_sure: boolean;
  /** One line. Feedback: what they ask her to change or build. Otherwise: what the message is about. */
  summary: string;
  /** Feedback only. */
  suggested_action: SuggestedAction | null;
  /** Confidence in `kind` (0–1). */
  confidence: number;
  /** They show they have the problem the project solves (doing it by hand, a workaround, asking for a tool): the app suggests "Invite to try". Absent on older rows. */
  has_the_problem?: boolean;
  /** Their own words for that problem (LLM decider only), null when none. */
  pain_quote?: string | null;
  /** Looks like a plug for someone else's product or site: the app offers "Hide as spam". */
  spam?: { suspected: boolean; signals: string[]; p_promotion: number | null };
  probabilities: {
    kind: Record<string, number>; action: Record<string, number>; suggested_action?: Record<string, number>; has_the_problem?: Record<string, number>;
    promotion?: Record<string, number>;
  };
  /** What the decider answered for `action` before policy (feedback → decide_queue) was applied. */
  decider_action: TriageRoute;
  /** Set when policy changed the decider's action. */
  policy?: string;
  decider: string;
  model: string;
  usage: Decision["usage"];
  latency_ms: number;
}

export interface TriageInput {
  project: Pick<ProjectProfile, "name" | "one_liner" | "founder_name" | "founder_handle">;
  context: ItemContext;
}

// ------------------------------------------------------------------ comments
export function commentQuestions(project: TriageInput["project"]): Questions {
  const p = project.name;
  return {
    kind: {
      type: "choice",
      instructions: `What kind of message is this, from the point of view of ${project.founder_name ?? "the founder"} (founder of ${p})? Unclear cases: if it asks her or ${p} to change, add, fix, adopt, publish, try or build something, or proposes a concrete fix for a problem in ${p} that the thread discussed (even phrased as "what I'd do in mine"), it is feedback_for_founder, even when wrapped in thanks. A suggestion aimed only at the writer's own project is engagement. Thanks plus a substantive new point: judge by the point.`,
      criteria: {
        feedback_for_founder: `about HER product or her own code/setup: a feature request, bug report, idea or fix she could adopt, a critique of how it works, a request to change/adopt/check something. She must decide or act before replying.`,
        engagement: `discussion, curiosity, opinion, shared experience or debate about the topic, including someone else's post she might comment on; nothing asked of ${p}.`,
        product_question: `a direct factual question about ${p} or her published work (how does X work, does it support Y, where is Z) that her docs/articles/stories could answer.`,
        thanks: `thanks, praise, "+1", a short reaction with nothing to decide or discuss.`,
        ignore: `spam, bots, off-topic, or a message whose real purpose is a plug for someone else's product or site, even when the rest is on-topic (generic tips ending in "found it via X", a link or a domain written with spaces).`,
      },
    },
    action: {
      type: "choice",
      instructions: "What should happen with it next?",
      criteria: {
        decide_queue: "she has to decide or do something first (feedback on her product); no reply draft yet",
        draft: "draft a reply now",
        short_draft: "a one-to-three-sentence reply is enough",
        skip: "no reply needed",
      },
    },
    suggested_action: {
      type: "choice",
      instructions: "If it is feedback on her product: what should she do with it? (If not feedback, answer just_thank.)",
      criteria: {
        act: "small, clearly right, in line with what she's doing; she could just do it",
        open_issue: "worth doing but bigger or needs thought; track it",
        not_now: "out of scope or against the product's direction",
        just_thank: "already done or decided, or not feedback; acknowledgement is enough",
      },
    },
    promotion: {
      type: "boolean",
      instructions: `Does the message advertise a product, service or site that is not ${p} or ${project.founder_name ?? "the founder"}'s own work, even if the rest is on-topic?`,
      criteria: {
        true: `it names or links someone else's product or site as a recommendation or source ("found it via X", "check out X", "site: x .tech", a domain written with spaces to dodge link filters), often after generic, could-fit-any-post tips`,
        false: `no product or site is pushed; a tool mentioned only as part of their own experience, with no link or call to visit it, is not promotion`,
      },
    },
    has_the_problem: {
      type: "boolean",
      instructions: `Does the writer of the message show that they have, in their own work, the problem ${p} solves${project.one_liner ? ` (${p}: ${project.one_liner})` : ""}?`,
      criteria: {
        true: `they describe that problem as their own: doing it by hand, losing time or money on it, a workaround they built, or they ask whether a tool for it exists`,
        false: `they only discuss the topic, praise, ask about ${p}, or the problem they describe is a different one`,
      },
    },
  };
}

/** The state a decider sees for a comment: where it is, the two messages above it, the message. */
export function commentState(input: TriageInput): string {
  const p = input.project, ctx = input.context;
  const who = p.founder_name ?? "the founder";
  const lines: string[] = [`Founder: ${who}${p.founder_handle ? ` (@${p.founder_handle})` : ""}, building ${p.name}${p.one_liner ? `: ${p.one_liner}` : ""}.`];
  if (ctx.post) {
    lines.push(`Where: ${ctx.platform}, under ${ctx.post.is_owner ? "HER OWN post" : `a post by @${ctx.post.author ?? "someone"} (not hers)`}: "${ctx.post.title ?? ""}"`);
    if (ctx.post.text) lines.push(`Post opening:\n${truncateToTokens(ctx.post.text, 350)}`);
  }
  if (ctx.chain.length > 2) lines.push(`[${ctx.chain.length - 2} earlier message(s) omitted]`);
  for (const m of ctx.chain.slice(-2)) lines.push(`@${m.author}${m.is_owner ? ` (${who})` : ""}:\n${truncateToTokens(m.text, 500)}`);
  lines.push(`MESSAGE TO SORT, by @${ctx.item.author}:\n${truncateToTokens(ctx.item.text, 1200)}`);
  return lines.join("\n\n---\n\n");
}

const NOTES = {
  summary: "one line, max 20 words. If it is feedback: what exactly they ask her to change or build. Otherwise: what the message is about.",
  pain: "only if they show they have the problem the project solves: their own words for it, copied exactly, at most 12 words. Otherwise an empty string.",
};

/** Domain-like words a plug spells with a space so the site won't link it ("labagent .tech"). */
const SPACED_DOMAIN = /\b[a-z0-9][a-z0-9-]{1,40}\s+\.\s*(?:com|io|ai|tech|dev|app|net|org|co|xyz|site|online|store|shop|pro|me|cc|so|sh|gg|tools?|vn|ru)\b/i;

/**
 * Pure: plain-text signs of a plug, checked before any model (Jev judged an
 * on-topic Vietnamese comment ending in "found it via LabAgent, site:
 * labagent .tech" as engagement 0.97). Each entry is a short reason the app
 * shows. Exported for tests.
 */
export function spamSignals(text: string): string[] {
  const out: string[] = [];
  const domain = text.match(SPACED_DOMAIN);
  if (domain) out.push(`a site written with a space to dodge links ("${domain[0].replace(/\s+/g, " ")}")`);
  if (/\bsite\s*:\s*\S/i.test(text)) out.push(`a "site:" plug`);
  const tail = text.slice(-240);
  const via = tail.match(/\bfound (?:it|this|them) (?:via|on|through|at|with)\s+([A-Z][\w.-]*)/);
  if (via) out.push(`ends with "found it via ${via[1]}"`);
  return out;
}

/** The model's promotion answer counts from here on. */
export const PROMOTION_P = 0.6;

/** Emoji, punctuation and whitespace only ("😂", "🔥🔥", "+1!"): a reaction, nothing to answer. */
export function isEmojiOnly(text: string): boolean {
  const t = text.replace(/\+1|-1/g, "").replace(/[\s\p{P}\p{S}\p{Extended_Pictographic}\u200d\ufe0f]/gu, "");
  return t.length === 0;
}

/**
 * Pure: the routing policy (docs/ARCHITECTURE.md › Triage). Feedback goes to
 * Decide; otherwise the decider's action is respected: "skip" means no reply
 * (no draft), "short_draft" means a one-line draft, and only "draft" gets a
 * full draft. Emoji-only reactions and bare thanks are never drafted.
 */
export function routeFor(kind: TriageKind, deciderAction: TriageRoute, notSure: boolean, pFeedback: number, text: string, spamSuspected = false):
  { route: TriageRoute; policy?: string } {
  if (isEmojiOnly(text)) return { route: "skip", policy: "emoji-only reaction: no reply needed" };
  // Her call, not ours: hide it as spam or treat it as a comment. No draft meanwhile.
  if (spamSuspected) return { route: "spam_check", policy: "looks like a plug: she decides (hide as spam / not spam)" };
  if (kind === "feedback_for_founder") return { route: "decide_queue" };
  if (notSure && pFeedback >= FEEDBACK_SAFETY_P) return { route: "decide_queue", policy: `not sure, P(feedback)=${pFeedback}: Decide queue instead of a draft` };
  if (kind === "ignore") return { route: "skip" };
  if (deciderAction === "skip") return { route: "skip", policy: `decider said skip (${kind}): no reply needed` };
  if (kind === "thanks") {
    if (words(text) < 6 && !text.includes("?")) return { route: "skip", policy: "bare thanks: no reply needed" };
    return { route: "short_draft" };
  }
  if (deciderAction === "short_draft") return { route: "short_draft" };
  return { route: "draft" };
}

/** Pure: decider answers → TriageResult, with the routing policy applied. Exported for tests. */
export function triageFromDecision(d: Decision, item: ItemContext["item"]): TriageResult {
  const k = d.answers.kind as Answer, a = d.answers.action as Answer, s = d.answers.suggested_action as Answer | undefined;
  const hp = d.answers.has_the_problem as Answer | undefined;
  // Their pain is an opening only in a conversation; feedback, thanks and spam aren't invitations.
  const hasProblem = hp ? hp.answer === true && (isConversation(k.answer as TriageKind)) : undefined;
  const kind = k.answer as TriageKind;
  const deciderAction = a.answer as TriageRoute;
  const notSure = k.confidence < CONFIDENCE_FLOOR;
  const pFeedback = k.probabilities.feedback_for_founder ?? 0;
  const pr = d.answers.promotion as Answer | undefined;
  const signals = spamSignals(item.text);
  const pPromo = pr ? pr.probabilities.true ?? (pr.answer === true ? 1 : 0) : null;
  const suspected = signals.length > 0 || (pPromo ?? 0) >= PROMOTION_P || kind === "ignore" && (pPromo ?? 0) >= 0.4;
  const r = routeFor(kind, deciderAction, notSure, pFeedback, item.text, suspected);
  const route = r.route;
  let policy = r.policy;
  if (!policy && route !== deciderAction) policy = `policy for ${kind}: ${route} (decider said ${deciderAction})`;
  const suggested = kind === "feedback_for_founder" || route === "decide_queue" ? (s?.answer as SuggestedAction ?? "open_issue") : null;
  return {
    kind, code: KIND_CODE[kind], route, not_sure: notSure,
    summary: d.notes?.summary ?? firstSentence(item.text),
    suggested_action: suggested,
    confidence: k.confidence,
    ...(hasProblem === undefined ? {} : { has_the_problem: hasProblem, pain_quote: hasProblem ? painQuote(d.notes?.pain, item.text) : null }),
    spam: { suspected, signals: suspected && !signals.length ? ["the decider reads it as a plug for another product"] : signals, p_promotion: pPromo },
    probabilities: {
      kind: k.probabilities, action: a.probabilities,
      ...(s ? { suggested_action: s.probabilities } : {}), ...(hp ? { has_the_problem: hp.probabilities } : {}),
      ...(pr ? { promotion: pr.probabilities } : {}),
    },
    decider_action: deciderAction, ...(policy ? { policy } : {}),
    decider: d.decider, model: d.model, usage: d.usage, latency_ms: d.latency_ms,
  };
}

function isConversation(kind: TriageKind) {
  return kind === "engagement" || kind === "product_question";
}

/** The decider's quote, kept only when it really is their words (a quote it paraphrased is dropped). Exported for tests. */
export function painQuote(note: string | undefined, text: string): string | null {
  const q = (note ?? "").trim().replace(/^["'“]|["'”]$/g, "").trim();
  if (!q) return null;
  const norm = (t: string) => t.toLowerCase().replace(/\s+/g, " ");
  return norm(text).includes(norm(q)) ? q : null;
}

/**
 * summarizer: a text model for the Decide queue's one-line summary when the
 * decider writes no notes (TypeSafe answers typed questions only). Called only
 * for items routed to the Decide queue; without it the summary is the first sentence.
 */
export async function triageItem(input: TriageInput, decider: Decider, opts: { summarizer?: Provider } = {}): Promise<TriageResult> {
  const d = await decider.decide(commentState(input), commentQuestions(input.project), { notes: NOTES });
  const r = triageFromDecision(d, input.context.item);
  if (!d.notes?.summary && opts.summarizer && r.route === "decide_queue") {
    const out = await opts.summarizer.generate({
      system: "You write one-line summaries for a founder's to-do queue. Output only the line.",
      prompt: `${commentState(input)}\n\nIn at most 20 words: what exactly does @${input.context.item.author} ask ${input.project.founder_name ?? "the founder"} to change, build or check in ${input.project.name}?`,
      temperature: 0, max_output_tokens: 80,
    });
    r.summary = out.text.trim().replace(/^["']|["']$/g, "");
  }
  return r;
}

// ------------------------------------------------------------------ articles
export type ArticleAction = "comment_to_engage" | "flag_for_founder" | "leave";

export interface ArticleInput {
  project: Pick<ProjectProfile, "name" | "one_liner" | "audience" | "aims" | "founder_name">;
  article: { title: string; url?: string; author: string; tags?: string[]; text: string; published_at?: string; comments_count?: number };
}

export interface ArticleDecisionResult {
  relevant: boolean;
  p_relevant: number;
  action: ArticleAction;
  not_sure: boolean;
  confidence: number;
  probabilities: { action: Record<string, number> };
  why: string;
  decider: string;
  model: string;
  usage: Decision["usage"];
  latency_ms: number;
}

export function articleQuestions(project: ArticleInput["project"]): Questions {
  return {
    relevant_to_project_aims: {
      type: "boolean",
      instructions: `Is this article relevant to what ${project.name} is trying to do? Aims: ${project.aims ?? project.one_liner ?? project.name}. Audience: ${project.audience ?? "-"}.`,
      criteria: {
        true: `its readers or author are people ${project.name} is for, AND its topic touches what ${project.founder_name ?? "the founder"} works on, so a comment from her would be on-topic, not a plug`,
        false: `a different audience or a topic she has nothing to add to`,
      },
    },
    action: {
      type: "choice",
      instructions: "What should she do with it?",
      criteria: {
        comment_to_engage: "she has real experience or published work on exactly this, and a comment would add something concrete to the discussion",
        flag_for_founder: "relevant, but the move isn't a comment: a competitor, a possible collaborator or user, a claim about her area she should know about, or something she'd want to read first",
        leave: "not relevant enough, or nothing she could add",
      },
    },
  };
}

export function articleState(input: ArticleInput): string {
  const a = input.article, p = input.project;
  return [
    `Founder: ${p.founder_name ?? "the founder"}, building ${p.name}${p.one_liner ? `: ${p.one_liner}` : ""}.`,
    `ARTICLE: "${a.title}" by @${a.author}${a.published_at ? `, ${a.published_at.slice(0, 10)}` : ""}${a.tags?.length ? `, tags: ${a.tags.join(", ")}` : ""}${a.comments_count !== undefined ? `, ${a.comments_count} comments` : ""}`,
    truncateToTokens(a.text, 900),
  ].join("\n\n");
}

export async function decideArticle(input: ArticleInput, decider: Decider): Promise<ArticleDecisionResult> {
  const d = await decider.decide(articleState(input), articleQuestions(input.project), { notes: { why: "one sentence: why this action" } });
  const r = d.answers.relevant_to_project_aims, act = d.answers.action;
  return {
    relevant: r.answer as boolean, p_relevant: r.probabilities.true,
    action: act.answer as ArticleAction,
    not_sure: Math.min(r.confidence, act.confidence) < CONFIDENCE_FLOOR,
    confidence: act.confidence,
    probabilities: { action: act.probabilities },
    why: d.notes?.why ?? "",
    decider: d.decider, model: d.model, usage: d.usage, latency_ms: d.latency_ms,
  };
}

// ------------------------------------------------------------------ helpers
function words(s: string) { return (s.trim().match(/\S+/g) ?? []).length; }
function firstSentence(s: string) {
  const t = s.replace(/\s+/g, " ").trim();
  const m = t.match(/^.{10,160}?[.!?](\s|$)/);
  return m ? m[0].trim() : t.length <= 140 ? t : t.slice(0, 140).replace(/\s+\S*$/, "") + "…";
}
