// Ask the code, offline: the repo tools over a fake GitHub, the agent loop
// over a scripted model, the answer parsing, and the model-call log rows.
//   deno test supabase/functions/_shared/

import { assert, assertEquals, assertStringIncludes } from "jsr:@std/assert@1";
import { askCode, firstTurn, parseAnswer, StepUsage, withCacheBreakpoint } from "./agent.ts";
import { blobUrl, decodeContent, grepLines, numberedLines, RepoTools } from "./repo_tools.ts";
import { conversationContext } from "../server/ask_code.ts";
import { functionName } from "../server/http.ts";
import { modelCallRow } from "../server/usage.ts";

const REPO = "worklore/patchwork";
const SHA = "abc1234def5678";
const b64 = (s: string) => btoa(String.fromCharCode(...new TextEncoder().encode(s)));

const FILES: Record<string, string> = {
  "README.md": "# Patchwork\nExports notes.\n",
  "src/export.ts": "export const FORMATS = ['md', 'pdf'];\n// csv is planned\nexport function exportNotes() {}\n",
  "node_modules/x/index.js": "csv everywhere",
};

function fakeGithub() {
  const calls: string[] = [];
  const get = <T>(path: string): Promise<T> => {
    calls.push(path);
    if (path.includes("/git/trees/")) {
      return Promise.resolve({ tree: Object.keys(FILES).map((p) => ({ path: p, type: "blob", size: FILES[p].length })) } as T);
    }
    const m = path.match(/\/contents\/(.+)\?ref=/);
    if (m) {
      const p = decodeURIComponent(m[1]);
      if (!(p in FILES)) return Promise.reject(new Error("GitHub 404"));
      return Promise.resolve({ type: "file", encoding: "base64", content: b64(FILES[p]), size: FILES[p].length } as T);
    }
    if (path.startsWith("/search/code")) return Promise.resolve({ total_count: 1, items: [{ path: "src/export.ts" }] } as T);
    if (path.includes("/commits?")) return Promise.resolve([{ sha: SHA, commit: { message: "Add pdf export\n\nbody", author: { date: "2026-10-01T10:00:00Z" } } }] as T);
    return Promise.reject(new Error(`unexpected ${path}`));
  };
  return { get, calls };
}

Deno.test("repo tools: numbered lines, grep skips vendored dirs, list, decode, links", async () => {
  assertEquals(numberedLines("a\nb\nc", 2).text, "2\tb\n3\tc");
  assertEquals(numberedLines("a\nb\nc", 1, 1).shown, [1, 1]);
  assertEquals(grepLines("x\ncsv here\ny", /csv/i), ["2: csv here"]);
  assertEquals(decodeContent(b64("héllo")), "héllo");
  assertEquals(blobUrl(REPO, SHA, "src/a b.ts", 3, 9), `https://github.com/${REPO}/blob/${SHA}/src/a%20b.ts#L3-L9`);
  assertEquals(blobUrl(REPO, SHA, "src/a.ts", 3, 3), `https://github.com/${REPO}/blob/${SHA}/src/a.ts#L3`);

  const gh = fakeGithub();
  const t = new RepoTools(REPO, SHA, gh.get);
  const grep = await t.run("grep", { pattern: "csv" });
  assertStringIncludes(grep, "src/export.ts\n  2: // csv is planned");
  assert(!grep.includes("node_modules"));
  assertStringIncludes(await t.run("list_files", { path_prefix: "src/" }), "src/export.ts");
  assertStringIncludes(await t.run("read_file", { path: "src/export.ts", start_line: 1, end_line: 1 }), "1\texport const FORMATS");
  assertStringIncludes(await t.run("recent_commits", {}), "abc1234 2026-10-01 Add pdf export");
  assertStringIncludes(await t.run("read_file", { path: "nope.ts" }), "Error: GitHub 404");
  assertStringIncludes(await t.run("grep", { pattern: "(" }), "Not a valid regex");
  // The tree is read once; a file read twice is fetched once.
  assertEquals(gh.calls.filter((c) => c.includes("/git/trees/")).length, 1);
  assertEquals(gh.calls.filter((c) => c.includes("contents/src/export.ts")).length, 1);
});

Deno.test("answer parsing: links at the commit, confidence, plain text", () => {
  const a = parseAnswer({
    answer: " Markdown and PDF. ", confidence: "high",
    sources: [{ path: "/src/export.ts", start_line: 1, end_line: 2, note: "formats" }, { nope: 1 }],
  }, REPO, SHA);
  assertEquals(a.answer, "Markdown and PDF.");
  assertEquals(a.sources.length, 1);
  assertEquals(a.sources[0].url, `https://github.com/${REPO}/blob/${SHA}/src/export.ts#L1-L2`);
  assertEquals(parseAnswer({ answer: "x", confidence: "sure" }, REPO, SHA).confidence, "low");
  assertEquals(parseAnswer("It isn't built.", REPO, SHA), { answer: "It isn't built.", details: null, sources: [], confidence: "low" });
});

Deno.test("cache breakpoint sits on the newest block only", () => {
  const m = withCacheBreakpoint([
    { role: "user", content: "q" },
    { role: "assistant", content: [{ type: "tool_use", id: "t1", name: "grep", input: {} }] },
    { role: "user", content: [{ type: "tool_result", tool_use_id: "t1", content: "a" }, { type: "text", text: "stop" }] },
  ]);
  assertEquals(m[0].content, "q");
  const last = m[2].content as Record<string, unknown>[];
  assertEquals(last[0].cache_control, undefined);
  assertEquals(last[1].cache_control, { type: "ephemeral" });
});

const usage = { input_tokens: 1000, output_tokens: 200, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 };

