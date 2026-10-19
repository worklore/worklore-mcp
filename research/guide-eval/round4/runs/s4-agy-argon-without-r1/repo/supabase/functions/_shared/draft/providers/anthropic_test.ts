import { assert, assertEquals, assertRejects } from "jsr:@std/assert@1";
import { AnthropicProvider } from "./anthropic.ts";
import { FallbackProvider, parseModelSpec } from "./index.ts";
import { costUsd } from "./pricing.ts";
import type { GenerateRequest, GenerateResult, Provider } from "./provider.ts";
import { ProviderError, userTurn } from "./provider.ts";

const OK = {
  model: "claude-sonnet-5-5", stop_reason: "end_turn",
  content: [{ type: "thinking", thinking: "" }, { type: "text", text: "Hello there." }],
  usage: { input_tokens: 900, output_tokens: 120, cache_read_input_tokens: 1500, cache_creation_input_tokens: 0 },
};

function fakeFetch(responses: { status: number; body: unknown; headers?: Record<string, string> }[], seen: RequestInit[] = []): typeof fetch {
  let i = 0;
  return ((_url: string, init: RequestInit) => {
    seen.push(init);
    const r = responses[Math.min(i++, responses.length - 1)];
    return Promise.resolve(new Response(typeof r.body === "string" ? r.body : JSON.stringify(r.body), { status: r.status, headers: r.headers }));
  }) as unknown as typeof fetch;
}
const REQ: GenerateRequest = { system: "RULES", context: "## Who you are\nP", prompt: "## Task\nT", temperature: 0.7, max_output_tokens: 2048 };

Deno.test("anthropic: request shape (cached profile block, key in header, no sampling params)", async () => {
  const seen: RequestInit[] = [];
  const p = new AnthropicProvider({ apiKey: "k-test", model: "claude-sonnet-5-5", fetch: fakeFetch([{ status: 200, body: OK }], seen) });
  const r = await p.generate(REQ);
  const body = JSON.parse(seen[0].body as string);
  const h = seen[0].headers as Record<string, string>;
  assertEquals(h["x-api-key"], "k-test");
  assertEquals(h["anthropic-version"], "2023-06-01");
  assertEquals(body.system, [{ type: "text", text: "RULES" }, { type: "text", text: "## Who you are\nP", cache_control: { type: "ephemeral" } }]);
  assertEquals(body.messages, [{ role: "user", content: "## Task\nT" }]);
  assertEquals(body.thinking, { type: "adaptive" });
  assertEquals(body.output_config, { effort: "medium" });
  assertEquals(body.temperature, undefined);
  assert(body.max_tokens >= 8000, "thinking needs room");
  assertEquals(r.text, "Hello there.");
  assertEquals(r.tokens_in, 2400);
  assertEquals(r.tokens_out, 120);
  assertEquals(r.usage?.cache_read, 1500);
  assertEquals(r.usage?.cost_usd, costUsd("claude-sonnet-5-5", { input: 900, output: 120, cache_read: 1500, cache_write: 0 }));
});

Deno.test("anthropic: one retry on 529, then success", async () => {
  const seen: RequestInit[] = [];
  const p = new AnthropicProvider({
    apiKey: "k", fetch: fakeFetch([{ status: 529, body: "overloaded", headers: { "retry-after": "1" } }, { status: 200, body: OK }], seen),
    sleep: () => Promise.resolve(),
  });
  assertEquals((await p.generate(REQ)).text, "Hello there.");
  assertEquals(seen.length, 2);
});

Deno.test("anthropic: 429 twice gives up after one retry; 400 is not retried", async () => {
  const seen: RequestInit[] = [];
  const p = new AnthropicProvider({ apiKey: "k", fetch: fakeFetch([{ status: 429, body: "slow down" }], seen), sleep: () => Promise.resolve() });
  const e = await assertRejects(() => p.generate(REQ), ProviderError);
  assertEquals((e as ProviderError).status, 429);
  assertEquals(seen.length, 2);
  const seen2: RequestInit[] = [];
  const q = new AnthropicProvider({ apiKey: "k", fetch: fakeFetch([{ status: 400, body: "bad" }], seen2), sleep: () => Promise.resolve() });
  await assertRejects(() => q.generate(REQ), ProviderError);
  assertEquals(seen2.length, 1);
});

Deno.test("anthropic: refusal and truncation are errors (the caller falls back)", async () => {
  const p = new AnthropicProvider({ apiKey: "k", fetch: fakeFetch([{ status: 200, body: { ...OK, stop_reason: "refusal", content: [] } }]) });
  await assertRejects(() => p.generate(REQ), ProviderError, "refused");
  const q = new AnthropicProvider({ apiKey: "k", fetch: fakeFetch([{ status: 200, body: { ...OK, stop_reason: "max_tokens" } }]) });
  await assertRejects(() => q.generate(REQ), ProviderError, "truncated");
});

Deno.test("fallback provider: primary error → fallback answers and is recorded", async () => {
  const bad: Provider = { name: "anthropic", model: "claude-sonnet-5-5", generate: () => Promise.reject(new ProviderError("boom", 500)) };
  const good: Provider = {
    name: "gemini", model: "gemini-3.1-flash-lite",
    generate: (r) => Promise.resolve({ text: userTurn(r), model: "gemini-3.1-flash-lite", tokens_in: 1, tokens_out: 1, latency_ms: 1 } as GenerateResult),
  };
  const f = new FallbackProvider(bad, good, () => {});
  const r = await f.generate(REQ);
  assertEquals(r.provider, "gemini");
  assertEquals(r.text, "## Who you are\nP\n## Task\nT"); // the same text, as one user turn
});

Deno.test("parseModelSpec", () => {
  assertEquals(parseModelSpec("anthropic:claude-sonnet-5-5"), { provider: "anthropic", model: "claude-sonnet-5-5" });
  assertEquals(parseModelSpec("gemini-3.1-flash-lite"), { provider: "gemini", model: "gemini-3.1-flash-lite" });
  assertEquals(parseModelSpec("claude-opus-5-5"), { provider: "anthropic", model: "claude-opus-5-5" });
});
