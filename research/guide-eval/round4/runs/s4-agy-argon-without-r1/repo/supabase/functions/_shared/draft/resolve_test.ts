import { assert, assertEquals, assertRejects } from "jsr:@std/assert@1";
import { hasUnresolvedCheck, parseChecks } from "./checks.ts";
import type { GenerateRequest, GenerateResult, Provider } from "./providers/provider.ts";
import { checkEdit, editByRule, paragraphs, resolveChecks, ResolveError, wordDiff } from "./resolve.ts";

// The real Sonnet 5.5 draft of 2026-10-11 (reply to FrancisTR on dev.to): the
// gap is a paragraph of its own at the end.
const P1 = "I agree that the reasoning is what separates a portfolio from a screenshot gallery. And your last point is the one I'd push on: you work with people who each have their own designs and constraints, so the real skill is picking the right plan for each of them. A finished project doesn't show that. A decision record does: what the options were, which one won, what it cost.";
const P2 = "That's also why I think it matters more now. When an agent writes most of the code, \"I built it\" says very little, but \"I chose this over that, for this reason\" is still something only the person can say.";
const GAP = "[check: do you keep a decision log on your own projects, or do you reconstruct the reasoning afterwards? Add one real example of a choice you rejected and why.]";
const DRAFT = `${P1}\n\n${P2}\n\n${GAP}`;

/** A provider that answers from a script, and remembers what it was asked. */
function scripted(...answers: (string | Error)[]) {
  const seen: GenerateRequest[] = [];
  let i = 0;
  const p: Provider = {
    name: "mock", model: "mock-1",
    generate(req: GenerateRequest): Promise<GenerateResult> {
      seen.push(req);
      const a = answers[Math.min(i++, answers.length - 1)];
      if (a instanceof Error) return Promise.reject(a);
      return Promise.resolve({ text: a, model: "mock-1", tokens_in: 100, tokens_out: 20, usage: { input: 100, output: 20 }, latency_ms: 5 });
    },
  };
  return { p, seen };
}

const unchangedOutside = (before: string, after: string, gapPara: number) => {
  const a = paragraphs(before).map((p) => p.text), b = paragraphs(after).map((p) => p.text);
  a.forEach((t, i) => { if (i !== gapPara) assert(b.includes(t), `paragraph ${i} changed`); });
};

Deno.test("checks: id, question and exact span", () => {
  const t = "It took [check: how many days?] and saved [check: 30% — not in your sources].";
  const c = parseChecks(t);
  assertEquals(c.map((x) => x.id), ["c1", "c2"]);
  assertEquals(c[0].question, "how many days?");
  assertEquals(t.slice(c[0].start, c[0].end), "[check: how many days?]");
  assertEquals(t.slice(c[1].start, c[1].end), c[1].marker);
  assertEquals(parseChecks(DRAFT)[0].start, DRAFT.indexOf(GAP));
  assert(hasUnresolvedCheck("a [CHECK how many"));
  assert(!hasUnresolvedCheck("checked it"));
});

