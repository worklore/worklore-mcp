// A Decider answers typed questions about a state with probabilities. Triage
// (triage.ts) is written against this interface only, so the model behind it
// is an adapter:
//   - GeminiDecider (gemini.ts): an LLM asked for per-option probabilities in JSON.
//   - TypeSafeDecider (typesafe.ts): TypeSafe AI's decision model "Jev", POST
//     https://api.typesafe.ai/v1/systemone with {model, state, questions:{id:{type,
//     instructions, criteria}}} → per-option probabilities + confidence. The
//     shapes below mirror that API (their "noul" is our "boolean"), so the
//     adapter is a field-for-field mapping.

export type Question =
  | { type: "choice"; instructions: string; /** option → when it applies */ criteria: Record<string, string> }
  | { type: "boolean"; instructions: string; criteria: { true: string; false: string } }
  | { type: "score"; instructions: string; /** ordered level descriptions; level i scores i */ criteria: string[] };

export type Questions = Record<string, Question>;

export interface Answer {
  /** choice: the option id; boolean: true/false; score: expected level (0 … levels-1, may be fractional). */
  answer: string | boolean | number;
  /** choice: option → p (sums to ~1); boolean: {true: p, false: 1-p}; score: {} */
  probabilities: Record<string, number>;
  /** 0–1. The app shows answers below its threshold as "not sure". */
  confidence: number;
}

export interface Decision {
  answers: Record<string, Answer>;
  /** Free-text notes the adapter could produce on request (e.g. a one-line summary). Optional: Jev returns none. */
  notes?: Record<string, string>;
  decider: string;   // "gemini" / "typesafe"
  model: string;
  usage: { tokens_in: number | null; tokens_out: number | null };
  latency_ms: number;
}

export interface DecideOptions {
  /** note id → instruction, e.g. {summary: "one line: what they ask her to change"}. Adapters that can't write text ignore it. */
  notes?: Record<string, string>;
}

export interface Decider {
  readonly name: string;
  readonly model: string;
  /** state: what the decision is about, as readable text (or a JSON-able object). */
  decide(state: string | Record<string, unknown>, questions: Questions, opts?: DecideOptions): Promise<Decision>;
}

/** Normalise raw per-option scores into an Answer; used by adapters. */
export function toAnswer(q: Question, raw: unknown): Answer {
  if (q.type === "choice") {
    const opts = Object.keys(q.criteria);
    const src = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
    const p: Record<string, number> = {};
    for (const o of opts) p[o] = Math.max(0, Number(src[o] ?? 0)) || 0;
    const sum = Object.values(p).reduce((a, b) => a + b, 0);
    if (sum > 0) for (const o of opts) p[o] = Math.round((p[o] / sum) * 1000) / 1000;
    else for (const o of opts) p[o] = Math.round(1000 / opts.length) / 1000;
    const sorted = [...opts].sort((a, b) => p[b] - p[a]);
    return { answer: sorted[0], probabilities: p, confidence: p[sorted[0]] };
  }
  if (q.type === "boolean") {
    const t = Math.min(1, Math.max(0, Number(raw ?? 0.5)));
    return { answer: t >= 0.5, probabilities: { true: t, false: Math.round((1 - t) * 1000) / 1000 }, confidence: Math.max(t, 1 - t) };
  }
  // score: raw is either the expected level, or {level: p} probabilities.
  const n = q.criteria.length;
  if (raw && typeof raw === "object") {
    const ps = q.criteria.map((_, i) => Math.max(0, Number((raw as Record<string, unknown>)[String(i)] ?? 0)));
    const sum = ps.reduce((a, b) => a + b, 0) || 1;
    const p = Object.fromEntries(ps.map((x, i) => [String(i), Math.round((x / sum) * 1000) / 1000]));
    const exp = ps.reduce((a, x, i) => a + i * x / sum, 0);
    return { answer: Math.round(exp * 100) / 100, probabilities: p, confidence: Math.max(...Object.values(p)) };
  }
  const v = Math.min(n - 1, Math.max(0, Number(raw ?? 0)));
  return { answer: v, probabilities: {}, confidence: 0.5 };
}
