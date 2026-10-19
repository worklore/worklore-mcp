// Resolving [check: …] gaps: she answers a check ("Answer") or drops it
// ("Drop this part"). The draft is edited ONLY where the gap is:
//
// - the edit unit is the paragraph that holds the gap; every other paragraph is
//   copied byte for byte, so the rest of the draft can't drift;
// - the model rewrites that paragraph to work her answer in (her words, her
//   voice, nothing beyond what she said, proofread: grammar and repeated
//   words fixed with the smallest change), or to remove the gap and whatever
//   depends on it;
// - the result is checked: the resolved marker is gone, the other gaps are
//   kept verbatim, the answer is really in it, and the word diff stays inside
//   a small budget (no new claims). The fact guard runs on the new paragraph;
// - if the model fails or breaks a rule twice, a deterministic edit does it
//   (the answer goes in place of the marker; a drop removes the gap's
//   sentence). Never a 502 for something this small.
//
// Storage-free like engine.ts: core/draft_run.ts loads, calls, stores.

import { CheckSpan, parseChecks } from "./checks.ts";
import { guardFacts } from "./guard.ts";
import { cleanDraft } from "./lint.ts";
import type { Provider } from "./providers/provider.ts";
import { terms } from "./text.ts";

export interface Resolution {
  check_id: string;
  /** Her answer. Required unless drop. */
  answer?: string | null;
  drop?: boolean;
}

export interface ResolvedCheck {
  check_id: string;
  question: string;
  action: "answer" | "drop";
  answer?: string;
  /** "model": rewritten by the model; "fallback": the deterministic edit. */
  method: "model" | "fallback";
  /** Why the model's edit was not used (fallback only). */
  reason?: string;
}

export interface ResolveInput {
  /** The draft as it is now (her edits included). Check ids refer to this text. */
  text: string;
  resolutions: Resolution[];
  founder_name?: string | null;
  voice_notes?: string | null;
  /** What she is replying to (for tone only, never a source of new claims). */
  replying_to?: string | null;
  /** guard.ts context: her sources and the thread. Her answers are added to it. */
  fact_context?: string;
}

export interface ResolveResult {
  text: string;
  resolved: ResolvedCheck[];
  /** Numbers/claims the fact guard turned into new gaps in the edited paragraphs. */
  invented: string[];
  provider: string;
  model: string;
  usage: { input: number; output: number; cache_read?: number; cache_write?: number; cost_usd?: number };
  latency_ms: number;
}

export class ResolveError extends Error {
  constructor(readonly code: "unknown_check" | "answer_required" | "duplicate_check", message: string, readonly checkId?: string) {
    super(message);
  }
}

const EMPTY = "<EMPTY>";

// ------------------------------------------------------------------ paragraphs

interface Para { text: string; start: number; end: number; sep: string }

/** Paragraphs with the blank-line separator that follows each. Joining text+sep gives the input back. */
export function paragraphs(text: string): Para[] {
  const out: Para[] = [];
  const re = /\n[ \t]*\n\s*/g;
  let last = 0;
  for (const m of text.matchAll(re)) {
    out.push({ text: text.slice(last, m.index!), start: last, end: m.index!, sep: m[0] });
    last = m.index! + m[0].length;
  }
  out.push({ text: text.slice(last), start: last, end: text.length, sep: "" });
  return out;
}

// ------------------------------------------------------------------ word diff