Deno.test("resolve: her answer goes in, in place; the rest is byte-identical", async () => {
  const answer = "yes, I keep a DECISIONS.md in each repo; I rejected Firebase for Hearback because I wanted row-level security in Postgres";
  const { p, seen } = scripted(
    "I do keep one: a DECISIONS.md in each repo. For Hearback I rejected Firebase because I wanted row-level security in Postgres.",
  );
  const r = await resolveChecks({ text: DRAFT, resolutions: [{ check_id: "c1", answer }], founder_name: "Valentina" }, p);
  assert(!/\[check/i.test(r.text));
  assert(r.text.startsWith(`${P1}\n\n${P2}\n\n`), "earlier paragraphs untouched");
  assert(r.text.includes("DECISIONS.md") && r.text.includes("Firebase"));
  assertEquals(r.resolved, [{ check_id: "c1", question: parseChecks(DRAFT)[0].question, action: "answer", answer, method: "model" }]);
  assertEquals(r.invented, []);
  // The model saw her answer and only the gap's paragraph to edit.
  assert(seen[0].prompt.includes(answer));
  assert(seen[0].prompt.includes(`## The paragraph to edit\n${GAP}`));
  // Diff budget over the whole text: only words of the gap and of her answer moved.
  const d = wordDiff(DRAFT, r.text);
  const allowed = new Set([...answer.toLowerCase().match(/[\p{L}\p{N}]+/gu)!, "i", "do", "one", "a", "for", "because", "keep"]);
  assertEquals(d.added.filter((w) => !allowed.has(w)), []);
  assertEquals(d.removed, []); // the gap's words don't count as text
});

Deno.test("resolve: her answer is proofread (grammar, repeats) with a minimal edit", async () => {
  // Her real answer of 2026-10-12: the model used to only add "the".
  const answer = "I think mainly I speak about the projects I made during interview process. It is the time when people really care about what I say and my point of view. They really have a reason to do this. No article could get so much attention, don\u2019t you think?";
  const fixed = "I mostly talk about the projects I made during the interview process. That's when people really care about what I say and my point of view, because they have a reason to. No article could get that much attention, don't you think?";
  const { p, seen } = scripted(fixed);
  const r = await resolveChecks({ text: DRAFT, resolutions: [{ check_id: "c1", answer }], founder_name: "Valentina" }, p);
  assertEquals(r.resolved[0].method, "model", r.resolved[0].reason);
  assert(r.text.endsWith(fixed));
  assert(seen[0].system.includes("Proofread her answer"));
});

Deno.test("resolve: an answer inside a sentence; the model rewrites too much → retry → rule fallback", async () => {
  const text = `${P1}\n\nIt took me [check: how many days did the rewrite take?] to rewrite the parser, and the tests caught two regressions.`;
  const wild = "Rewriting the parser was a long, painful journey that taught me patience and showed how fragile my whole testing setup had become over the years.";
  const { p, seen } = scripted(wild, wild);
  const r = await resolveChecks({ text, resolutions: [{ check_id: "c1", answer: "three days" }] }, p);
  assertEquals(seen.length, 2, "one retry");
  assertEquals(r.resolved[0].method, "fallback");
  assert(r.resolved[0].reason, "says why the model's edit was not used");
  assertEquals(r.text, `${P1}\n\nIt took me three days to rewrite the parser, and the tests caught two regressions.`);
});

Deno.test("resolve: drop a gap that is a whole paragraph → the paragraph goes, nothing else changes", async () => {
  const { p } = scripted("<EMPTY>");
  const r = await resolveChecks({ text: DRAFT, resolutions: [{ check_id: "c1", drop: true }] }, p);
  assertEquals(r.text, `${P1}\n\n${P2}`);
  assertEquals(r.resolved[0].action, "drop");
  assertEquals(r.resolved[0].method, "model");
});

Deno.test("resolve: drop removes the dependent sentence (model), smoothing allowed, no new claims", async () => {
  const text = `${P1} It cut my review time by [check: 3 hours — not in your sources], which surprised me.\n\n${P2}`;
  const { p } = scripted(P1);
  const r = await resolveChecks({ text, resolutions: [{ check_id: "c1", drop: true }] }, p);
  assertEquals(r.text, `${P1}\n\n${P2}`);
  unchangedOutside(text, r.text, 0);
});

Deno.test("resolve: a drop that adds claims is refused; the rule removes the gap's sentence", async () => {
  const text = `${P1} It cut my review time by [check: 3 hours — not in your sources], which surprised me.\n\n${P2}`;
  const sneaky = `${P1} Reviews are now twice as fast thanks to Copilot and a new checklist.`;
  const { p } = scripted(sneaky, sneaky);
  const r = await resolveChecks({ text, resolutions: [{ check_id: "c1", drop: true }] }, p);
  assertEquals(r.resolved[0].method, "fallback");
  assertEquals(r.text, `${P1}\n\n${P2}`);
});

Deno.test("resolve: other gaps stay verbatim; a model that touches them is refused", async () => {
  const text = "I tried [check: which tool did you try?] and it took [check: how long?].";
  const { p } = scripted("I tried Cursor and it took a while.", "I tried Cursor and it took [check: how long?].");
  const r = await resolveChecks({ text, resolutions: [{ check_id: "c1", answer: "Cursor" }] }, p);
  assertEquals(r.text, "I tried Cursor and it took [check: how long?].");
  assertEquals(parseChecks(r.text).map((c) => c.id), ["c1"]); // ids are per text: the remaining gap is c1 now
});

Deno.test("resolve: no provider (or it fails) → the rule; several checks at once", async () => {
  const text = `Intro.\n\nI tried [check: which tool?] last week. [check: Add an example of a bug it caught.]\n\nBye [check: sign-off?] now.`;
  const r = await resolveChecks({
    text,
    resolutions: [{ check_id: "c1", answer: "Cursor" }, { check_id: "c2", answer: "it caught an off-by-one in the pager" }, { check_id: "c3", drop: true }],
  }, scripted(new Error("boom")).p);
  assertEquals(r.text, "Intro.\n\nI tried Cursor last week. It caught an off-by-one in the pager.");
  assertEquals(r.resolved.map((x) => `${x.check_id}:${x.action}:${x.method}`), ["c1:answer:fallback", "c2:answer:fallback", "c3:drop:fallback"]);
  assertEquals((await resolveChecks({ text: "A [check: x?] b.", resolutions: [{ check_id: "c1", answer: "y" }] }, null)).text, "A y b.");
});

Deno.test("resolve: the fact guard still runs on the edited paragraph", async () => {
  const { p } = scripted("I keep a DECISIONS.md in every repo, for 4 years now.");
  const r = await resolveChecks({ text: DRAFT, resolutions: [{ check_id: "c1", answer: "I keep a DECISIONS.md in every repo" }], fact_context: "" }, p);
  assertEquals(r.invented, ["4 years"]);
  assert(r.text.endsWith("I keep a DECISIONS.md in every repo, for [check: 4 years — not in your sources] now."));
});

Deno.test("resolve: unknown check, missing answer", async () => {
  await assertRejects(() => resolveChecks({ text: DRAFT, resolutions: [{ check_id: "c9", answer: "x" }] }, null), ResolveError);
  const e = await assertRejects(() => resolveChecks({ text: DRAFT, resolutions: [{ check_id: "c1", answer: "  " }] }, null), ResolveError);
  assertEquals((e as ResolveError).code, "answer_required");
});

Deno.test("checkEdit and editByRule details", () => {
  const span = parseChecks(GAP)[0];
  assertEquals(checkEdit(GAP, "", [{ span, r: { check_id: "c1", answer: "yes" } }], []).ok, false);
  assertEquals(checkEdit(GAP, "", [{ span, r: { check_id: "c1", drop: true } }], []).ok, true);
  assertEquals(editByRule(GAP, 0, [{ span, r: { check_id: "c1", answer: "yes, a DECISIONS.md" } }]), "Yes, a DECISIONS.md.");
  assertEquals(editByRule(`A b. ${GAP} C d.`, 0, [{ span: { ...span, start: 5, end: 5 + GAP.length }, r: { check_id: "c1", drop: true } }]), "A b. C d.");
});
