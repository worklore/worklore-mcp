// Grapheme-aware length (Bluesky counts graphemes, max 300 per post) and a
// cut that ends at a sentence or word boundary.

const seg = new Intl.Segmenter(undefined, { granularity: "grapheme" });

export function graphemeLength(s: string): number {
  let n = 0;
  for (const _ of seg.segment(s)) n++;
  return n;
}

export function clampGraphemes(s: string, max: number): string {
  if (graphemeLength(s) <= max) return s;
  const gs = [...seg.segment(s)].map((x) => x.segment);
  const head = gs.slice(0, max - 1).join("");
  // Prefer the last sentence end in the second half; else the last space.
  const ends = [...head.matchAll(/[.!?](\s|$)/g)].map((m) => (m.index ?? 0) + 1);
  const lastEnd = ends.length ? ends[ends.length - 1] : -1;
  if (lastEnd > head.length * 0.4) return head.slice(0, lastEnd).trim();
  const sp = head.lastIndexOf(" ");
  return (sp > head.length * 0.5 ? head.slice(0, sp) : head).trim() + "…";
}

export function firstSentence(s: string, max = 160): string {
  const t = s.replace(/\s+/g, " ").trim();
  const m = t.match(/^.{10,}?[.!?](\s|$)/);
  const out = m ? m[0].trim() : t;
  return out.length <= max ? out : out.slice(0, max).replace(/\s+\S*$/, "") + "…";
}

/** Pure: how many of the topics' words appear in the text (for pre-ranking). Exported for tests. */
export function topicScore(text: string, topics: string[]): number {
  const t = text.toLowerCase();
  let s = 0;
  for (const topic of topics) {
    const words = topic.toLowerCase().replace(/^#/, "").split(/\s+/).filter((w) => w.length > 2);
    if (words.length && words.every((w) => t.includes(w))) s += 2;
    else s += words.filter((w) => t.includes(w)).length * 0.5;
  }
  return s;
}

/** Plain text from comment HTML (dev.to, any HTML message). */
export function htmlToText(html: string): string {
  return html
    .replace(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/g, (_m, c) => "\n```\n" + c + "\n```\n")
    .replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, (_m, href, t) => {
      const txt = t.replace(/<[^>]+>/g, "");
      return txt.trim() === href.trim() ? href : `${txt} (${href})`;
    })
    .replace(/<br\s*\/?>/g, "\n")
    .replace(/<\/(p|li|h\d|blockquote)>/g, "\n")
    .replace(/<li>/g, "- ")
    .replace(/<[^>]+>/g, "")
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&nbsp;/g, " ")
    .replace(/&#x([0-9a-f]+);/gi, (_m, n) => String.fromCodePoint(parseInt(n, 16)))
    .replace(/&#(\d+);/g, (_m, n) => String.fromCodePoint(Number(n)))
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Markdown → readable plain text (keeps code and link targets). */
export function markdownToText(md: string): string {
  return md
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m, t, u) => (t.trim() === u.trim() ? u : `${t} (${u})`))
    .replace(/\{%[^%]*%\}/g, "")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/(\*\*|__)(.*?)\1/g, "$2")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
