import { assertEquals } from "jsr:@std/assert@1";
import { discoveryTriage } from "./triage_run.ts";

Deno.test("discovered posts get a triage from their relevance decision (never untriaged)", () => {
  const t = discoveryTriage({ why: "Her MCP tool-count research answers this", p_relevant: 0.82, action: "comment_to_engage", title: "Skills are not tools" });
  assertEquals([t.kind, t.route, t.summary, t.not_sure], ["engagement", "draft", "Her MCP tool-count research answers this", false]);
  assertEquals(discoveryTriage({ action: "flag_for_founder", p_relevant: 0.5 }).route, "decide_queue");
  assertEquals(discoveryTriage(null).route, "skip");
});
