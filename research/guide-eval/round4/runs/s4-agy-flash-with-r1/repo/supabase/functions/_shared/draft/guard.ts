// Fact guard: a draft must not state numbers, percentages, statistics or
// cited studies that are neither in the retrieved sources nor in the thread.
// The model can't know them (2026-10-09: "78% of failed agent tasks…",
// "reduced my failure rate by 40%"), so each one becomes a [check: …] gap she
// fills or deletes. Deterministic, no model call. Pure; tested.

export interface GuardResult {
  text: string;
  /** What was turned into gaps, as found in the draft ("78%", "a study by Stanford"). */
  invented: string[];
}

const SMALL = 10; // "two things", "3 steps": small counts are not statistics…
// …unless they carry a unit that makes them a measurement or a share.
const UNIT = String.raw`(?:%|\s?percent\b|\s?pct\b|x\b|×|\s?(?:times|hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?|months?|years?|ms|k\b|m\b|tokens?|users?|people|developers|devs|stars|downloads|requests|calls|tasks|agents|stories|repos|projects|customers|signups|sign-ups|installs|dollars|usd)\b)`;
const NUMBER = new RegExp(String.raw`(?<![\w.#/@:-])(\$?\d{1,3}(?:[,\s]\d{3})+(?:\.\d+)?|\$?\d+(?:\.\d+)?)((?:st|nd|rd|th)\b)?(${UNIT})?`, "gi");
const CITED = /\b(?:according to|a (?:recent )?(?:study|survey|report|paper) (?:by|from)|(?:studies|research|surveys|data) (?:show|shows|suggest|suggests|found|finds))\b[^.!?\n]*/gi;

const digitsOf = (s: string) => s.replace(/[^\d.]/g, "").replace(/\.$/, "");

/** The numbers present anywhere in the context, as digit strings ("1,200" → "1200"). */
function contextNumbers(context: string): Set<string> {
  const out = new Set<string>();
  for (const m of context.matchAll(/\d[\d,.\s]*\d|\d/g)) {
    const d = digitsOf(m[0].replace(/\s/g, ""));
    if (d) out.add(d);
    for (const part of m[0].split(/[\s,]+/)) if (part) out.add(digitsOf(part));
  }
  return out;
}

/** Applies f to the text outside existing [check: …] gaps. */
function outsideChecks(text: string, f: (part: string) => string): string {
  return text.split(/(\[check:[^\]]*\])/gi).map((p) => (/^\[check:/i.test(p) ? p : f(p))).join("");
}

export function guardFacts(draft: string, context: string): GuardResult {
  const known = contextNumbers(context);
  const ctxLower = context.toLowerCase();
  const invented: string[] = [];
  let text = outsideChecks(draft, (part) => part.replace(CITED, (m) => {
    if (ctxLower.includes(m.toLowerCase().trim())) return m;
    invented.push(m.trim());
    return `[check: ${m.trim()} — source?]`;
  }));
  text = outsideChecks(text, (part) => part.replace(NUMBER, (m, num: string, ord: string | undefined, unit: string | undefined, offset: number, whole: string) => {
    const before = whole.slice(Math.max(0, offset - 2), offset);
    const digits = digitsOf(num);
    if (!digits) return m;
    const value = Number(digits);
    // Years and version-like numbers next to a dot are dates/versions, not stats.
    if (/^(19|20)\d\d$/.test(digits) && !unit) return m;
    if (/\.\s?$/.test(before) && /^\d$/.test(digits)) return m;
    if (!unit && !ord && value <= SMALL) return m;
    if (known.has(digits)) return m;
    invented.push(m.trim());
    return `[check: ${m.trim()} — not in your sources]`;
  }));
  return { text, invented };
}
