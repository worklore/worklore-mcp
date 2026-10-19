// Offline tests for the pure parts of the server functions.
//   deno test supabase/functions/_shared/

import { assert, assertEquals, assertThrows } from "jsr:@std/assert@1";
import { detectFacets, normaliseHandle } from "../connectors/bluesky/client.ts";
import { threadContext } from "../connectors/bluesky/connector.ts";
import { flattenTree, parseIngestItem } from "../connectors/devto/parse.ts";
import { checksOf, intentNote } from "../core/draft_run.ts";
import { ideaQuestions } from "../core/ideas.ts";
import { privacyFlags } from "./knowledge.ts";
import { isRunnableSpec, modelFounderFor, PlanRow, resolveDraftModel } from "./models.ts";
import { extractPage, isPrivateIp, normaliseUrl, parseLandingJson } from "./landing.ts";
import { clampGraphemes, firstSentence, graphemeLength, htmlToText, markdownToText, topicScore } from "./text.ts";

Deno.test("graphemes: emoji and flags count as one; clamp ends at a sentence", () => {
  assertEquals(graphemeLength("héllo 👋🏽 🇦🇷"), 9);
  const long = "First sentence here. " + "word ".repeat(80);
  const cut = clampGraphemes(long, 60);
  assert(graphemeLength(cut) <= 60);
  const s = "One two three. Four five six seven eight nine ten eleven twelve.";
  assertEquals(clampGraphemes(s, 30), "One two three.");
  assertEquals(clampGraphemes("short", 300), "short");
});

Deno.test("firstSentence and topicScore", () => {
  assertEquals(firstSentence("I'd pay for this. Really."), "I'd pay for this.");
  assert(topicScore("Building AI agents with Claude Code", ["ai agents", "claude code"]) >= 4);
  assertEquals(topicScore("cooking pasta", ["mcp", "ai agents"]), 0);
});

Deno.test("SSRF guard: private and reserved addresses are blocked", () => {
  for (const ip of ["127.0.0.1", "10.1.2.3", "172.16.0.1", "172.31.255.255", "192.168.1.1", "169.254.169.254", "100.64.0.1", "0.0.0.0", "::1", "fd00::1", "fe80::1", "::ffff:127.0.0.1", "224.0.0.1"]) {
    assert(isPrivateIp(ip), ip);
  }
  for (const ip of ["8.8.8.8", "172.32.0.1", "104.18.2.3", "2606:4700::1111"]) assert(!isPrivateIp(ip), ip);
});

Deno.test("normaliseUrl", () => {
  assertEquals(normaliseUrl("patchwork.dev"), "https://patchwork.dev/");
  assertEquals(normaliseUrl("http://x.io/a?b=1"), "http://x.io/a?b=1");
  assertEquals(normaliseUrl("patchwork"), null);
  assertEquals(normaliseUrl("ftp://x.io"), null);
  assertEquals(normaliseUrl("https://x.io:8080"), null);
  assertEquals(normaliseUrl("https://user:pw@x.io"), null);
});

Deno.test("extractPage: title, description, favicon, text without scripts", () => {
  const html = `<html><head><title>Patchwork — notes</title><meta name="description" content="Release notes from commits">
    <link rel="icon" href="/fav.png"><script>var x = 1;</script></head><body><h1>Ship notes</h1><p>For solo devs &amp; teams.</p></body></html>`;
  const ex = extractPage(html, "https://patchwork.dev/");
  assertEquals(ex.title, "Patchwork — notes");
  assertEquals(ex.description, "Release notes from commits");
  assertEquals(ex.favicon, "https://patchwork.dev/fav.png");
  assert(ex.text.includes("For solo devs & teams."));
  assert(!ex.text.includes("var x"));
});

Deno.test("parseLandingJson cleans lists", () => {
  const r = parseLandingJson('```json\n{"name":"P","one_liner":"x","audience":["A","A"," B "],"topics":["t1"],"competitors":null}\n```', "fb");
  assertEquals(r.audience, ["A", "B"]);
  assertEquals(r.competitors, []);
  assertEquals(parseLandingJson('{"name":""}', "fallback").name, "fallback");
});

