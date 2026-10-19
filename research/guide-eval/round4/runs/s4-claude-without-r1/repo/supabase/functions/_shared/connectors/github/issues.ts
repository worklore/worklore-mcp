// Pure parts of "idea → GitHub issue": the issue body (people's own words as
// quotes, each linked to its conversation), the duplicate search (title words
// → GitHub search queries → ranked open issues) and label choice (only labels
// the repo already has; Hearback never creates labels). Tested in
// github_app_test.ts.

export interface IssueAsk {
  /** The person's name as shown in Hearback. */
  name: string;
  /** Their words (the item text). */
  text: string;
  /** Link to the conversation (dev.to comment, Bluesky post). */
  url: string | null;
  /** Connector id: devto, bluesky, … */
  platform: string;
  posted_at?: string | null;
}

export interface IssueIdea {
  title: string;
  summary: string | null;
  kind: string;
  themes: string[];
}

const PLATFORM_LABEL: Record<string, string> = { devto: "dev.to", bluesky: "Bluesky", github: "GitHub", threads: "Threads", habr: "Habr", reddit: "Reddit", x: "X" };
export const platformLabel = (p: string) => PLATFORM_LABEL[p] ?? p;

const KIND_LABEL: Record<string, string> = { feature: "Feature idea", bug: "Bug", pain: "Pain point", would_pay: "Would pay if", other: "Idea" };

