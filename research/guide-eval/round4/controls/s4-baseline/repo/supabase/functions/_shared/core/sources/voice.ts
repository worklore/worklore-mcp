// Voice samples: which of the founder's own messages show how she writes.
// Platform-free. A candidate (OwnWriting from any connector, a reply she
// posted through Hearback, a paragraph from her GitHub folder) goes through:
//   1. rules (no model): empty, emoji-only, bare thanks, too short, mostly
//      code / quotes / links → rejected with reason 'rule: …';
//   2. the Decider (TypeSafe Jev, Gemini fallback): "is this a meaningful
//      sample of her voice?" + a 0–4 quality score → accepted above threshold;
//   3. selectActive: the best ACTIVE_CAP accepted samples, diverse by length,
//      platform and recency, near-duplicates skipped. Drafts draw only from these.

import type { Decider, Decision, Questions } from "../../draft/decide/decider.ts";
import { terms, words } from "../../draft/text.ts";
import { isEmojiOnly } from "../../draft/triage.ts";

export const ACTIVE_CAP = 30;
/** P(meaningful) needed to accept. */
export const MEANINGFUL_P = 0.5;
/** Expected quality level (0–4) needed to accept. */
export const QUALITY_MIN = 1.5;
/** Below this many accepted samples the app asks her to help (docs/API.md › source_summary). */
export const FEW_SAMPLES = 8;
const MIN_WORDS = 8;

export const normalizeText = (s: string) => s.trim().replace(/\s+/g, " ");

export async function textSha(s: string): Promise<string> {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalizeText(s)));
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const THANKS = /^(?:many |big |huge )?(?:thanks?(?: you)?(?: so much| a lot)?|thx|ty|cheers|great (?:post|article|read|write-?up|work|job|point)|nice(?: one| post| article)?|awesome|cool|love (?:it|this)|congrats|congratulations|well done|agreed|same here|this|\+1|so true|exactly)\b[\s\S]{0,40}$/i;

