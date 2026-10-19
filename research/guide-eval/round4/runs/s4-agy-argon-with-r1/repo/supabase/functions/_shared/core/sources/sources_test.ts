// Sources pipeline: connector contract (a fake source plugs in), the voice
// filter's routing (rules before Jev), the active set, the GitHub folder sync
// (SHA skip, size caps, ETag, private repo, rate limit) and idempotent
// knowledge storage.
//   deno test -A supabase/functions/_shared/

import { assert, assertEquals } from "jsr:@std/assert@1";
import "../../connectors/mod.ts";
import type { Decider, Decision, Questions } from "../../draft/decide/decider.ts";
import { voicePool } from "../../draft/load.ts";
import { DevtoPublic } from "../../connectors/devto/api.ts";
import { devtoOwnWriting, ownWritingFromComments, parseDeviceRefs } from "../../connectors/devto/sources.ts";
import { flattenTree } from "../../connectors/devto/parse.ts";
import { githubFolderSource } from "../../connectors/github/connector.ts";
import { GITHUB_CAPS, planGithubSync, writingFromFile } from "../../connectors/github/split.ts";
import { docSha, planDocs } from "../../server/knowledge.ts";
import { connector, connectors, registerConnector, unregisterConnector } from "../registry.ts";
import type { Connector, SourceContext } from "../types.ts";
import { sameSiteLinks } from "./site.ts";
import { FEW_SAMPLES, judgeCandidate, ruleReject, selectActive, verdictFrom } from "./voice.ts";

const ctx = (over: Partial<SourceContext> = {}): SourceContext => ({
  state: {}, deadline: Date.now() + 60_000, knownWriting: () => Promise.resolve(new Set()), ...over,
});

/** A decider that records calls and answers fixed probabilities. */
function fakeDecider(pMeaningful: number, quality: number) {
  const calls: string[] = [];
  const d: Decider = {
    name: "fake", model: "fake-1",
    decide(state: string | Record<string, unknown>, _q: Questions): Promise<Decision> {
      calls.push(String(state));
      return Promise.resolve({
        answers: {
          meaningful: { answer: pMeaningful >= 0.5, probabilities: { true: pMeaningful, false: 1 - pMeaningful }, confidence: Math.max(pMeaningful, 1 - pMeaningful) },
          quality: { answer: quality, probabilities: {}, confidence: 0.8 },
        },
        decider: "fake", model: "fake-1", usage: { tokens_in: null, tokens_out: null }, latency_ms: 1,
      });
    },
  };
  return { d, calls };
}

// ------------------------------------------------------------------ contract
const fakeForum: Connector = {
  id: "forum", label: "Forum", auth: "none", accountAuth: "none", needsSecret: false, enabled: () => true, schedule: null,
  rateLimit: { minIntervalMs: 0, maxRequestsPerRun: 10, on429: "retry_after" }, reply: { mode: "none", maxGraphemes: null },
  ownWriting: async (account, c) => {
    const all = [
      { platform: "forum", external_id: "p1", url: "https://forum.example/p1", text: "I tried three schedulers before settling on a plain cron job, because the failure modes were easier to see.", posted_at: "2026-09-01T10:00:00Z", context: "Which scheduler do you use?" },
      { platform: "forum", external_id: "p2", url: "https://forum.example/p2", text: "🙏🔥", posted_at: "2026-09-02T10:00:00Z" },
    ];
    const known = await c.knownWriting("forum", all.map((x) => x.external_id));
    return { writing: all.filter((x) => !known.has(x.external_id)), state: { cursor: `after:${account.handle}` }, status: "ok" };
  },
  projectSource: (project) => Promise.resolve({
    documents: [{ kind: "article", title: "Notes", url: `https://forum.example/${project.id}`, published_at: "2026-09-03", markdown: "# Notes\n\nSome text." }],
    status: "ok",
  }),
};

