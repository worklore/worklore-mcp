// GitHub App: state tokens and the setup handler (install, update without a
// state, bad / expired / used state, someone else's installation), the issue
// body, the duplicate search, labels, token minting (mocked GitHub) and the
// GitHub source with an installation token.
//   deno test -A supabase/functions/_shared/

import { assert, assertEquals, assertNotEquals, assertRejects } from "jsr:@std/assert@1";
import { appJwt, GithubApp, importAppKey, InstallationRepo, manageUrl, RawInstallation, TOKEN_TTL_MS } from "./app.ts";
import { githubFolderSource } from "./connector.ts";
import { handleSetup, hashState, InstallationRow, InstallStore, newStateToken, setupRedirect, StateRow } from "./install.ts";
import { duplicateQueries, issueBody, issueComment, issueNumberFromUrl, neutralize, parseDuplicates, pickLabels, titleWords } from "./issues.ts";

// ------------------------------------------------------------------ fixtures

const NOW = new Date("2026-10-10T12:00:00Z");
const iso = (msFromNow: number) => new Date(NOW.getTime() + msFromNow).toISOString();
const repo = (full_name: string, priv = false): InstallationRepo => ({
  full_name, private: priv, default_branch: "main", open_issues: 3, pushed_at: iso(-86_400_000), description: null, archived: false, has_issues: true,
});
const rawInst = (id: number, over: Partial<RawInstallation> = {}): RawInstallation => ({
  id, account: { login: "worklore", id: 900, type: "Organization" }, repository_selection: "selected",
  created_at: iso(-60_000), updated_at: iso(-60_000), suspended_at: null, ...over,
});

/** In-memory InstallStore with a few founders and projects. */
function memStore(opts: { members?: Record<string, string[]>; githubIds?: Record<string, number> } = {}) {
  const states = new Map<string, StateRow>();
  const installs = new Map<number, InstallationRow>();
  const links: { installation_id: number; project_id: string; founder_id: string }[] = [];
  const store: InstallStore = {
    findState: (h) => Promise.resolve(states.get(h) ?? null),
    consumeState: (h, nowIso) => {
      const s = states.get(h);
      if (!s || s.used_at || s.expires_at <= nowIso) return Promise.resolve(null);
      s.used_at = nowIso;
      return Promise.resolve({ ...s });
    },
    getInstallation: (id) => Promise.resolve(installs.get(id) ?? null),
    upsertInstallation: (row) => { installs.set(row.installation_id, row); return Promise.resolve(); },
    linkProject: (installation_id, project_id, founder_id) => {
      if (!links.some((l) => l.installation_id === installation_id && l.project_id === project_id)) links.push({ installation_id, project_id, founder_id });
      return Promise.resolve();
    },
    memberOfLinkedProject: (id, founder) =>
      Promise.resolve(links.some((l) => l.installation_id === id && (opts.members?.[l.project_id] ?? []).includes(founder))),
    founderGithubId: (f) => Promise.resolve(opts.githubIds?.[f] ?? null),
  };
  async function addState(founder: string, project: string, over: Partial<StateRow> = {}) {
    const { token, hash } = await newStateToken();
    states.set(hash, { founder_id: founder, project_id: project, client: "app", expires_at: iso(15 * 60_000), used_at: null, ...over });
    return token;
  }
  return { store, states, installs, links, addState };
}

function fakeGh(insts: Record<number, RawInstallation>, repos: Record<number, InstallationRepo[]>) {
  const calls: string[] = [];
  return {
    calls,
    installation: (id: number) => { calls.push(`inst:${id}`); return Promise.resolve(insts[id] ?? null); },
    repos: (id: number) => { calls.push(`repos:${id}`); return Promise.resolve(repos[id] ?? []); },
  };
}

const q = (o: Record<string, string>) => new URLSearchParams(o);

// ------------------------------------------------------------------ state + setup

Deno.test("state token: random, 43 chars, only the hash is stored and it is stable", async () => {
  const a = await newStateToken(), b = await newStateToken();
  assertEquals(a.token.length, 43);
  assert(/^[A-Za-z0-9_-]+$/.test(a.token));
  assertNotEquals(a.token, b.token);
  assertEquals(a.hash, await hashState(a.token));
  assertEquals(a.hash.length, 64);
  assert(!a.hash.includes(a.token));
});

