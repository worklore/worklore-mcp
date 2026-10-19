import { assert, assertEquals } from "jsr:@std/assert@1";
import { guardFacts } from "./guard.ts";

// The two real auto-drafts of 2026-10-09 (item: Fayaz's "😂" under "What was your win this week?").
const THREAD = `What was your win this week?\nyahhi: I would like to do the same with my 50. How did you dare? 😜\nFayaz: 😂`;

Deno.test("guard: '78% of failed agent tasks…' becomes a check", () => {
  const draft = "My win was documenting the 50th agent story in Worklore, which revealed that 78% of failed agent tasks stem from ambiguous prompt instructions. How are you tracking your own agent failures?";
  const g = guardFacts(draft, THREAD);
  assertEquals(g.invented, ["78%"]);
  assert(g.text.includes("[check: 78% — not in your sources] of failed agent tasks"));
  assert(!/(?<!check: )78%/.test(g.text.replace("[check: 78% — not in your sources]", "")));
  assert(g.text.includes("50th")); // "my 50" is in the thread
});

Deno.test("guard: 'reduced my failure rate by 40%' and 'first 12 workflows' become checks", () => {
  const draft = "I built Worklore to solve that exact hesitation. When I documented the first 12 agent workflows, I found that peer review reduced my failure rate by 40%. What holds you?";
  const g = guardFacts(draft, THREAD);
  assertEquals(g.invented, ["12", "40%"]);
  assert(g.text.includes("reduced my failure rate by [check: 40% — not in your sources]."));
  assert(g.text.includes("the first [check: 12 — not in your sources] agent workflows"));
});

Deno.test("guard: numbers from the sources or thread stay; small counts, years, versions stay", () => {
  const ctx = "Survey: what 91 sources advise about MCP tool count. Agents got 1,200 calls right.";
  const draft = "The survey read 91 sources and 1,200 calls; two things stood out in 2026, and v0.6.0 ships 3 steps.";
  const g = guardFacts(draft, ctx);
  assertEquals(g.invented, []);
  assertEquals(g.text, draft);
});

Deno.test("guard: small numbers with a unit are measurements; cited studies need a source", () => {
  const g = guardFacts("It cut review time by 3 hours. According to a Stanford study, agents fail often.", "nothing here");
  assertEquals(g.invented, ["According to a Stanford study, agents fail often", "3 hours"]);
  assert(g.text.includes("[check: According to a Stanford study, agents fail often — source?]"));
  assert(g.text.includes("[check: 3 hours — not in your sources]"));
});

Deno.test("guard: existing gaps are left alone", () => {
  const draft = "It took [check: how many days?] and saved 30%.";
  assertEquals(guardFacts(draft, "saved 30%").text, draft);
});

Deno.test("guard: a cited study with a number becomes one gap, not nested ones", () => {
  const g = guardFacts("A study by MIT found 30% fewer bugs. Nice.", "");
  assertEquals(g.text, "[check: A study by MIT found 30% fewer bugs — source?]. Nice.");
});