Deno.test("a fake source connector plugs in: own writing → rules + decider → active set; project source → documents", async () => {
  registerConnector(fakeForum);
  try {
    assertEquals(connector("forum")?.label, "Forum");
    assert(connectors().some((c) => c.id === "github" && c.projectSource), "github is a registered source connector");
    assert(connectors().some((c) => c.id === "devto" && c.ownWriting && c.publishedWork));
    const acct = { id: "a1", project_id: "p", platform: "forum", handle: "me" };
    const b = await fakeForum.ownWriting!(acct, ctx({ knownWriting: () => Promise.resolve(new Set(["p9"])) }));
    assertEquals(b.writing!.length, 2);
    assertEquals(b.state, { cursor: "after:me" });
    const { d, calls } = fakeDecider(0.9, 3);
    const verdicts = await Promise.all(b.writing!.map((w) => judgeCandidate(d, { text: w.text, context: w.context, platform: w.platform })));
    assertEquals(verdicts.map((v) => v.status), ["accepted", "rejected"]);
    assertEquals(verdicts[1].reason, "rule: emoji_only");
    assertEquals(calls.length, 1, "the emoji-only candidate never reaches the decider");
    assert(calls[0].includes("Which scheduler do you use?"), "the decider sees what it answered");
    const docs = await fakeForum.projectSource!({ id: "p" }, ctx());
    assertEquals(docs.documents?.[0].url, "https://forum.example/p");
    // Known ids are skipped by the connector itself.
    const again = await fakeForum.ownWriting!(acct, ctx({ knownWriting: () => Promise.resolve(new Set(["p1", "p2"])) }));
    assertEquals(again.writing!.length, 0);
  } finally {
    unregisterConnector("forum");
  }
});

// ------------------------------------------------------------------ voice filter
Deno.test("voice rules reject without a model: emoji-only, bare thanks, too short, code, quotes, links", () => {
  assertEquals(ruleReject("🔥🔥🔥"), "emoji_only");
  assertEquals(ruleReject("+1 👍"), "emoji_only");
  assertEquals(ruleReject("Thanks a lot!"), "bare_thanks");
  assertEquals(ruleReject("Great post!! 🙌"), "bare_thanks");
  assertEquals(ruleReject("Yes, that one."), "too_short");
  assertEquals(ruleReject("```\nconst a = 1;\nconst b = 2;\nconsole.log(a + b);\n```\nsee above"), "mostly_code");
  assertEquals(ruleReject("> You said the cache never expires and the job runs every night\n> and nobody noticed for a week\nright"), "mostly_quote");
  assertEquals(ruleReject("see https://e.com/a https://e.com/b https://e.com/c https://e.com/d https://e.com/e https://e.com/f https://e.com/g"), "mostly_links");
  assertEquals(ruleReject("Thanks! I ran into the same thing last week: the retry loop hid the real error until I logged it."), null);
});

Deno.test("decider verdict: accepted above both thresholds, rejected below either", async () => {
  const text = "I tried three schedulers before settling on a plain cron job, because the failure modes were easier to see.";
  for (const [p, q, want] of [[0.9, 3, "accepted"], [0.3, 3, "rejected"], [0.9, 1, "rejected"], [0.6, 1.5, "accepted"]] as const) {
    const { d } = fakeDecider(p, q);
    const v = await judgeCandidate(d, { text, platform: "devto" });
    assertEquals(v.status, want, `p=${p} q=${q}`);
    assert(v.reason.startsWith("decider:"));
    assertEquals((v.scores as Record<string, unknown>).decider, "fake");
  }
  const v = verdictFrom({ answers: {}, decider: "x", model: "y" });
  assertEquals(v.status, "rejected");
});

