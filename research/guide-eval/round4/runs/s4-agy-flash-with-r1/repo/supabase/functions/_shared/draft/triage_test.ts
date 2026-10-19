// deno test supabase/functions/_shared/draft/   (no network: a stub Decider)
import { assertEquals } from "jsr:@std/assert@1";
import { Decider, Decision, Questions, toAnswer } from "./decide/decider.ts";
import { commentQuestions, decideArticle, isEmojiOnly, painQuote, spamSignals, triageItem } from "./triage.ts";
import type { ItemContext } from "./types.ts";

/** Returns fixed raw answers, the way an adapter would after parsing its API. */
function stub(raw: Record<string, unknown>, notes?: Record<string, string>): Decider {
  return {
    name: "stub", model: "stub",
    decide(_s: unknown, qs: Questions): Promise<Decision> {
      return Promise.resolve({
        answers: Object.fromEntries(Object.entries(qs).map(([id, q]) => [id, toAnswer(q, raw[id])])),
        notes, decider: "stub", model: "stub", usage: { tokens_in: null, tokens_out: null }, latency_ms: 0,
      });
    },
  };
}
const project = { name: "worklore", one_liner: "developer stories agents can reproduce", founder_name: "Valentina", founder_handle: "yahhi" };
const ctx = (text: string): ItemContext => ({ platform: "devto", kind: "reply", post: null, chain: [], item: { author: "x", text } });

Deno.test("feedback always goes to the Decide queue, whatever the decider's action", async () => {
  const r = await triageItem({ project, context: ctx("Could worklore publish the hashes under my key?") }, stub({
    kind: { feedback_for_founder: 0.8, engagement: 0.2 }, action: { draft: 1 }, suggested_action: { act: 0.7, open_issue: 0.3 },
  }, { summary: "Publish the surface hashes under the mcp-surface key" }));
  assertEquals([r.kind, r.code, r.route, r.suggested_action, r.not_sure], ["feedback_for_founder", "a", "decide_queue", "act", false]);
  assertEquals(r.decider_action, "draft");
  assertEquals(r.summary, "Publish the surface hashes under the mcp-surface key");
});

Deno.test("unsure engagement with a real chance of feedback is routed to Decide (safety rule)", async () => {
  const r = await triageItem({ project, context: ctx("The cheap fix I can see is to hash the initialize result too.") }, stub({
    kind: { engagement: 0.55, feedback_for_founder: 0.45 }, action: { draft: 1 }, suggested_action: { open_issue: 1 },
  }));
  assertEquals([r.kind, r.route, r.not_sure, r.suggested_action], ["engagement", "decide_queue", true, "open_issue"]);
});

Deno.test("short thanks is skipped, longer thanks gets a short draft, engagement gets a draft", async () => {
  const thanks = { kind: { thanks: 0.95, engagement: 0.05 }, action: { short_draft: 1 }, suggested_action: { just_thank: 1 } };
  assertEquals((await triageItem({ project, context: ctx("Thanks!") }, stub(thanks))).route, "skip");
  assertEquals((await triageItem({ project, context: ctx("Good guide, I want to try building an MCP server too.") }, stub(thanks))).route, "short_draft");
  const eng = await triageItem({ project, context: ctx("Have you seen agents ignore tool descriptions?") }, stub({ kind: { engagement: 0.9, product_question: 0.1 }, action: { draft: 1 } }));
  assertEquals([eng.route, eng.suggested_action, eng.code], ["draft", null, "b"]);
});

Deno.test("comment questions are the typed choice set the TypeSafe adapter will send", () => {
  const q = commentQuestions(project);
  assertEquals(Object.keys(q), ["kind", "action", "suggested_action", "promotion", "has_the_problem"]);
  assertEquals(q.kind.type === "choice" && Object.keys(q.kind.criteria), ["feedback_for_founder", "engagement", "product_question", "thanks", "ignore"]);
  assertEquals(q.action.type === "choice" && Object.keys(q.action.criteria), ["decide_queue", "draft", "short_draft", "skip"]);
});

Deno.test("article decision keeps probabilities and flags low confidence", async () => {
  const r = await decideArticle({
    project: { ...project, aims: "find developers building MCP servers and agent workflows", audience: "developers with AI agents" },
    article: { title: "Your MCP server changed. Its version didn't.", author: "sidneybissoli", text: "A version number is a promise…" },
  }, stub({ relevant_to_project_aims: 0.9, action: { comment_to_engage: 0.5, flag_for_founder: 0.4, leave: 0.1 } }, { why: "her own drift work" }));
  assertEquals([r.relevant, r.action, r.not_sure, r.p_relevant], [true, "comment_to_engage", true, 0.9]);
});

