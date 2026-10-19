// Small, dependency-free text helpers: token estimate, language guess,
// lexical similarity for choosing voice samples and memory snippets.
// Lexical is deliberate for v1: no extra model call per draft, deterministic,
// good enough at 10s–100s of samples. An embedding column can replace
// `similarity()` later without touching the callers.

/** ~4 chars per token for Latin text, ~2.5 for Cyrillic. Close enough for budgeting. */
export function estimateTokens(s: string): number {
  if (!s) return 0;
  const cyr = (s.match(/[Ѐ-ӿ]/g) ?? []).length;
  return Math.ceil((s.length - cyr) / 4 + cyr / 2.5);
}

export function words(s: string): number {
  return (s.trim().match(/\S+/g) ?? []).length;
}

/** Cheap language guess for the languages Valentina writes in. */
export function detectLanguage(s: string): string {
  const letters = s.replace(/```[\s\S]*?```/g, "").replace(/https?:\/\/\S+/g, "");
  const cyr = (letters.match(/[Ѐ-ӿ]/g) ?? []).length;
  const lat = (letters.match(/[A-Za-z]/g) ?? []).length;
  if (cyr > lat) return "ru";
  const es = (letters.toLowerCase().match(/\b(que|para|los|las|una|por|pero|está|gracias|muy|también|cómo)\b/g) ?? []).length;
  const en = (letters.toLowerCase().match(/\b(the|and|is|to|of|that|it|for|with|this|you)\b/g) ?? []).length;
  if (es > en && es >= 3) return "es";
  return "en";
}

const STOP = new Set(("a an the and or but if then of to in on at for with by from as is are was were be been being it its this that " +
  "these those i you he she we they me my your our their his her them us do does did done have has had not no so too very just " +
  "can could would should will what which who how why when where there here than also about into over out up more most some any " +
  "all one two get got really thanks thank yes like").split(" "));

export function terms(s: string): string[] {
  const toks = s.toLowerCase().replace(/https?:\/\/\S+/g, " ").match(/[\p{L}\p{N}][\p{L}\p{N}_.-]*[\p{L}\p{N}]|[\p{L}\p{N}]/gu) ?? [];
  const out: string[] = [];
  for (const t of toks) if (t.length > 2 && !STOP.has(t)) out.push(stem(t));
  return out;
}

function stem(t: string): string {
  return t.replace(/(ings?|ed|es|s|ly)$/u, "") || t;
}

/** BM25 over a small in-memory corpus. Returns scores aligned with docs. */
export function bm25(query: string, docs: string[], k1 = 1.4, b = 0.75): number[] {
  const dt = docs.map(terms);
  const avg = dt.reduce((s, d) => s + d.length, 0) / Math.max(1, dt.length);
  const df = new Map<string, number>();
  for (const d of dt) for (const t of new Set(d)) df.set(t, (df.get(t) ?? 0) + 1);
  const q = [...new Set(terms(query))];
  return dt.map((d) => {
    const tf = new Map<string, number>();
    for (const t of d) tf.set(t, (tf.get(t) ?? 0) + 1);
    let s = 0;
    for (const t of q) {
      const f = tf.get(t);
      if (!f) continue;
      const n = df.get(t) ?? 0;
      const idf = Math.log(1 + (dt.length - n + 0.5) / (n + 0.5));
      s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d.length / (avg || 1)));
    }
    return s;
  });
}

/** Cut at a sentence/paragraph boundary near maxTokens, never mid-word. */
export function truncateToTokens(s: string, maxTokens: number): string {
  if (estimateTokens(s) <= maxTokens) return s;
  const approxChars = Math.max(40, Math.floor(s.length * maxTokens / estimateTokens(s)));
  const cut = s.slice(0, approxChars);
  const at = Math.max(cut.lastIndexOf("\n\n"), cut.lastIndexOf(". "), cut.lastIndexOf("? "), cut.lastIndexOf("! "));
  return (at > approxChars * 0.5 ? cut.slice(0, at + 1) : cut.replace(/\s+\S*$/, "")) + " […]";
}

export function median(xs: number[]): number {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