Deno.test("selectActive: cap, near-duplicates skipped, Hearback replies and quality first, length bands mixed", () => {
  const mk = (id: string, words: number, q: number, extra: Partial<{ source: string; platform: string; posted_at: string }> = {}) => ({
    id, text: Array.from({ length: words }, (_, i) => `${id}w${i}`).join(" "), platform: "devto", source: "own_writing", quality: q,
    posted_at: "2026-09-01T00:00:00Z", ...extra,
  });
  const pool = [
    ...Array.from({ length: 40 }, (_, i) => mk(`s${i}`, 20, 2 + (i % 3) * 0.5)),
    ...Array.from({ length: 10 }, (_, i) => mk(`l${i}`, 150, 2.5)),
    mk("h1", 30, 2, { source: "hearback" }),
  ];
  const chosen = selectActive(pool, 30, new Date("2026-10-09T00:00:00Z"));
  assertEquals(chosen.length, 30);
  assert(chosen.includes("h1"), "a reply posted through Hearback gets in");
  assertEquals(chosen.filter((id) => id.startsWith("l")).length, 10, "all long ones fit: short band is capped at half");
  const dup = { ...mk("d1", 20, 4), text: pool[0].text };
  const withDup = selectActive([pool[0], dup], 30);
  assertEquals(withDup.length, 1, "same words twice: one sample");
  assert(FEW_SAMPLES > 0);
});

Deno.test("voicePool: her reply to this very item is left out of the draft's pool", () => {
  const item = "Does the MCP server cache tool lists between sessions, or does every client fetch them again?";
  const rows = [
    { id: "1", text: "It caches them per session.", context: `Reply to @ana on "X": ${item}`, posted_at: "2026-10-01T00:00:00Z" },
    { id: "2", text: "Another reply of hers.", context: "Comment on \"Y\"", posted_at: "2026-09-01T00:00:00Z" },
  ];
  assertEquals(voicePool(rows, item).map((v) => v.id), ["voice:2"]);
  assertEquals(voicePool(rows, null).length, 2);
});

// ------------------------------------------------------------------ dev.to own writing
const tree = [{
  id_code: "c1", created_at: "2026-09-01T10:00:00Z", body_html: "<p>How do you count tool calls?</p>", user: { username: "ana" },
  children: [{ id_code: "c2", created_at: "2026-09-01T11:00:00Z", body_html: "<p>Per session, in a small table keyed by the tool name.</p>", user: { username: "yahhi" }, children: [] }],
}, { id_code: "c3", created_at: "2026-09-02T10:00:00Z", body_html: "<p>Nice write-up on the registry, the server.json part saved me an hour.</p>", user: { username: "Yahhi" }, children: [] }];

Deno.test("dev.to: her comments in a tree become candidates with what they answered", () => {
  const art = { id: 7, title: "Counting tools", url: "https://dev.to/ana/counting", user: { username: "ana" } };
  const w = ownWritingFromComments(flattenTree(art, "yahhi", tree), "yahhi");
  assertEquals(w.map((x) => x.external_id), ["c2", "c3"]);
  assert(w[0].context!.startsWith('Reply to @ana on "Counting tools": How do you count'));
  assertEquals(w[1].context, 'Comment on "Counting tools" by @ana');
  assertEquals(parseDeviceRefs([{ id_code: "abc" }, { id_code: "abc" }, { id_code: "../x" }, null]).map((r) => r.id_code), ["abc"]);
});

/** A DevtoPublic that answers from a map, counting requests. */
function fakeDevto(routes: Record<string, unknown>) {
  const api = new DevtoPublic(60, 0);
  const seen: string[] = [];
  api.get = <T>(path: string) => { api.requests++; seen.push(path); return Promise.resolve((routes[path] ?? null) as T | null); };
  return { api, seen };
}

