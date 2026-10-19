// The ask-code agent: a Claude tool-use loop over one repo (repo_tools.ts)
// that answers one question from the code and cites the lines. It never
// writes anything. docs/ARCHITECTURE.md › Ask the code.
//
// Each step is one Messages API call; the conversation grows by the tool
// results, so the newest message carries the cache breakpoint and the next
// step reads everything before it from cache. Limits per run: steps, a
// deadline and a cost ceiling; past any of them the agent is told to answer
// with what it has. The answer comes through the `answer` tool (thinking is
// on, so the tool can't be forced: a plain-text reply is taken as the answer).

import { costUsd } from "../draft/providers/pricing.ts";
import { blobUrl, REPO_TOOLS, RepoTools, ToolDef } from "./repo_tools.ts";

export interface AskInput {
  question: string;
  repo: string;
  /** The reply she is writing, the comment it answers: what the question is for. */
  context?: string | null;
}

export interface Source { path: string; start_line?: number | null; end_line?: number | null; note?: string | null; url: string }

export interface AskAnswer {
  /** Short, plain: what she can say (a check's answer). */
  answer: string;
  /** Longer, for her: how it works, caveats. */
  details: string | null;
  sources: Source[];
  confidence: "high" | "medium" | "low";
}

export interface StepUsage {
  model: string; input: number; output: number; cache_read: number; cache_write: number;
  cost_usd: number | null; latency_ms: number; ok: boolean; error?: string;
}

export interface AskRun extends AskAnswer {
  model: string;
  steps: number;
  tool_calls: number;
  github_requests: number;
  usage: { input: number; output: number; cache_read: number; cache_write: number; cost_usd: number };
}

export interface AgentOptions {
  model: string;
  effort?: "low" | "medium" | "high";
  maxSteps?: number;
  deadlineMs?: number;
  maxUsd?: number;
  /** One Messages API call: body → response JSON (throws on HTTP errors). */
  send: (body: Record<string, unknown>) => Promise<Record<string, unknown>>;
  /** Every step's usage, as it happens (model_calls). */
  onStep?: (u: StepUsage) => Promise<void> | void;
  now?: () => number;
}

const ANSWER_TOOL: ToolDef = {
  name: "answer",
  description: "Give the final answer. Call it exactly once, when you know, or when you are told to stop.",
  input_schema: {
    type: "object",
    properties: {
      answer: { type: "string", description: "The fact she can put in her reply: 1–2 plain sentences, no file paths, no hedging beyond what is true. If the code doesn't say, say so." },
      details: { type: "string", description: "For her only: how it works and any caveat, a few sentences. May mention files." },
      sources: {
        type: "array",
        items: {
          type: "object",
          properties: { path: { type: "string" }, start_line: { type: "integer" }, end_line: { type: "integer" }, note: { type: "string" } },
          required: ["path"],
        },
      },
      confidence: { type: "string", enum: ["high", "medium", "low"] },
    },
    required: ["answer", "confidence"],
  },
};

export function systemPrompt(repo: string, sha: string): string {
  return [
    `You answer one question about the software in the GitHub repository ${repo} (commit ${sha.slice(0, 7)}), for its maintainer, who is replying to a user's comment and needs a fact she can rely on.`,
    "Work from the code only: search, list and read files with the tools, then call `answer`. Read the actual lines before you state anything; names and docs can be out of date, the code is what runs.",
    "Be economical: a few targeted searches and reads, not a tour of the repository. Stop as soon as the code answers the question.",
    "If the code doesn't settle it (it depends on configuration, a service, or it isn't built), say exactly that in `answer` and set confidence low. Never guess a version, number, date or behaviour.",
    "Cite the lines you relied on in `sources` (path and line range).",
  ].join("\n");
}

/** Pure: the user turn that opens the run. */
export function firstTurn(input: AskInput): string {
  return [
    input.context?.trim() ? `Context (the conversation she is replying in):\n${input.context.trim().slice(0, 6000)}\n` : null,
    `Question: ${input.question.trim()}`,
  ].filter(Boolean).join("\n");
}

type Block = Record<string, unknown> & { type: string };
type Message = { role: "user" | "assistant"; content: string | Block[] };

/** Pure: messages with one cache breakpoint, on the newest block. */
export function withCacheBreakpoint(messages: Message[]): Message[] {
  return messages.map((m, i) => {
    if (i !== messages.length - 1) return m;
    const blocks: Block[] = typeof m.content === "string" ? [{ type: "text", text: m.content }] : m.content;
    return { ...m, content: blocks.map((b, j) => (j === blocks.length - 1 ? { ...b, cache_control: { type: "ephemeral" } } : b)) };
  });
}