Deno.test("dev.to tree: ancestors, her replies mark answered, deleted nodes skipped", () => {
  const tree = [{
    id_code: "a1", created_at: "2026-10-01T10:00:00Z", body_html: "<p>Does it support X?</p>", user: { username: "sam", name: "Sam" },
    children: [
      { id_code: "a2", created_at: "2026-10-01T11:00:00Z", body_html: "<p>Yes</p>", user: { username: "yahhi" }, children: [
        { id_code: "a3", created_at: "2026-10-01T12:00:00Z", body_html: "<p>Thanks!</p>", user: { username: "sam" }, children: [] },
      ] },
      { id_code: "a4", created_at: "2026-10-01T12:00:00Z", body_html: "[deleted]", children: [] },
    ],
  }];
  const out = flattenTree({ id: 7, title: "T", url: "https://dev.to/yahhi/t", description: "d" }, "yahhi", tree);
  assertEquals(out.map((c) => c.id_code), ["a1", "a2", "a3"]);
  assertEquals(out[0].answered_by_owner, true);
  assertEquals(out[2].answered_by_owner, false);
  assertEquals(out[2].thread!.map((m) => m.author), ["sam", "yahhi"]);
  assertEquals(out[2].parent?.id_code, "a2");
  assertEquals(out[2].top_id_code, "a1");
  assertEquals(out[0].url, "https://dev.to/sam/comment/a1");
  assertEquals([out[0].under_owner, out[2].under_owner], [false, true]);
  assertEquals([out[0].kind, out[2].kind], ["comment", "reply"]);
});

Deno.test("parseIngestItem: formats and validation", () => {
  const base = { id_code: "3h0h7", text: "**Nice** [link](https://x.io)", created_at: "2026-10-08T12:00:00Z", author: { username: "@sid" },
    article: { id: 1, title: "A", url: "https://dev.to/yahhi/a" } };
  const p = parseIngestItem(base);
  assertEquals(p.text, "Nice link (https://x.io)");
  assertEquals(p.author.username, "sid");
  assertEquals(p.url, "https://dev.to/sid/comment/3h0h7");
  assertEquals(parseIngestItem({ ...base, text: "<p>Hi &amp; bye</p>", text_format: "html" }).text, "Hi & bye");
  assertThrows(() => parseIngestItem({ ...base, id_code: "../x" }));
  assertThrows(() => parseIngestItem({ ...base, text: " " }));
  assertThrows(() => parseIngestItem({ ...base, created_at: "nope" }));
});

Deno.test("html/markdown to text", () => {
  assertEquals(htmlToText('<p>See <a href="https://a.b">https://a.b</a></p>'), "See https://a.b");
  assertEquals(markdownToText("## Title\n\n![img](x.png) text"), "Title\n\n text");
});

Deno.test("Bluesky facets use UTF-8 byte offsets", () => {
  const text = "Привет @ana.bsky.social see https://worklore.dev/s/x.";
  const f = detectFacets(text);
  assertEquals(f.mentions[0].handle, "ana.bsky.social");
  const bytes = new TextEncoder().encode(text);
  const dec = (s: number, e: number) => new TextDecoder().decode(bytes.slice(s, e));
  assertEquals(dec(f.mentions[0].start, f.mentions[0].end), "@ana.bsky.social");
  assertEquals(f.links[0].uri, "https://worklore.dev/s/x");
  assertEquals(dec(f.links[0].start, f.links[0].end), "https://worklore.dev/s/x");
});

Deno.test("normaliseHandle", () => {
  assertEquals(normaliseHandle("@Ana"), "ana.bsky.social");
  assertEquals(normaliseHandle("ana.builds.dev"), "ana.builds.dev");
});

Deno.test("threadContext: root, chain without root, answered", () => {
  const thread = {
    post: { uri: "at://c" },
    parent: { post: { uri: "at://b", author: { did: "did:me", handle: "me" }, record: { text: "B", createdAt: "2" } },
      parent: { post: { uri: "at://a", author: { did: "did:x", handle: "x" }, record: { text: "A", createdAt: "1" } } } },
    replies: [{ post: { author: { did: "did:me" } } }],
  };
  const ctx = threadContext(thread, "did:me");
  assertEquals(ctx.root.uri, "at://a");
  assertEquals(ctx.chain, [{ author: "me", text: "B", posted_at: "2", is_owner: true }]);
  assertEquals(ctx.answered, true);
});