Deno.test("dev.to ownWriting: unchanged articles cost no tree request; phone refs are fetched once and must be hers", async () => {
  const { api, seen } = fakeDevto({
    "/articles?username=yahhi&per_page=30": [{ id: 1, title: "Mine", url: "https://dev.to/yahhi/mine", comments_count: 2, published_at: "2026-09-01T00:00:00Z", user: { username: "yahhi" } }],
    "/articles/9": { id: 9, title: "Ana's", url: "https://dev.to/ana/x", comments_count: 2, published_at: "2026-09-01T00:00:00Z", user: { username: "ana" } },
    "/comments?a_id=9&per_page=1000": tree,
    "/comments/r1": { id_code: "r1", created_at: "2026-08-01T00:00:00Z", body_html: "<p>I moved the cron to the database and the drift went away.</p>", user: { username: "yahhi" } },
    "/comments/r2": { id_code: "r2", created_at: "2026-08-01T00:00:00Z", body_html: "<p>not hers</p>", user: { username: "mallory" } },
  });
  const acct = { id: "a", project_id: "p", platform: "devto", handle: "yahhi", settings: { watch_articles: [9] } };
  const b = await devtoOwnWriting(acct, ctx({
    state: { counts: { "1": 2 } }, // her own article unchanged since last run
    deviceRefs: [{ id_code: "c2" }, { id_code: "r1", article_title: "Cron" }, { id_code: "r2" }, { id_code: "k1" }],
    knownWriting: (_p, ids) => Promise.resolve(new Set(ids.filter((i) => i === "k1"))),
  }), api);
  assertEquals(b.status, "ok");
  assertEquals(b.writing!.map((w) => w.external_id).sort(), ["c2", "c3", "r1"]);
  assert(!seen.includes("/comments?a_id=1&per_page=1000"), "unchanged article: no tree request");
  assert(!seen.includes("/comments/c2") && !seen.includes("/comments/k1"), "found in a tree / already stored: not fetched");
  assertEquals(b.stats!.foreign, 1);
  assertEquals((b.state as { counts: Record<string, number> }).counts["9"], 2);
  assertEquals(b.writing!.find((w) => w.external_id === "r1")!.context, 'Comment on "Cron"');
});

// ------------------------------------------------------------------ GitHub folder
const T = (path: string, sha: string, size = 1000) => ({ path, type: "blob", sha, size });

Deno.test("GitHub plan: only the folder's text files, unchanged SHAs skipped, size and run caps", () => {
  const tree = [
    T("README.md", "r"), T("hearback/a.md", "a1"), T("hearback/b.md", "b2"), T("hearback/deep/c.txt", "c1"),
    T("hearback/img.png", "p"), T("hearback/huge.md", "h", 500_000), T("hearbackish/x.md", "x"),
    { path: "hearback/deep", type: "tree", sha: "t" },
  ];
  const plan = planGithubSync(tree, "hearback/", { "hearback/a.md": "a1", "hearback/b.md": "OLD" });
  assertEquals(plan.read.map((f) => f.path), ["hearback/b.md", "hearback/deep/c.txt"]);
  assertEquals(plan.unchanged, ["hearback/a.md"]);
  assertEquals(plan.skipped, [{ path: "hearback/huge.md", reason: "too_large" }]);
  const capped = planGithubSync(Array.from({ length: 30 }, (_, i) => T(`hearback/${String(i).padStart(2, "0")}.md`, `s${i}`)), "hearback", {},
    { ...GITHUB_CAPS, maxChangedPerRun: 5 });
  assertEquals(capped.read.length, 5);
  assertEquals(capped.skipped.filter((s) => s.reason === "run_file_cap").length, 25);
  const bytes = planGithubSync([T("hearback/1.md", "1", 90_000), T("hearback/2.md", "2", 90_000)], "hearback", {}, { ...GITHUB_CAPS, maxRunBytes: 100_000 });
  assertEquals(bytes.skipped, [{ path: "hearback/2.md", reason: "run_byte_cap" }]);
  assertEquals(planGithubSync(tree, "", {}).read.map((f) => f.path).includes("README.md"), true, "empty folder = repo root");
});