/** No GitHub @mentions or issue references from other people's words. */
export function neutralize(s: string): string {
  return s.replace(/@(?=[A-Za-z0-9-])/g, "@​").replace(/(^|\s)#(?=\d)/g, "$1#​");
}

const MAX_QUOTE = 600;

function quoteBlock(a: IssueAsk): string {
  let t = a.text.replace(/\r\n/g, "\n").trim();
  if (t.length > MAX_QUOTE) t = t.slice(0, MAX_QUOTE).replace(/\s+\S*$/, "") + " …";
  const lines = neutralize(t).split("\n").map((l) => `> ${l}`.trimEnd());
  const where = platformLabel(a.platform);
  const source = a.url ? `[${where}](${a.url})` : where;
  return `${lines.join("\n")}\n>\n> — ${neutralize(a.name)} on ${source}`;
}

/** Max people quoted in one issue (the rest are counted). */
export const MAX_ASKS = 10;

/** Pure. The issue body: summary, people's words, the theme, the source line. */
export function issueBody(idea: IssueIdea, asks: IssueAsk[]): string {
  const shown = asks.slice(0, MAX_ASKS);
  const people = new Set(asks.map((a) => a.name)).size;
  const parts: string[] = [];
  if (idea.summary?.trim()) parts.push(idea.summary.trim());
  parts.push(`### What people said\n\n${shown.map(quoteBlock).join("\n\n")}`);
  if (asks.length > shown.length) parts.push(`…and ${asks.length - shown.length} more.`);
  const theme = idea.themes.length ? idea.themes.join(", ") : (KIND_LABEL[idea.kind] ?? "Idea");
  parts.push(`**Theme:** ${neutralize(theme)}  \n**Asked by:** ${people} ${people === 1 ? "person" : "people"}`);
  parts.push("---\n_Created from [Hearback](https://hearback.dev)._");
  return parts.join("\n\n");
}

/** Pure. A comment for an existing issue: "more people asked", with their words. */
export function issueComment(asks: IssueAsk[]): string {
  const shown = asks.slice(0, MAX_ASKS);
  const people = new Set(asks.map((a) => a.name)).size;
  return [
    `${people === 1 ? "Someone else asked" : `${people} more people asked`} for this:`,
    shown.map(quoteBlock).join("\n\n"),
    "---\n_Added from [Hearback](https://hearback.dev)._",
  ].join("\n\n");
}

const STOP = new Set(("a an and are as at be but by can could do does for from has have how i if in into is it its " +
  "me more my no not of on or our please should so some than that the their them then there these they this to " +
  "too us use using was we were what when where which while who why will with would you your add support allow " +
  "make let want wants need needs able way feature").split(" "));

/** Pure. The words of a title worth searching for, most specific (longest) first, ≤ 6. */
export function titleWords(title: string): string[] {
  const words = title.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .split(/[^a-z0-9+.#-]+/).map((w) => w.replace(/^[.#-]+|[.#-]+$/g, ""))
    .filter((w) => w.length >= 3 && !STOP.has(w) && !/^\d+$/.test(w));
  return [...new Set(words)].sort((a, b) => b.length - a.length).slice(0, 6);
}

/**
 * Pure. Search queries to try in order (GitHub's issue search ANDs terms, so
 * three words, then the two most specific). Empty when the title has no
 * searchable words.
 */
export function duplicateQueries(repo: string, title: string): string[] {
  const w = titleWords(title);
  if (!w.length) return [];
  const base = `repo:${repo} is:issue is:open in:title`;
  const qs = [`${base} ${w.slice(0, 3).join(" ")}`];
  if (w.length > 2) qs.push(`${base} ${w.slice(0, 2).join(" ")}`);
  return qs;
}

/** Pure. Shared title words / all title words (0–1, two decimals): how alike two asks read. */
export function wordOverlap(want: Set<string>, title: string): number {
  const have = new Set(titleWords(title));
  const shared = [...want].filter((w) => have.has(w)).length;
  const union = new Set([...want, ...have]).size || 1;
  return Math.round((shared / union) * 100) / 100;
}

export interface DuplicateIssue { number: number; title: string; url: string; score: number; comments: number }

/** Pure. GET /search/issues JSON → open issues (not PRs) that look like the same ask, best first, ≤ 3. */
export function parseDuplicates(json: unknown, title: string, minScore = 0.2): DuplicateIssue[] {
  const items = (json as { items?: unknown[] } | null)?.items;
  if (!Array.isArray(items)) return [];
  const want = new Set(titleWords(title));
  const out: DuplicateIssue[] = [];
  for (const raw of items) {
    const it = raw as { number?: number; title?: string; html_url?: string; state?: string; pull_request?: unknown; comments?: number };
    if (typeof it.number !== "number" || typeof it.title !== "string" || typeof it.html_url !== "string") continue;
    if (it.pull_request || (it.state && it.state !== "open")) continue;
    const score = wordOverlap(want, it.title);
    if (score < minScore) continue;
    out.push({ number: it.number, title: it.title, url: it.html_url, score, comments: it.comments ?? 0 });
  }
  return out.sort((a, b) => b.score - a.score || b.number - a.number).slice(0, 3);
}

const WANTED: Record<string, string[]> = {
  feature: ["enhancement", "feature", "feature request"],
  would_pay: ["enhancement", "feature", "feature request"],
  bug: ["bug"],
  pain: ["enhancement", "ux"],
  other: [],
};
const ALWAYS = ["from-users", "user feedback", "feedback"];

/** Pure. Labels to put on the issue: only ones the repo has, spelled as the repo spells them. */
export function pickLabels(existing: string[], kind: string): string[] {
  const byLower = new Map(existing.map((l) => [l.toLowerCase(), l]));
  const out: string[] = [];
  const kindLabel = (WANTED[kind] ?? []).map((w) => byLower.get(w)).find(Boolean);
  if (kindLabel) out.push(kindLabel);
  const from = ALWAYS.map((w) => byLower.get(w)).find(Boolean);
  if (from) out.push(from);
  return out;
}

/** Pure. "https://github.com/o/r/issues/12" → 12 (null for anything else). */
export function issueNumberFromUrl(url: string | null | undefined): number | null {
  const m = url?.match(/^https:\/\/github\.com\/[^/]+\/[^/]+\/issues\/(\d+)/);
  return m ? Number(m[1]) : null;
}
