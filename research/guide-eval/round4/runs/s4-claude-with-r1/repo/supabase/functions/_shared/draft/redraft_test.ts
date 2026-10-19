// deno test supabase/functions/_shared/draft/redraft_test.ts   (no network)
// Redraft is built on her point, or only rewords; points come from her own words.
import { assert, assertEquals } from "jsr:@std/assert@1";
import { assemble, targetLength } from "./context.ts";
import { parsePoints, pointSources } from "./points.ts";
import { userPrompt } from "./prompt.ts";
import type { DraftRequest, VoiceSample } from "./types.ts";

const words = (n: number) => Array.from({ length: n }, (_, i) => `w${i}`).join(" ");

function req(over: Partial<DraftRequest> = {}): DraftRequest {
  return {
    project: { name: "Hearback", founder_name: "Valentina", founder_handle: "yahhi" },
    context: {
      platform: "devto", kind: "reply", post: { title: "Shipping faster with AI", text: "", author: "dimitris", is_owner: false },
      chain: [{ author: "yahhi", is_owner: true, text: "Every developer KPI I've seen broke the same way. The signal I trust most is how long a new person takes to make a safe change." }],
      item: { author: "dimitris", text: "That last point is probably the best answer to the question.", posted_at: "2026-10-12T06:20:59Z" },
    },
    person: { handle: "dimitris", touches: [{ direction: "out", text: "Thanks for the link.", occurred_at: "2026-10-01T00:00:00Z" }, { direction: "in", text: "hi", occurred_at: "2026-10-02T00:00:00Z" }] },
    voice_pool: [], memory_pool: [],
    knowledge: [{ id: "k1", kind: "article", title: "The code was never the point", source_url: "https://dev.to/x", published_at: "2026-09-22T00:00:00Z", text: "Agents let us fly over a codebase.", tokens: 10, lang: "en" }],
    ...over,
  } as DraftRequest;
}

Deno.test("point sources: her thread comment, what she wrote to them, her published work; not their messages", () => {
  const s = pointSources(req());
  assertEquals(s.map((x) => `${x.id}:${x.kind}`), ["T1:thread", "P1:earlier", "K1:published"]);
});

Deno.test("parsePoints keeps cited points, drops unknown sources and duplicates, caps at 3", () => {
  const sources = pointSources(req());
  const raw = '```json\n{"points":[{"source":"T1","text":"The signal I trust is how long a new person takes to make a safe change."},' +
    '{"source":"X9","text":"An invented idea about prompts."},{"source":"[K1]","text":"Agents let us fly over a codebase."},' +
    '{"source":"T1","text":"The signal I trust is how long a new person takes to make a safe change."},{"source":"P1","text":"ok"}]}\n```';
  const p = parsePoints(raw, sources);
  assertEquals(p.map((x) => x.source.id), ["T1", "K1"]);
  assertEquals(p[1].source.url, "https://dev.to/x");
  assert(p[0].source.excerpt.startsWith("Every developer KPI"));
  assertEquals(parsePoints("not json", sources), []);
});

Deno.test("redraft with her point builds on it; without one it only rewords", () => {
  const base = req({ variant: "redraft", previous_draft: "Old draft about saving prompts." });
  const withPoint = userPrompt({ ...base, gist: "KPIs broke long before AI." }, assemble(base), "redraft", "v4");
  assert(withPoint.includes("Her point:\nKPIs broke long before AI."));
  assert(withPoint.includes("Don't add another idea"));
  assert(!withPoint.includes("different angle"));
  const reword = userPrompt(base, assemble(base), "redraft", "v4");
  assert(reword.includes("Reword this draft"));
  assert(reword.includes("Don't add any idea"));
});

Deno.test("target length: a short message is sized from her short replies and capped by its own length", () => {
  const pool: VoiceSample[] = [
    ...[150, 170, 190, 200, 220].map((n, i) => ({ id: `long${i}`, text: words(n) })),
    ...[30, 40, 45, 50, 55].map((n, i) => ({ id: `short${i}`, text: words(n) })),
  ];
  const r = req({ voice_pool: pool, context: { ...req().context, item: { author: "d", text: words(60), posted_at: "2026-10-12T00:00:00Z" } } });
  const [lo, hi] = targetLength(r, []);
  assert(hi <= Math.round(90 * 1.35), `hi ${hi}`);
  assertEquals([lo, hi], [27, 61]); // mid 45 = median of her short replies
  // A long message keeps the full pool.
  const long = req({ voice_pool: pool, context: { ...req().context, item: { author: "d", text: words(300), posted_at: "2026-10-12T00:00:00Z" } } });
  assert(targetLength(long, [])[1] > 100);
});

Deno.test("her point is grown and tied to their words, not squeezed (even on a short reaction)", () => {
  const base = req({ variant: "redraft", previous_draft: "Thanks!", item_kind: "reaction", gist: "KPIs broke long before AI." });
  const p = userPrompt(base, assemble(base), "redraft", "v4");
  assert(p.includes("develop it against what @dimitris actually said"));
  assert(p.includes("longer than her point"));
  const short = req({ variant: "redraft", previous_draft: "Thanks!", item_kind: "reaction" });
  const reword = userPrompt(short, assemble(short), "redraft", "v4");
  const cap = (t: string) => Number(t.match(/at most (\d+) words/)?.[1]);
  assert(cap(reword) <= 60, `reaction reword capped: ${cap(reword)}`);
});

Deno.test("Longer grows the one-liner with its point instead of starting over", () => {
  const base = req({ variant: "redraft", previous_draft: "KPIs broke long before AI.", expand: true, gist: "KPIs broke long before AI." });
  const p = userPrompt(base, assemble(base), "redraft", "v4");
  assert(p.includes("Make this one-line draft a full reply"));
  assert(p.includes("and her point"));
  assert(p.includes("Draft:\nKPIs broke long before AI."));
  assert(!p.includes("Reword this draft"));
});