Deno.test("setup: install with a fresh state stores the installation + repos, links the project, single use", async () => {
  const m = memStore();
  const token = await m.addState("f1", "p1");
  const gh = fakeGh({ 7: rawInst(7) }, { 7: [repo("worklore/worklore")] });
  const o = await handleSetup(q({ installation_id: "7", setup_action: "install", state: token }), m.store, gh, NOW);
  assert(o.ok);
  assertEquals(o.project_id, "p1");
  assertEquals(o.repos, 1);
  assertEquals(m.installs.get(7)!.founder_id, "f1");
  assertEquals(m.installs.get(7)!.account_login, "worklore");
  assertEquals(m.installs.get(7)!.repos[0].full_name, "worklore/worklore");
  assertEquals(m.links, [{ installation_id: 7, project_id: "p1", founder_id: "f1" }]);
  assertEquals(setupRedirect(o), "dev.hearback.app://github-installed?ok=1&installation_id=7");
  // The same link again: used.
  const again = await handleSetup(q({ installation_id: "7", setup_action: "install", state: token }), m.store, gh, NOW);
  assertEquals(again, { ok: false, client: "app", reason: "used_state" });
  assert(setupRedirect(again).startsWith("https://hearback.dev/github-installed.html?ok=0&client=app&reason=used_state"));
});

Deno.test("setup: bad, expired and missing state; org approval request", async () => {
  const m = memStore();
  const gh = fakeGh({ 7: rawInst(7) }, { 7: [] });
  assertEquals(await handleSetup(q({ installation_id: "7", setup_action: "install", state: "forged" }), m.store, gh, NOW),
    { ok: false, client: null, reason: "bad_state" });
  const old = await m.addState("f1", "p1", { expires_at: iso(-1) });
  assertEquals((await handleSetup(q({ installation_id: "7", setup_action: "install", state: old }), m.store, gh, NOW)), { ok: false, client: "app", reason: "expired_state" });
  assertEquals((await handleSetup(q({ installation_id: "7", setup_action: "install" }), m.store, gh, NOW)), { ok: false, client: null, reason: "missing_state" });
  const web = await m.addState("f1", "p1", { client: "web" });
  assertEquals((await handleSetup(q({ setup_action: "request", state: web }), m.store, gh, NOW)), { ok: false, client: "web", reason: "requested" });
  const bad = await m.addState("f1", "p1");
  assertEquals((await handleSetup(q({ installation_id: "x7", state: bad }), m.store, gh, NOW)).ok, false);
  assertEquals(gh.calls, [], "GitHub is not asked for bad input");
  assertEquals(m.installs.size, 0);
});

Deno.test("setup: update without state refreshes a known installation only", async () => {
  const m = memStore();
  const gh = fakeGh({ 7: rawInst(7, { repository_selection: "all" }) }, { 7: [repo("worklore/worklore"), repo("worklore/site")] });
  // Unknown installation: nothing stored.
  assertEquals(await handleSetup(q({ installation_id: "7", setup_action: "update" }), m.store, gh, NOW), { ok: false, client: null, reason: "unknown_installation" });
  const token = await m.addState("f1", "p1");
  await handleSetup(q({ installation_id: "7", setup_action: "install", state: token }), m.store, fakeGh({ 7: rawInst(7) }, { 7: [repo("worklore/worklore")] }), NOW);
  const o = await handleSetup(q({ installation_id: "7", setup_action: "update" }), m.store, gh, NOW);
  assert(o.ok && o.refreshed_only);
  assertEquals(m.installs.get(7)!.repos.length, 2);
  assertEquals(m.installs.get(7)!.repository_selection, "all");
  assertEquals(m.installs.get(7)!.founder_id, "f1", "owner kept");
  assertEquals(m.links.length, 1, "no new link");
  assert(setupRedirect(o).startsWith("https://hearback.dev/github-installed.html?ok=1"));
});