/** Pure. Why a candidate is not a voice sample without asking a model, or null. */
export function ruleReject(raw: string): string | null {
  const text = raw.trim();
  if (!text) return "empty";
  if (isEmojiOnly(text)) return "emoji_only";
  const n = words(text);
  if (n < MIN_WORDS && THANKS.test(text.replace(/[!.\p{Extended_Pictographic}\s]+$/u, ""))) return "bare_thanks";
  if (n < MIN_WORDS) return "too_short";
  const lines = text.split("\n").filter((l) => l.trim());
  let inFence = false, code = 0, quote = 0;
  for (const l of lines) {
    if (/^\s*```/.test(l)) { inFence = !inFence; code++; continue; }
    if (inFence || /^( {4}|\t)/.test(l)) code++;
    else if (/^\s*>/.test(l)) quote++;
  }
  if (lines.length && code / lines.length > 0.6) return "mostly_code";
  if (lines.length && quote / lines.length > 0.6) return "mostly_quote";
  const prose = text.replace(/https?:\/\/\S+/g, "").replace(/\s+/g, " ").trim();
  if (words(prose) < MIN_WORDS) return "mostly_links";
  return null;
}

export function voiceQuestions(): Questions {
  return {
    meaningful: {
      type: "boolean",
      instructions: "Is this a meaningful sample of how this person writes in her own words, worth imitating when drafting her future replies?",
      criteria: {
        true: "Her own prose: at least one full sentence she wrote herself, with her own point, experience, tone or reasoning (a reply, an opinion, an explanation, a question back).",
        false: "Not her prose, or too empty to show a voice: emoji or bare thanks, mostly a quote of someone else, a code or log dump, a bare link or list of links, a template or auto-generated text.",
      },
    },
    quality: {
      type: "score",
      instructions: "How well does this show her personal writing voice?",
      criteria: [
        "no voice at all",
        "short and generic: anyone could have written it",
        "a plain, real message with some content",
        "substantive: her own point or experience, clearly in her words",
        "distinctive: shows how she argues, explains or jokes; a great example to imitate",
      ],
    },
  };
}

export interface Candidate {
  text: string;
  context?: string | null;
  platform: string;
}

export interface Verdict {
  status: "accepted" | "rejected";
  reason: string;
  quality: number | null;
  scores: Record<string, unknown> | null;
}

/** Pure. The decider's answers → accepted / rejected. */
export function verdictFrom(d: Pick<Decision, "answers" | "decider" | "model">): Verdict {
  const m = d.answers.meaningful, q = d.answers.quality;
  const pMeaningful = Number(m?.probabilities?.true ?? (m?.answer === true ? 1 : 0));
  const quality = Math.round(Number(q?.answer ?? 0) * 100) / 100;
  const scores = { p_meaningful: pMeaningful, quality, decider: d.decider, model: d.model };
  if (pMeaningful < MEANINGFUL_P) return { status: "rejected", reason: `decider: not a meaningful sample (p=${pMeaningful.toFixed(2)})`, quality, scores };
  if (quality < QUALITY_MIN) return { status: "rejected", reason: `decider: quality ${quality} < ${QUALITY_MIN}`, quality, scores };
  return { status: "accepted", reason: `decider: meaningful (p=${pMeaningful.toFixed(2)}), quality ${quality}`, quality, scores };
}

/** Rules first; the decider only for what the rules let through. */
export async function judgeCandidate(decider: Decider, c: Candidate): Promise<Verdict> {
  const rule = ruleReject(c.text);
  if (rule) return { status: "rejected", reason: `rule: ${rule}`, quality: 0, scores: null };
  const state = [
    `Platform: ${c.platform}`,
    c.context ? `What it answered (or where it sits):\n${c.context.slice(0, 600)}` : "",
    `What she wrote:\n${c.text.slice(0, 3000)}`,
  ].filter(Boolean).join("\n\n");
  return verdictFrom(await decider.decide(state, voiceQuestions()));
}

export interface AcceptedSample {
  id: string;
  text: string;
  platform: string;
  source: string;
  quality: number | null;
  posted_at: string | null;
}

/**
 * Pure. The active set: at most `cap` accepted samples, best first, diverse:
 * no length band (short < 40 words, medium, long > 120) over half the set,
 * no platform over 70% while others exist, near-duplicates skipped. A reply
 * she posted through Hearback and recent writing get a bonus.
 */
export function selectActive(accepted: AcceptedSample[], cap = ACTIVE_CAP, now = new Date()): string[] {
  const score = (s: AcceptedSample) => {
    const ageDays = s.posted_at ? (now.getTime() - new Date(s.posted_at).getTime()) / 86_400_000 : 365;
    return (s.quality ?? 2) + (s.source === "hearback" ? 1 : 0) + Math.max(0, 0.5 * (1 - ageDays / 365));
  };
  const band = (s: AcceptedSample) => { const n = words(s.text); return n < 40 ? "short" : n > 120 ? "long" : "medium"; };
  const ranked = [...accepted].sort((a, b) => score(b) - score(a) || (b.posted_at ?? "").localeCompare(a.posted_at ?? ""));
  const platforms = new Set(accepted.map((s) => s.platform)).size;
  const bandMax = Math.ceil(cap / 2), platformMax = platforms > 1 ? Math.ceil(cap * 0.7) : cap;
  const chosen: AcceptedSample[] = [];
  const termSets = new Map<string, Set<string>>();
  const ts = (s: AcceptedSample) => termSets.get(s.id) ?? termSets.set(s.id, new Set(terms(s.text))).get(s.id)!;
  const dup = (s: AcceptedSample) => chosen.some((c) => {
    const a = ts(s), b = ts(c);
    const inter = [...a].filter((t) => b.has(t)).length;
    return inter / Math.max(1, Math.min(a.size, b.size)) > 0.8;
  });
  const count = (f: (s: AcceptedSample) => string, v: string) => chosen.filter((c) => f(c) === v).length;
  for (const strict of [true, false]) {
    for (const s of ranked) {
      if (chosen.length >= cap) break;
      if (chosen.includes(s) || dup(s)) continue;
      if (strict && (count(band, band(s)) >= bandMax || count((x) => x.platform, s.platform) >= platformMax)) continue;
      chosen.push(s);
    }
  }
  return chosen.map((s) => s.id);
}
