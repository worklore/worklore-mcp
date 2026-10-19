// What a page or file is, from where it lives. Founders don't configure their
// material: a site's /faq, /docs and /stories (or a repo's docs/ and
// stories/ folders) are recognised by their path, so the draft can point
// someone to "the FAQ" or "how someone did this" (draft/materials.ts).

export type MaterialKind = "faq" | "docs" | "story" | "changelog" | "article";

const RULES: [MaterialKind, RegExp][] = [
  ["faq", /(^|\/)(faqs?|frequently-asked-questions|questions)(\/|\.|$)/i],
  ["changelog", /(^|\/)(changelog|changes|releases?|release-notes|whats-new|what-s-new|updates)(\/|\.|$)/i],
  ["docs", /(^|\/)(docs?|documentation|guides?|help|manual|reference|tutorials?|how-?to|getting-started|kb|knowledge-base|support)(\/|\.|$)/i],
  ["story", /(^|\/)(stories|story|case-stud(y|ies)|customers?|success-stories|examples?|showcase|use-cases?|testimonials)(\/|\.|$)/i],
  ["article", /(^|\/)(blog|posts?|articles?|news|journal|writing)(\/|\.|$)/i],
];

/** Pure. The kind of a page URL or repo path, null when the path says nothing. */
export function materialKind(urlOrPath: string): MaterialKind | null {
  let path = urlOrPath;
  try { path = new URL(urlOrPath).pathname; } catch { /* a repo path */ }
  path = path.toLowerCase();
  for (const [kind, re] of RULES) if (re.test(path)) return kind;
  return null;
}

/** Pure. Material first (faq, docs, stories, changelog, articles), then the rest; stable otherwise. */
export function materialFirst<T>(xs: T[], url: (x: T) => string): T[] {
  const rank = (x: T) => {
    const k = materialKind(url(x));
    return k === "faq" ? 0 : k === "docs" ? 1 : k === "story" ? 2 : k === "changelog" ? 3 : k === "article" ? 4 : 5;
  };
  return xs.map((x, i) => ({ x, i, r: rank(x) })).sort((a, b) => a.r - b.r || a.i - b.i).map((y) => y.x);
}