Deno.test("setup: someone else's installation is never taken; an old unclaimed one only by its GitHub user", async () => {
  const m = memStore({ members: { p2: ["f2", "f3"] }, githubIds: { f4: 555 } });
  const t1 = await m.addState("f1", "p1");
  const gh = fakeGh({ 7: rawInst(7), 8: rawInst(8, { created_at: iso(-3 * 3600_000), updated_at: iso(-3 * 3600_000), account: { login: "ana", id: 555, type: "User" } }) },
    { 7: [repo("worklore/worklore")], 8: [repo("ana/x")] });
  assert((await handleSetup(q({ installation_id: "7", state: t1 }), m.store, gh, NOW)).ok);
  // f2 pastes installation 7 with her own valid state.
  const t2 = await m.addState("f2", "p2");
  assertEquals((await handleSetup(q({ installation_id: "7", state: t2 }), m.store, gh, NOW)), { ok: false, client: "app", reason: "not_yours" });
  assertEquals(m.links.length, 1);
  // f1 links the same installation to a second project of hers: fine.
  const t3 = await m.addState("f1", "p3");
  assert((await handleSetup(q({ installation_id: "7", setup_action: "update", state: t3 }), m.store, gh, NOW)).ok);
  assertEquals(m.links.length, 2);
  // Old unclaimed installation: refused for f1, accepted for the GitHub user it is installed on.
  const t4 = await m.addState("f1", "p1");
  assertEquals((await handleSetup(q({ installation_id: "8", state: t4 }), m.store, gh, NOW)).ok, false);
  const t5 = await m.addState("f4", "p4");
  assert((await handleSetup(q({ installation_id: "8", state: t5 }), m.store, gh, NOW)).ok);
});

Deno.test("setup: GitHub down or the id unknown to GitHub", async () => {
  const m = memStore();
  const t = await m.addState("f1", "p1");
  assertEquals((await handleSetup(q({ installation_id: "9", state: t }), m.store, fakeGh({}, {}), NOW)).ok, false);
  const t2 = await m.addState("f1", "p1");
  const down = { installation: () => Promise.reject(new Error("503")), repos: () => Promise.resolve([]) };
  assertEquals((await handleSetup(q({ installation_id: "9", state: t2 }), m.store, down, NOW)), { ok: false, client: "app", reason: "github_error" });
});

Deno.test("manage URL: personal settings vs the org's", () => {
  assertEquals(manageUrl({ installation_id: 5, account_login: "ana", account_type: "User" }), "https://github.com/settings/installations/5");
  assertEquals(manageUrl({ installation_id: 5, account_login: "worklore", account_type: "Organization" }),
    "https://github.com/organizations/worklore/settings/installations/5");
});

// ------------------------------------------------------------------ issues

const asks = [
  { name: "Jonas Weber", text: "I'd pay for this if it exported straight to Markdown in the repo.\nCopy-pasting is where I give up. cc @octocat see #12", url: "https://dev.to/jonas/comment/3h0h7", platform: "devto" },
  { name: "Sam Lee", text: "Markdown export into the repo please", url: "https://bsky.app/profile/sam.bsky.social/post/abc", platform: "bluesky" },
];