Deno.test("intentNote and checksOf", () => {
  assertEquals(intentNote("auto", { name: "P" }), null);
  assert(intentNote("invite_to_try", { name: "P", url: "https://p.dev" })!.includes("https://p.dev"));
  assert(intentNote("just_answer", { name: "P" }, "say thanks")!.includes("What she wants to say: say thanks"));
  assertEquals(checksOf(["[check: did you try X?]", "[CHECK:  y ]"]), ["did you try X?", "y"]);
});

Deno.test("ideaQuestions maps options to idea ids", () => {
  const { questions, optionToId } = ideaQuestions([{ id: "u1", title: "Export to Markdown" }]);
  assertEquals(optionToId.idea_1, "u1");
  const q = questions.same_as;
  assert(q.type === "choice" && "new" in q.criteria && "idea_1" in q.criteria);
});

Deno.test("privacyFlags", () => {
  assertEquals(privacyFlags("write to me at someone@example.com"), ["email"]);
  assertEquals(privacyFlags("npm i pkg@1.2.3"), []);
  assertEquals(privacyFlags("run aws ssm get-parameter"), ["secret-like"]);
});

Deno.test("draft model resolution: override → plan default → env", () => {
  const founderPlan: PlanRow = {
    id: "founder", default_model: "anthropic:claude-sonnet-5-5",
    allowed_models: ["gemini:gemini-3.1-flash-lite", "anthropic:claude-haiku-5-5", "anthropic:claude-sonnet-5-5", "anthropic:claude-opus-5-5"],
  };
  const free: PlanRow = { id: "free", default_model: "gemini:gemini-3.1-flash-lite", allowed_models: ["gemini:gemini-3.1-flash-lite", "anthropic:claude-haiku-5-5"] };
  const env = "anthropic:claude-haiku-5-5";

  // Her own pick, allowed by her plan.
  let c = resolveDraftModel({ id: "u1", plan_id: "founder", draft_model: "anthropic:claude-opus-5-5" }, founderPlan, env);
  assertEquals([c.spec, c.reason, c.founder_id, c.plan_id], ["anthropic:claude-opus-5-5", "override", "u1", "founder"]);
  // No pick → the plan's default.
  c = resolveDraftModel({ id: "u1", plan_id: "founder", draft_model: null }, founderPlan, env);
  assertEquals([c.spec, c.reason], ["anthropic:claude-sonnet-5-5", "plan default"]);
  // A pick the plan doesn't allow (plan changed, or a stale row) → the plan default, never the pick.
  c = resolveDraftModel({ id: "u2", plan_id: "free", draft_model: "anthropic:claude-opus-5-5" }, free, env);
  assertEquals([c.spec, c.reason], ["gemini:gemini-3.1-flash-lite", "plan default"]);
  // An allowed but unpriced Claude model is never run.
  c = resolveDraftModel({ id: "u3", plan_id: "x", draft_model: "anthropic:claude-fable-9" },
    { id: "x", default_model: "anthropic:claude-haiku-5-5", allowed_models: ["anthropic:claude-fable-9", "anthropic:claude-haiku-5-5"] }, env);
  assertEquals([c.spec, c.reason], ["anthropic:claude-haiku-5-5", "plan default"]);
  // No founder/plan (a project without one) → env, then the built-in default.
  c = resolveDraftModel(null, null, env);
  assertEquals([c.spec, c.reason, c.founder_id], [env, "env", null]);
  assertEquals(resolveDraftModel(null, null, "").spec, "gemini:gemini-3.1-flash-lite");
  // A plan with a broken default → env.
  c = resolveDraftModel({ id: "u4", plan_id: "y" }, { id: "y", default_model: "openai:gpt-6", allowed_models: ["openai:gpt-6"] }, env);
  assertEquals([c.spec, c.reason], [env, "env"]);
});

Deno.test("whose model: requester, else assignee, else owner", () => {
  assertEquals(modelFounderFor({ requestedBy: "a", assignedTo: "b", owner: "c" }), "a");
  assertEquals(modelFounderFor({ requestedBy: null, assignedTo: "b", owner: "c" }), "b");
  assertEquals(modelFounderFor({ requestedBy: null, assignedTo: null, owner: "c" }), "c");
  assertEquals(modelFounderFor({}), null);
  assert(isRunnableSpec("gemini:gemini-3.1-flash-lite") && isRunnableSpec("anthropic:claude-opus-5-5"));
  assert(!isRunnableSpec("anthropic:claude-fable-9") && !isRunnableSpec("") && !isRunnableSpec(null));
});