Deno.test("GitHub file → paragraphs (or --- separated messages) as candidates; short bits, code and headings skipped", () => {
  const md = "---\ntitle: x\n---\n# How I answer\n\nShort line.\n\nWhen someone asks about pricing I say plainly that it is free while in beta, and that I will ask before anything changes.\n\n```\ncode block that is long enough to have more than fifteen words in it for sure yes indeed\n```\n\n| a | b |\n";
  const meta = { repo: "o/r", path: "hearback/answers.md", url: "https://github.com/o/r/blob/main/hearback/answers.md", date: "2026-09-01T00:00:00Z" };
  const w = writingFromFile(md, meta);
  assertEquals(w.length, 1);
  assert(w[0].text.startsWith("When someone asks about pricing"));
  assertEquals(w[0].context, 'From "x" (hearback/answers.md)', "front-matter title first");
  assertEquals(writingFromFile(md, meta)[0].external_id, w[0].external_id, "stable id");
  const msgs = "First message: I usually reply within a day, and I like to ask what they tried before suggesting anything at all.\n\n---\n\nSecond message: thanks for the bug report, I reproduced it on Safari and the fix ships with the next release tonight.\n";
  assertEquals(writingFromFile(msgs, { ...meta, path: "hearback/messages.txt" }).length, 2);
});

/** fetch stub: path → [status, body, headers]. */
function fakeFetch(routes: Record<string, [number, unknown, Record<string, string>?]>) {
  const calls: { url: string; inm?: string }[] = [];
  const f = (input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    const h = new Headers(init?.headers);
    calls.push({ url, inm: h.get("if-none-match") ?? undefined });
    const key = Object.keys(routes).find((k) => url.endsWith(k));
    if (!key) return Promise.resolve(new Response("nope", { status: 404 }));
    const [status, body, headers] = routes[key];
    const ok = status === 304 ? null : typeof body === "string" ? body : JSON.stringify(body);
    return Promise.resolve(new Response(ok, { status, headers: headers ?? {} }));
  };
  return { f: f as typeof fetch, calls };
}

Deno.test("GitHub source: reads changed files once, ETag 304 on an unchanged head skips the run, private repo needs sign-in, rate limit stops", async () => {
  const para = "When someone asks about pricing I say plainly that it is free while in beta, and that I will ask before anything changes.";
  const routes: Record<string, [number, unknown, Record<string, string>?]> = {
    "/repos/o/r": [200, { default_branch: "main" }, { etag: '"m1"' }],
    "/repos/o/r/commits/main": [200, "HEADSHA", { etag: '"h1"' }],
    "/repos/o/r/git/trees/HEADSHA?recursive=1": [200, { tree: [T("hearback/a.md", "a1", 200), T("hearback/b.md", "b1", 200)] }],
    "/o/r/HEADSHA/hearback/a.md": [200, `# A\n\n${para}`],
    "/o/r/HEADSHA/hearback/b.md": [200, `# B\n\n${para} Also b.`],
    "commits?path=hearback%2Fa.md&sha=main&per_page=1": [200, [{ commit: { committer: { date: "2026-09-05T00:00:00Z" } } }]],
    "commits?path=hearback%2Fb.md&sha=main&per_page=1": [200, [{ commit: { committer: { date: "2026-09-06T00:00:00Z" } } }]],
  };
  const project = { id: "p", github_repo: "o/r", github_folder: "hearback" };
  const one = fakeFetch(routes);
  const b1 = await githubFolderSource(project, ctx(), one.f);
  assertEquals(b1.status, "ok");
  assertEquals(b1.documents!.map((d) => d.url), ["https://github.com/o/r/blob/main/hearback/a.md", "https://github.com/o/r/blob/main/hearback/b.md"]);
  assertEquals(b1.documents![0].published_at, "2026-09-05T00:00:00Z");
  assertEquals(b1.writing!.length, 2);
  // Second run: the head answers 304 → nothing read.
  const two = fakeFetch({ ...routes, "/repos/o/r/commits/main": [304, null], "/repos/o/r": [304, null] });
  const b2 = await githubFolderSource(project, ctx({ state: b1.state! }), two.f);
  assertEquals(b2.documents, undefined);
  assertEquals(two.calls.find((c) => c.url.endsWith("/commits/main"))?.inm, '"h1"');
  assertEquals(two.calls.length, 2);
  // New head, one file changed → only that file is read.
  const three = fakeFetch({
    ...routes, "/repos/o/r/commits/main": [200, "NEW", { etag: '"h2"' }],
    "/repos/o/r/git/trees/NEW?recursive=1": [200, { tree: [T("hearback/a.md", "a1", 200), T("hearback/b.md", "b2", 200)] }],
    "/o/r/NEW/hearback/b.md": [200, `# B\n\n${para} Changed.`],
  });
  const b3 = await githubFolderSource(project, ctx({ state: b2.state! }), three.f);
  assertEquals(b3.documents!.map((d) => d.title), ["B"]);
  assertEquals(b3.stats!.unchanged, 1);
  // Private or missing.
  const priv = await githubFolderSource({ id: "p", github_repo: "o/secret" }, ctx(), fakeFetch({}).f);
  assertEquals(priv.status, "needs_auth");
  assert(priv.message!.includes("Connect GitHub"));
  // Rate limited.
  const rl = await githubFolderSource(project, ctx(), fakeFetch({ "/repos/o/r": [403, "limit", { "x-ratelimit-remaining": "0", "x-ratelimit-reset": "1791600000" }] }).f);
  assertEquals(rl.status, "rate_limited");
  assertEquals((await githubFolderSource({ id: "p" }, ctx(), one.f)).status, "empty");
});