Deno.test("issue body: summary, each person's words quoted with a link, theme, source line; no pings", () => {
  const body = issueBody({ title: "Export release notes to CHANGELOG.md", summary: "Users want notes written to the repo.", kind: "feature", themes: [] }, asks);
  assert(body.startsWith("Users want notes written to the repo."));
  assert(body.includes("> I'd pay for this if it exported straight to Markdown in the repo.\n> Copy-pasting"));
  assert(body.includes("> — Jonas Weber on [dev.to](https://dev.to/jonas/comment/3h0h7)"));
  assert(body.includes("> — Sam Lee on [Bluesky](https://bsky.app/profile/sam.bsky.social/post/abc)"));
  assert(body.includes("**Theme:** Feature idea"));
  assert(body.includes("**Asked by:** 2 people"));
  assert(body.trimEnd().endsWith("_Created from [Hearback](https://hearback.dev)._"));
  assert(!body.includes("@octocat"), "no @mention");
  assert(!/\s#12\b/.test(body), "no cross-reference");
  const themed = issueBody({ title: "t", summary: null, kind: "bug", themes: ["Export", "Docs"] }, [asks[0]]);
  assert(themed.includes("**Theme:** Export, Docs"));
  assert(themed.includes("**Asked by:** 1 person"));
  assert(themed.startsWith("### What people said"));
  const long = issueBody({ title: "t", summary: null, kind: "other", themes: [] }, [{ ...asks[0], text: "word ".repeat(400), url: null }]);
  assert(long.includes(" …"));
  assert(long.includes("> — Jonas Weber on dev.to"));
  assert(issueComment(asks).startsWith("2 more people asked for this:"));
  assertEquals(neutralize("@a #1 x#2"), "@​a #​1 x#2");
});

Deno.test("duplicate search: specific title words, two queries, ranked open issues only", () => {
  assertEquals(titleWords("Export release notes to CHANGELOG.md in the repo"), ["changelog.md", "release", "export", "notes", "repo"]);
  assertEquals(duplicateQueries("o/r", "Export release notes to CHANGELOG.md"), [
    "repo:o/r is:issue is:open in:title changelog.md release export",
    "repo:o/r is:issue is:open in:title changelog.md release",
  ]);
  assertEquals(duplicateQueries("o/r", "Add a way to"), []);
  const json = {
    total_count: 4,
    items: [
      { number: 38, title: "Export release notes as Markdown", html_url: "https://github.com/o/r/issues/38", state: "open", comments: 2 },
      { number: 40, title: "PR: export notes", html_url: "https://github.com/o/r/pull/40", state: "open", pull_request: {} },
      { number: 12, title: "Unrelated crash on start", html_url: "https://github.com/o/r/issues/12", state: "open" },
      { number: 41, title: "Release notes export to changelog.md", html_url: "https://github.com/o/r/issues/41", state: "open" },
      { bogus: true },
    ],
  };
  const d = parseDuplicates(json, "Export release notes to CHANGELOG.md");
  assertEquals(d.map((x) => x.number), [41, 38]);
  assertEquals(d[1].comments, 2);
  assertEquals(parseDuplicates({ message: "Validation Failed" }, "x"), []);
  assertEquals(parseDuplicates(null, "x"), []);
});

Deno.test("labels: only existing ones, the repo's spelling; never invented", () => {
  assertEquals(pickLabels(["Bug", "enhancement", "from-users"], "feature"), ["enhancement", "from-users"]);
  assertEquals(pickLabels(["Bug", "enhancement"], "bug"), ["Bug"]);
  assertEquals(pickLabels([], "feature"), []);
  assertEquals(pickLabels(["question"], "other"), []);
  assertEquals(issueNumberFromUrl("https://github.com/o/r/issues/12"), 12);
  assertEquals(issueNumberFromUrl("https://github.com/o/r/issues/new?title=x"), null);
});

// ------------------------------------------------------------------ token minting

async function testKey() {
  const pair = await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
  const der = new Uint8Array(await crypto.subtle.exportKey("pkcs8", pair.privateKey));
  const b64 = btoa(String.fromCharCode(...der)).replace(/(.{64})/g, "$1\n");
  return { pem: `-----BEGIN PRIVATE KEY-----\n${b64}\n-----END PRIVATE KEY-----\n`, pub: pair.publicKey };
}

Deno.test("app JWT: RS256, iss = app id, iat 60 s back, exp ≤ 10 min, verifies with the public key", async () => {
  const { pem, pub } = await testKey();
  const jwt = await appJwt("12345", await importAppKey(pem), NOW.getTime());
  const [h, c, s] = jwt.split(".");
  const dec = (x: string) => JSON.parse(atob(x.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - x.length % 4) % 4)));
  assertEquals(dec(h), { alg: "RS256", typ: "JWT" });
  const claims = dec(c);
  assertEquals(claims.iss, "12345");
  assertEquals(claims.iat, NOW.getTime() / 1000 - 60);
  assert(claims.exp - claims.iat <= 600);
  const sig = Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - s.length % 4) % 4)), (ch) => ch.charCodeAt(0));
  assert(await crypto.subtle.verify("RSASSA-PKCS1-v1_5", pub, sig, new TextEncoder().encode(`${h}.${c}`)));
  await assertRejects(() => importAppKey("-----BEGIN RSA PRIVATE KEY-----\nAAAA\n-----END RSA PRIVATE KEY-----"), Error, "PKCS#1");
});