Deno.test("agent: searches, reads, answers; every step is reported", async () => {
  const gh = fakeGithub();
  const bodies: Record<string, unknown>[] = [];
  const script = [
    { stop_reason: "tool_use", content: [{ type: "thinking", thinking: "…", signature: "s" }, { type: "tool_use", id: "t1", name: "search_code", input: { query: "export" } }] },
    { stop_reason: "tool_use", content: [{ type: "tool_use", id: "t2", name: "read_file", input: { path: "src/export.ts" } }] },
    { stop_reason: "tool_use", content: [{ type: "tool_use", id: "t3", name: "answer", input: { answer: "Markdown and PDF; CSV isn't built yet.", confidence: "high", sources: [{ path: "src/export.ts", start_line: 1, end_line: 2 }] } }] },
  ];
  const steps: StepUsage[] = [];
  const run = await askCode({ question: "Which export formats are there?", repo: REPO, context: "Can I export to CSV?" }, new RepoTools(REPO, SHA, gh.get), {
    model: "claude-opus-5-5",
    send: (b) => { bodies.push(structuredClone(b)); return Promise.resolve({ ...script[bodies.length - 1], usage, model: "claude-opus-5-5" }); },
    onStep: (s) => { steps.push(s); },
  });
  assertEquals(run.answer, "Markdown and PDF; CSV isn't built yet.");
  assertEquals(run.steps, 3);
  assertEquals(run.tool_calls, 2);
  assertEquals(steps.length, 3);
  // Opus 5.5 at $4/$20 per million: 1000 in + 200 out = $0.008 a step.
  assertEquals(run.usage.cost_usd, 0.024);
  // The thinking block goes back unchanged with the tool result.
  const third = bodies[2].messages as { role: string; content: Record<string, unknown>[] }[];
  assertEquals(third[1].content[0].type, "thinking");
  assertEquals(third[4].content[0].type, "tool_result");
  assertStringIncludes(String(third[4].content[0].content), "1\texport const FORMATS");
  assertStringIncludes(firstTurn({ question: "Q?", repo: REPO, context: "ctx" }), "Context");
});

Deno.test("agent: past the step limit it is told to answer, and a second refusal fails", async () => {
  const gh = fakeGithub();
  let n = 0;
  const seen: string[] = [];
  const run = await askCode({ question: "q?", repo: REPO }, new RepoTools(REPO, SHA, gh.get), {
    model: "claude-opus-5-5", maxSteps: 2,
    send: (b) => {
      n++;
      const msgs = b.messages as { content: unknown }[];
      seen.push(JSON.stringify(msgs[msgs.length - 1].content));
      if (n <= 2) return Promise.resolve({ stop_reason: "tool_use", usage, content: [{ type: "tool_use", id: `t${n}`, name: "list_files", input: {} }] });
      return Promise.resolve({ stop_reason: "end_turn", usage, content: [{ type: "text", text: "Couldn't tell from the code." }] });
    },
  });
  assertStringIncludes(seen[2], "Stop searching now");
  assertEquals(run.confidence, "low");
  assertEquals(run.answer, "Couldn't tell from the code.");

  let m = 0;
  let failed = false;
  try {
    await askCode({ question: "q?", repo: REPO }, new RepoTools(REPO, SHA, gh.get), {
      model: "claude-opus-5-5", maxSteps: 1,
      send: () => Promise.resolve({ stop_reason: "tool_use", usage, content: [{ type: "tool_use", id: `x${++m}`, name: "list_files", input: {} }] }),
    });
  } catch (e) {
    failed = /kept searching/.test((e as Error).message);
  }
  assert(failed);
});

Deno.test("agent: a cost ceiling stops the search", async () => {
  const gh = fakeGithub();
  let n = 0;
  const big = { input_tokens: 200_000, output_tokens: 0 }; // $0.80 a step
  const run = await askCode({ question: "q?", repo: REPO }, new RepoTools(REPO, SHA, gh.get), {
    model: "claude-opus-5-5", maxUsd: 1,
    send: () => {
      n++;
      if (n < 3) return Promise.resolve({ stop_reason: "tool_use", usage: big, content: [{ type: "tool_use", id: `t${n}`, name: "list_files", input: {} }] });
      return Promise.resolve({ stop_reason: "tool_use", usage: big, content: [{ type: "tool_use", id: "a", name: "answer", input: { answer: "Partly.", confidence: "medium" } }] });
    },
  });
  assertEquals(run.steps, 3);
  assertEquals(run.answer, "Partly.");
});

Deno.test("usage: model_calls rows carry the scope; function names from URLs", () => {
  const row = modelCallRow(
    { purpose: "ask_code", provider: "anthropic", model: "claude-opus-5-5", ok: false, error: "x".repeat(400), tokens_in: 5 },
    { fn: "ask-code", project_id: "p", run_id: "r" },
  );
  assertEquals(row.fn, "ask-code");
  assertEquals(row.run_id, "r");
  assertEquals(row.item_id, null);
  assertEquals(row.error!.length, 300);
  assertEquals(functionName("https://x.supabase.co/functions/v1/ask-code"), "ask-code");
  assertEquals(functionName("http://localhost:9000/draft"), "draft");
});

Deno.test("ask-code context: the comment, the thread's end and her draft", () => {
  const c = conversationContext({ text: "Can I export CSV?", thread: [{ author: "ana", text: "hi" }], my_post: { title: "Patchwork 1.4" } }, "Yes, [check: does CSV export exist?]");
  assertStringIncludes(c, "Her post: Patchwork 1.4");
  assertStringIncludes(c, "ana: hi");
  assertStringIncludes(c, "The comment she is answering: Can I export CSV?");
  assertStringIncludes(c, "Her draft reply:");
  assertEquals(conversationContext(null, null), "");
});