Deno.test("the decider's skip is respected: no draft for a reaction (Fayaz's 😂)", async () => {
  const r = await triageItem({ project, context: ctx("😂") }, stub({ kind: { engagement: 0.7, thanks: 0.3 }, action: { skip: 0.8, draft: 0.2 } }));
  assertEquals([r.kind, r.route, r.decider_action], ["engagement", "skip", "skip"]);
  // Emoji-only is skipped even when the decider wanted a draft.
  const r2 = await triageItem({ project, context: ctx("🔥🔥") }, stub({ kind: { engagement: 0.9 }, action: { draft: 1 } }));
  assertEquals(r2.route, "skip");
  // A thank-you with substance where the decider says skip: skip.
  const r3 = await triageItem({ project, context: ctx("Thank you for the Habr write-up, and for putting my name next to it.") },
    stub({ kind: { engagement: 0.8, thanks: 0.2 }, action: { skip: 0.7, short_draft: 0.3 } }));
  assertEquals(r3.route, "skip");
});

Deno.test("short_draft stays short_draft; only draft gets a full draft", async () => {
  const short = await triageItem({ project, context: ctx("Capability tier as the verdict, patterns as hints, that's the right split.") },
    stub({ kind: { engagement: 0.9 }, action: { short_draft: 0.8, draft: 0.2 } }));
  assertEquals(short.route, "short_draft");
  const full = await triageItem({ project, context: ctx("How do you keep the fake as strict as production at every depth?") },
    stub({ kind: { engagement: 0.9 }, action: { draft: 0.9 } }));
  assertEquals(full.route, "draft");
});

Deno.test("isEmojiOnly", () => {
  for (const s of ["😂", " 🔥🔥 ", "👍🏽", "+1", "❤️!", "🙌"]) assertEquals(isEmojiOnly(s), true, s);
  for (const s of ["ok 😂", "Thanks!", "10/10"]) assertEquals(isEmojiOnly(s), false, s);
});

Deno.test("has_the_problem: kept with their own words in a conversation, never on feedback", async () => {
  const text = "I keep a notes file of what my agent tried, by hand, every session.";
  const eng = await triageItem({ project, context: ctx(text) }, stub(
    { kind: { engagement: 0.9, thanks: 0.1 }, action: { draft: 1 }, has_the_problem: 0.85 },
    { summary: "keeps agent notes by hand", pain: "a notes file of what my agent tried, by hand" },
  ));
  assertEquals([eng.has_the_problem, eng.pain_quote], [true, "a notes file of what my agent tried, by hand"]);
  const fb = await triageItem({ project, context: ctx(text) }, stub(
    { kind: { feedback_for_founder: 0.9, engagement: 0.1 }, action: { draft: 1 }, has_the_problem: 0.85 },
  ));
  assertEquals([fb.has_the_problem, fb.pain_quote], [false, null]);
});

Deno.test("painQuote drops a paraphrase and keeps an exact (case/space-insensitive) quote", () => {
  const text = "Honestly I  re-run the whole thing by hand every Friday.";
  assertEquals(painQuote('"re-run the whole thing by hand"', text), "re-run the whole thing by hand");
  assertEquals(painQuote("they repeat it manually", text), null);
  assertEquals(painQuote("", text), null);
  assertEquals(painQuote(undefined, text), null);
});

Deno.test("spamSignals: a spaced domain, site:, 'found it via X' at the end; a plain tool mention is clean", () => {
  const plug = "Một vài thứ mình áp dụng thực tế: PR description viết như changelog.\n\nKleon — found it via LabAgent, site: labagent .tech";
  const s = spamSignals(plug);
  assertEquals(s.length, 3);
  assertEquals(s[0], 'a site written with a space to dodge links ("labagent .tech")');
  assertEquals(spamSignals("I use Obsidian for this, and git bisect saved me twice. Node.js handles it fine."), []);
  assertEquals(spamSignals("We moved to example.com last year."), []);
});

Deno.test("a suspected plug goes to spam_check (no draft), even when the decider calls it engagement", async () => {
  const plug = "Great tips on PR descriptions and commits.\n\nKleon — found it via LabAgent, site: labagent .tech";
  const r = await triageItem({ project, context: ctx(plug) }, stub({ kind: { engagement: 0.97, feedback_for_founder: 0.03 }, action: { short_draft: 1 }, promotion: 0.2 }));
  assertEquals([r.kind, r.route, r.spam?.suspected], ["engagement", "spam_check", true]);
  // The model alone can flag it too.
  const quiet = await triageItem({ project, context: ctx("Nice write-up. Our team switched to a tool that does all of this for us, worth a look.") },
    stub({ kind: { engagement: 0.9, ignore: 0.1 }, action: { draft: 1 }, promotion: 0.8 }));
  assertEquals([quiet.route, quiet.spam?.signals], ["spam_check", ["the decider reads it as a plug for another product"]]);
  // A real comment stays a comment.
  const real = await triageItem({ project, context: ctx("Have you seen agents ignore tool descriptions?") },
    stub({ kind: { engagement: 0.9, product_question: 0.1 }, action: { draft: 1 }, promotion: 0.05 }));
  assertEquals([real.route, real.spam?.suspected], ["draft", false]);
});