Deno.test("installation tokens: minted once, reused under 50 min, re-minted after; a 401 drops the token and retries", async () => {
  const { pem } = await testKey();
  let clock = NOW.getTime();
  let n = 0;
  const seen: { url: string; auth: string; method: string }[] = [];
  let failNext = false;
  const f = (input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    const auth = new Headers(init?.headers).get("authorization") ?? "";
    seen.push({ url, auth, method: init?.method ?? "GET" });
    if (url.endsWith("/access_tokens")) {
      assert(auth.startsWith("Bearer "), "minted with the app JWT");
      return Promise.resolve(Response.json({ token: `tok${++n}`, expires_at: new Date(clock + 3600_000).toISOString() }, { status: 201 }));
    }
    if (failNext) { failNext = false; return Promise.resolve(new Response("bad creds", { status: 401 })); }
    return Promise.resolve(Response.json({ total_count: 1, repositories: [{ full_name: "o/r", private: true }] }));
  };
  const app = new GithubApp({ appId: "1", privateKeyPem: pem }, f as typeof fetch, () => clock);
  assertEquals(await app.installationToken(7), "tok1");
  clock += TOKEN_TTL_MS - 1000;
  assertEquals(await app.installationToken(7), "tok1");
  clock += 2000;
  assertEquals(await app.installationToken(7), "tok2");
  assertEquals(await app.installationToken(8), "tok3", "per installation");
  failNext = true;
  const repos = await app.installationRepos(7);
  assertEquals(repos[0], { full_name: "o/r", private: true, default_branch: null, open_issues: 0, pushed_at: null, description: null, archived: false, has_issues: true });
  assertEquals(n, 4, "401 → a new token");
  assertEquals(seen.filter((s) => s.url.includes("/installation/repositories")).map((s) => s.auth), ["token tok2", "token tok4"]);
});

// ------------------------------------------------------------------ source with a token

Deno.test("GitHub source with an installation token: private repo readable, contents API, background label", async () => {
  const para = "When someone asks about pricing I say plainly that it is free while in beta, and that I will ask before anything changes.";
  const calls: { url: string; auth: string | null; accept: string | null }[] = [];
  const routes: Record<string, [number, unknown]> = {
    "/repos/o/secret": [200, { default_branch: "main", private: true }],
    "/repos/o/secret/commits/main": [200, "SHA1"],
    "/repos/o/secret/git/trees/SHA1?recursive=1": [200, { tree: [{ path: "hearback/a.md", type: "blob", sha: "a1", size: 200 }] }],
    "/repos/o/secret/contents/hearback/a.md?ref=SHA1": [200, `# A\n\n${para}`],
    "commits?path=hearback%2Fa.md&sha=main&per_page=1": [200, [{ commit: { committer: { date: "2026-09-05T00:00:00Z" } } }]],
  };
  const f = (input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    const h = new Headers(init?.headers);
    calls.push({ url, auth: h.get("authorization"), accept: h.get("accept") });
    const key = Object.keys(routes).find((k) => url.endsWith(k));
    if (!key) return Promise.resolve(new Response("nope", { status: 404 }));
    const [status, body] = routes[key];
    return Promise.resolve(new Response(typeof body === "string" ? body : JSON.stringify(body), { status }));
  };
  const ctx = { state: {}, deadline: Date.now() + 60_000, knownWriting: () => Promise.resolve(new Set<string>()) };
  const b = await githubFolderSource({ id: "p", github_repo: "o/secret" }, ctx, f as typeof fetch, "itok");
  assertEquals(b.status, "ok");
  assertEquals(b.documents!.length, 1);
  assertEquals(b.documents![0].label, "background");
  assertEquals(b.writing!.length, 1, "her words still teach the voice");
  assert(calls.every((c) => c.auth === "token itok"));
  assert(!calls.some((c) => c.url.includes("raw.githubusercontent.com")));
  assertEquals(calls.find((c) => c.url.includes("/contents/"))!.accept, "application/vnd.github.raw");
  // Not in the installation's repos: the message says what to do.
  const none = await githubFolderSource({ id: "p", github_repo: "o/other" }, ctx, f as typeof fetch, "itok");
  assertEquals(none.status, "needs_auth");
  assert(none.message!.includes("Add it to the app's repositories"));
});