// ------------------------------------------------------------------ knowledge
Deno.test("knowledge ingest is idempotent: unchanged hash = no write, same text from another source = relabel only", async () => {
  const doc = { kind: "article" as const, title: "T", url: "https://x/a", published_at: "2026-09-01T00:00:00Z", markdown: "# T\n\nbody" };
  const sha = await docSha(doc);
  assertEquals(sha, await docSha({ ...doc }), "stable");
  assert(sha !== await docSha({ ...doc, markdown: "# T\n\nbody2" }));
  const first = planDocs([], [{ url: doc.url, sha, source: "devto" }]);
  assertEquals(first, { write: [doc.url], relabel: [], unchanged: [] });
  const again = planDocs([{ url: doc.url, content_sha256: sha, source: "devto" }], [{ url: doc.url, sha, source: "devto" }]);
  assertEquals(again, { write: [], relabel: [], unchanged: [doc.url] });
  const seed = planDocs([{ url: doc.url, content_sha256: null, source: "seed" }], [{ url: doc.url, sha, source: "devto" }]);
  assertEquals(seed.write, [doc.url], "a seed document without a hash is rewritten by the pipeline");
  const moved = planDocs([{ url: doc.url, content_sha256: sha, source: "seed" }], [{ url: doc.url, sha, source: "landing" }, { url: doc.url, sha, source: "github" }]);
  assertEquals(moved, { write: [], relabel: [doc.url], unchanged: [] });
});

Deno.test("site links: same host only, shallow first, assets and auth pages skipped, capped", () => {
  const html = `<a href="/s/2026-a">a</a><a href="https://www.site.dev/about">about</a><a href="/feed.xml">f</a>
    <a href="https://other.dev/x">x</a><a href="/login">l</a><a href="/s/2026-b#top">b</a><a href="/s/2026-a?ref=1">dup</a><a href="/">home</a>`;
  assertEquals(sameSiteLinks(html, "https://site.dev/"), ["https://www.site.dev/about", "https://site.dev/s/2026-a", "https://site.dev/s/2026-b"]);
  assertEquals(sameSiteLinks(html, "https://site.dev/", 1), ["https://www.site.dev/about"]);
});

Deno.test("site page date: meta first, then JSON-LD; date-only values stay day precision", async () => {
  const { metaDate } = await import("./site.ts");
  assertEquals(metaDate('<meta property="article:published_time" content="2026-09-01T10:00:00Z">'), "2026-09-01T10:00:00.000Z");
  assertEquals(metaDate('<script type="application/ld+json">{"datePublished": "2026-10-02"}</script>'), "2026-10-02");
  assertEquals(metaDate("<p>no date</p>"), null);
});