const tokens = (s: string) => s.toLowerCase().replace(/\[check:[^\]]*\]/gi, " ").match(/[\p{L}\p{N}]+(?:['’][\p{L}]+)?/gu) ?? [];

/** Words added and removed between a and b (LCS on lowercase word tokens). */
export function wordDiff(a: string, b: string): { added: string[]; removed: string[] } {
  const x = tokens(a), y = tokens(b);
  const dp: number[][] = Array.from({ length: x.length + 1 }, () => new Array(y.length + 1).fill(0));
  for (let i = x.length - 1; i >= 0; i--) {
    for (let j = y.length - 1; j >= 0; j--) dp[i][j] = x[i] === y[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  }
  const added: string[] = [], removed: string[] = [];
  let i = 0, j = 0;
  while (i < x.length && j < y.length) {
    if (x[i] === y[j]) { i++; j++; } else if (dp[i + 1][j] >= dp[i][j + 1]) removed.push(x[i++]); else added.push(y[j++]);
  }
  while (i < x.length) removed.push(x[i++]);
  while (j < y.length) added.push(y[j++]);
  return { added, removed };
}

// ------------------------------------------------------------------ checking an edit

/** Small words that any smoothing may add ("and", "so", "I"). They don't count as new content. */
const GLUE = new Set(("a an the and or but so yet also too then that this these those it its i i'm i've my me we our you your " +
  "is are was were be been do does did have has had not no of to in on at for with by from as about which who what how why " +
  "when where there here just still even only both either because since while one ones").split(" "));

export interface EditCheck { ok: boolean; reason?: string }

/**
 * Is `after` an acceptable edit of the paragraph `before` for these checks?
 * `keep` are the markers in the paragraph that are NOT being resolved.
 */
export function checkEdit(before: string, after: string, targets: { span: CheckSpan; r: Resolution }[], keep: CheckSpan[]): EditCheck {
  for (const { span } of targets) if (after.includes(span.marker)) return { ok: false, reason: `${span.id} is still there` };
  for (const k of keep) if (!after.includes(k.marker)) return { ok: false, reason: `the other gap ${k.id} was changed` };
  const traces = (after.match(/\[check/gi) ?? []).length;
  if (traces !== keep.length) return { ok: false, reason: "a new [check] appeared" };
  const answers = targets.filter((t) => !t.r.drop).map((t) => t.r.answer!.trim());
  if (!after.trim() && answers.length) return { ok: false, reason: "the answer was dropped" };
  // Her answer is really in it: most of its content words appear.
  for (const a of answers) {
    const want = [...new Set(terms(a))];
    if (!want.length) continue;
    const have = new Set(terms(after));
    const hit = want.filter((t) => have.has(t)).length;
    if (hit / want.length < 0.6) return { ok: false, reason: "the answer is not in the text" };
  }
  // Diff budget. New words must come from her answer (or be glue); removed
  // words are limited when answering (a drop may remove the sentences that
  // depended on the gap, so removals are free there).
  const { added, removed } = wordDiff(before, after);
  const answerWords = new Set(answers.flatMap((a) => tokens(a)));
  const novel = added.filter((w) => !answerWords.has(w) && !GLUE.has(w));
  const base = tokens(before).length;
  // Proofreading her answer replaces some of its words: the budget grows
  // with the answer, not only with the paragraph.
  const answerLen = answers.reduce((n, a) => n + tokens(a).length, 0);
  const novelBudget = answers.length ? 4 + Math.ceil(base * 0.1) + Math.ceil(answerLen * 0.25) : 3;
  if (novel.length > novelBudget) return { ok: false, reason: `too many new words (${novel.slice(0, 8).join(", ")})` };
  if (answers.length && targets.every((t) => !t.r.drop)) {
    const removeBudget = 4 + Math.ceil(base * 0.15);
    if (removed.length > removeBudget) return { ok: false, reason: `too much of the text was rewritten (${removed.length} words removed)` };
  }
  return { ok: true };
}

// ------------------------------------------------------------------ deterministic edit

const SENT_END = /(?<=[.!?…])\s+/;

/** The answer as a sentence of its own: capitalised, with an end mark. */
function asSentence(a: string): string {
  const t = a.trim().replace(/\s+/g, " ");
  const s = t.charAt(0).toUpperCase() + t.slice(1);
  return /[.!?…)"”]$/.test(s) ? s : `${s}.`;
}

/**
 * The fallback: the answer replaces the marker (as its own sentence when the
 * marker was one, inline otherwise); a drop removes the sentence holding the
 * marker (the marker alone when it was a sentence of its own).
 */
export function editByRule(paragraph: string, offset: number, targets: { span: CheckSpan; r: Resolution }[]): string {
  // Right to left, so earlier offsets stay valid.
  let p = paragraph;
  for (const { span, r } of [...targets].sort((a, b) => b.span.start - a.span.start)) {
    const s = span.start - offset, e = span.end - offset;
    const before = p.slice(0, s), after = p.slice(e);
    const alone = /(^|[.!?…:]\s*|\n\s*)$/.test(before) && /^\s*($|\n|[A-Z\p{Lu}])/u.test(after);
    if (!r.drop) {
      const a = r.answer!.trim();
      p = alone ? before + asSentence(a) + after : before + a.replace(/[.!?]+$/, "") + after;
      continue;
    }
    if (alone) { p = (before.replace(/\s+$/, "") + (after.trim() ? " " + after.replace(/^\s+/, "") : "")).trim(); continue; }
    // The marker is inside a sentence: that sentence goes. Markers are masked so
    // the "?" and "." inside them don't split sentences.
    const masked = p.slice(0, s) + "\u0000".repeat(e - s) + p.slice(e);
    const parts = masked.split(SENT_END);
    let pos = 0;
    const keep: string[] = [];
    for (const part of parts) {
      const at = masked.indexOf(part, pos);
      const end = at + part.length;
      pos = end;
      if (!(at <= s && end >= e)) keep.push(p.slice(at, end));
    }
    p = keep.join(" ");
  }
  return p.replace(/[ \t]{2,}/g, " ").replace(/\s+([,.;:!?])/g, "$1").trim();
}

// ------------------------------------------------------------------ the model's edit

export const RESOLVE_SYSTEM = (name: string) => `You make one small edit to a reply draft that ${name} wrote. The draft has gaps marked [check: …]: questions only she can answer. She has now answered some gaps (or asked to drop them). You get ONE paragraph of the draft and rewrite only that paragraph.

Rules:
1. Minimal edit. Change only what the gap needs. Every other sentence of the paragraph stays word for word.
2. "Answer": put her answer in place of the gap, in her voice (first person, her wording). Make it read naturally with the sentences around it. Say nothing beyond her answer: no new facts, numbers, names, examples, results or opinions.
3. Proofread her answer as you put it in: she often writes in a second language and types fast. Fix grammar, articles, prepositions, tense, word order and awkward phrasing; remove words she repeats (the same word twice in a sentence or two, "really … really") and anything that repeats what the paragraph or draft already says. Use the smallest change that makes it correct and natural English; keep her meaning, her points, her tone and as many of her words as fit. Do not polish it into a different voice.
4. "Drop": remove the gap and any words or sentence that only make sense with it, then smooth the joint. Add nothing new.
5. Gaps that are not being resolved stay exactly as they are, character for character.
6. Same language as the draft. Plain text. No quotes around the output, no comments.
7. Output only the rewritten paragraph. If nothing of the paragraph is left (a dropped gap was the whole paragraph), output exactly ${EMPTY}.`;

function resolvePrompt(input: ResolveInput, para: string, targets: { span: CheckSpan; r: Resolution }[], strict: boolean): string {
  const tasks = targets.map(({ span, r }) =>
    r.drop
      ? `- ${span.marker}\n  → Drop: remove this gap and whatever depends on it.`
      : `- ${span.marker}\n  → Answer. Her answer, in her words: """${r.answer!.trim()}"""`
  ).join("\n");
  return [
    input.replying_to ? `## What she is replying to (context only)\n${input.replying_to.slice(0, 1500)}` : null,
    input.voice_notes ? `## How she writes\n${input.voice_notes}` : null,
    `## The whole draft (context only; do not output it)\n${input.text}`,
    `## The paragraph to edit\n${para}`,
    `## What to do\n${tasks}`,
    strict ? "Your last edit changed too much or lost her answer. This time keep every other word of the paragraph and her answer's own words, changing only what grammar needs." : null,
    "Output only the edited paragraph.",
  ].filter(Boolean).join("\n\n");
}

// ------------------------------------------------------------------ resolveChecks

export async function resolveChecks(input: ResolveInput, provider: Provider | null): Promise<ResolveResult> {
  const spans = parseChecks(input.text);
  const byId = new Map(spans.map((s) => [s.id, s]));
  const seen = new Set<string>();
  const targets: { span: CheckSpan; r: Resolution }[] = [];
  for (const r of input.resolutions) {
    const span = byId.get(r.check_id);
    if (!span) throw new ResolveError("unknown_check", `No check ${r.check_id} in this draft.`, r.check_id);
    if (seen.has(r.check_id)) throw new ResolveError("duplicate_check", `${r.check_id} is resolved twice.`, r.check_id);
    seen.add(r.check_id);
    if (!r.drop && !r.answer?.trim()) throw new ResolveError("answer_required", `Answer ${r.check_id}, or drop it.`, r.check_id);
    targets.push({ span, r });
  }

  const paras = paragraphs(input.text);
  const usage = { input: 0, output: 0, cache_read: 0, cache_write: 0, cost_usd: 0 };
  let latency = 0, usedModel: string | null = null, usedProvider: string | null = null;
  const resolved: ResolvedCheck[] = [];
  const invented: string[] = [];
  const answers = targets.filter((t) => !t.r.drop).map((t) => t.r.answer!.trim());
  const newText: string[] = [];

  for (const p of paras) {
    const here = targets.filter((t) => t.span.start >= p.start && t.span.end <= p.end);
    if (!here.length) { newText.push(p.text); continue; }
    const keep = spans.filter((s) => s.start >= p.start && s.end <= p.end && !here.some((t) => t.span.id === s.id));
    let edited: string | null = null, reason: string | undefined;
    for (let attempt = 0; provider && attempt < 2 && edited === null; attempt++) {
      try {
        const out = await provider.generate({
          system: RESOLVE_SYSTEM(input.founder_name ?? "the founder"),
          prompt: resolvePrompt(input, p.text, here, attempt > 0),
          temperature: attempt ? 0 : 0.3,
          max_output_tokens: 1024,
        });
        usage.input += out.usage?.input ?? out.tokens_in ?? 0;
        usage.output += out.usage?.output ?? out.tokens_out ?? 0;
        usage.cache_read += out.usage?.cache_read ?? 0;
        usage.cache_write += out.usage?.cache_write ?? 0;
        usage.cost_usd += out.usage?.cost_usd ?? 0;
        latency += out.latency_ms;
        usedModel = out.model;
        usedProvider = out.provider ?? provider.name;
        let candidate = cleanDraft(out.text, input.founder_name);
        if (candidate.trim() === EMPTY) candidate = "";
        const verdict = checkEdit(p.text, candidate, here, keep);
        if (verdict.ok) edited = candidate; else reason = verdict.reason;
      } catch (e) {
        reason = `model failed: ${(e as Error).message.slice(0, 120)}`;
        break;
      }
    }
    const method: "model" | "fallback" = edited === null ? "fallback" : "model";
    if (edited === null) edited = editByRule(p.text, p.start, here);
    // The fact guard on what changed: anything not in her sources, the thread,
    // the paragraph as it was, or her answers becomes a gap again.
    const g = guardFacts(edited, [input.fact_context ?? "", p.text, ...answers].join("\n\n"));
    edited = g.text;
    invented.push(...g.invented);
    for (const { span, r } of here) {
      resolved.push({
        check_id: span.id, question: span.question, action: r.drop ? "drop" : "answer",
        ...(r.drop ? {} : { answer: r.answer!.trim() }), method, ...(method === "fallback" && reason ? { reason } : {}),
      });
    }
    newText.push(edited);
  }

  // Rejoin with the original separators; an emptied paragraph takes its separator with it.
  let text = "", sep = "";
  paras.forEach((p, i) => {
    const t = newText[i];
    if (!t.trim()) return;
    text += (text ? sep || "\n\n" : "") + t;
    sep = p.sep;
  });
  text = text.replace(/\n{3,}/g, "\n\n").trim();
  resolved.sort((a, b) => Number(a.check_id.slice(1)) - Number(b.check_id.slice(1)));
  return {
    text, resolved, invented,
    provider: usedProvider ?? "hearback", model: usedModel ?? "rule",
    usage: { input: usage.input, output: usage.output, cache_read: usage.cache_read, cache_write: usage.cache_write, cost_usd: Math.round(usage.cost_usd * 1e6) / 1e6 },
    latency_ms: latency,
  };
}