/** Pure: the answer tool's input (or a plain-text reply) → AskAnswer with links at [sha]. */
export function parseAnswer(raw: Record<string, unknown> | string, repo: string, sha: string): AskAnswer {
  if (typeof raw === "string") return { answer: raw.trim(), details: null, sources: [], confidence: "low" };
  const conf = raw.confidence === "high" || raw.confidence === "medium" ? raw.confidence : "low";
  const sources = (Array.isArray(raw.sources) ? raw.sources : [])
    .filter((s): s is Record<string, unknown> => !!s && typeof s === "object" && typeof (s as Record<string, unknown>).path === "string")
    .slice(0, 8)
    .map((s) => {
      const path = String(s.path).replace(/^\/+/, "");
      const a = Number(s.start_line) || null, b = Number(s.end_line) || null;
      return { path, start_line: a, end_line: b, note: typeof s.note === "string" ? s.note : null, url: blobUrl(repo, sha, path, a, b) };
    });
  return {
    answer: String(raw.answer ?? "").trim(),
    details: typeof raw.details === "string" && raw.details.trim() ? raw.details.trim() : null,
    sources,
    confidence: conf,
  };
}

export async function askCode(input: AskInput, tools: RepoTools, opts: AgentOptions): Promise<AskRun> {
  const now = opts.now ?? Date.now;
  const t0 = now();
  const maxSteps = opts.maxSteps ?? 12;
  const deadline = t0 + (opts.deadlineMs ?? 120_000);
  const maxUsd = opts.maxUsd ?? 1;
  const total = { input: 0, output: 0, cache_read: 0, cache_write: 0, cost_usd: 0 };
  const messages: Message[] = [{ role: "user", content: firstTurn(input) }];
  let toolCalls = 0;
  let toldToStop = false;

  for (let step = 1; step <= maxSteps + 1; step++) {
    const body = {
      model: opts.model,
      max_tokens: 16000,
      system: [{ type: "text", text: systemPrompt(tools.repo, tools.sha) }],
      tools: [...REPO_TOOLS, ANSWER_TOOL],
      messages: withCacheBreakpoint(messages),
      thinking: { type: "adaptive" },
      output_config: { effort: opts.effort ?? "medium" },
    };
    const s0 = now();
    let res: Record<string, unknown>;
    try {
      res = await opts.send(body);
    } catch (e) {
      await opts.onStep?.({ model: opts.model, input: 0, output: 0, cache_read: 0, cache_write: 0, cost_usd: null, latency_ms: now() - s0, ok: false, error: (e as Error).message });
      throw e;
    }
    const u = (res.usage ?? {}) as Record<string, number>;
    const usage = { input: u.input_tokens ?? 0, output: u.output_tokens ?? 0, cache_read: u.cache_read_input_tokens ?? 0, cache_write: u.cache_creation_input_tokens ?? 0 };
    const model = String(res.model ?? opts.model);
    const cost = costUsd(model, usage) ?? null;
    for (const k of ["input", "output", "cache_read", "cache_write"] as const) total[k] += usage[k];
    total.cost_usd += cost ?? 0;
    await opts.onStep?.({ model, ...usage, cost_usd: cost, latency_ms: now() - s0, ok: true });

    const content = (res.content ?? []) as Block[];
    const finish = (a: AskAnswer): AskRun => ({
      ...a, model, steps: step, tool_calls: toolCalls, github_requests: tools.requests,
      usage: { ...total, cost_usd: Math.round(total.cost_usd * 1e6) / 1e6 },
    });
    const answer = content.find((b) => b.type === "tool_use" && b.name === "answer");
    if (answer) return finish(parseAnswer(answer.input as Record<string, unknown>, tools.repo, tools.sha));
    const uses = content.filter((b) => b.type === "tool_use");
    if (!uses.length || res.stop_reason !== "tool_use") {
      const text = content.filter((b) => b.type === "text").map((b) => String(b.text)).join("").trim();
      if (res.stop_reason === "refusal") throw new Error("the model declined to answer");
      if (!text) throw new Error(`no answer (stop_reason=${res.stop_reason ?? "?"})`);
      return finish(parseAnswer(text, tools.repo, tools.sha));
    }

    messages.push({ role: "assistant", content });
    const results: Block[] = [];
    for (const b of uses) {
      toolCalls++;
      const out = await tools.run(String(b.name), (b.input ?? {}) as Record<string, unknown>);
      results.push({ type: "tool_result", tool_use_id: b.id, content: out.slice(0, 40_000) });
    }
    const overSteps = step >= maxSteps;
    const overTime = now() > deadline - 25_000;
    const overCost = total.cost_usd >= maxUsd;
    if ((overSteps || overTime || overCost) && !toldToStop) {
      toldToStop = true;
      results.push({ type: "text", text: "Stop searching now: call `answer` with what you found. If it isn't enough, say what is still unknown and set confidence low." });
    } else if (toldToStop) {
      throw new Error("the agent kept searching after it was told to answer");
    }
    messages.push({ role: "user", content: results });
  }
  throw new Error("no answer within the step limit");
}

/** The Messages API sender (one retry on 429/529); the key only in a header. */
export function anthropicSender(apiKey: string, fetchFn: typeof fetch = fetch, timeoutMs = 90_000) {
  return async (body: Record<string, unknown>): Promise<Record<string, unknown>> => {
    for (let attempt = 0; ; attempt++) {
      const res = await fetchFn("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "content-type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(timeoutMs),
      });
      if (res.ok) return await res.json();
      const text = (await res.text()).slice(0, 300).replace(/\s+/g, " ");
      if ((res.status === 429 || res.status === 529) && attempt === 0) {
        await new Promise((r) => setTimeout(r, 3000));
        continue;
      }
      throw new Error(`anthropic ${res.status}: ${text}`);
    }
  };
}
