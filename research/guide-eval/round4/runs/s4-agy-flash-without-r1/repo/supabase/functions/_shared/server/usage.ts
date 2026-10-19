// Every model call, logged (model_calls): which function and purpose, which
// project, the model, tokens and cost at list price (pricing.ts). Spend is
// read with SQL over model_calls / model_spend_daily (docs/API.md › Spend).
//
// The function, project and item travel in a per-request scope, so a call
// deep in the engine is tagged without passing ids around: serve() opens the
// scope with the function's name, a handler adds the project once it knows
// it (tagUsage). Work handed to background() keeps the scope it started in.
// Logging never fails the call it logs.

import { AsyncLocalStorage } from "node:async_hooks";
import { admin } from "./ctx.ts";

export interface UsageScope {
  fn?: string;
  project_id?: string | null;
  founder_id?: string | null;
  item_id?: string | null;
  /** Groups the calls of one multi-step run (an ask-code agent run). */
  run_id?: string | null;
}

const scope = new AsyncLocalStorage<UsageScope>();

/** Runs [f] with a fresh scope (serve() does this per request). */
export function withUsage<T>(s: UsageScope, f: () => T): T {
  return scope.run({ ...s }, f);
}

/** Adds what the handler learned (project, item) to the current scope. */
export function tagUsage(s: UsageScope) {
  const cur = scope.getStore();
  if (cur) Object.assign(cur, s);
}

export const currentUsage = (): UsageScope => ({ ...(scope.getStore() ?? {}) });

export interface ModelCall {
  purpose: string;
  provider: string;
  model: string;
  ok: boolean;
  error?: string | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
  usage?: Record<string, unknown> | null;
  cost_usd?: number | null;
  latency_ms?: number | null;
}

/** Pure: the model_calls row for a call in a scope. */
export function modelCallRow(c: ModelCall, s: UsageScope) {
  return {
    fn: s.fn ?? null,
    purpose: c.purpose,
    project_id: s.project_id ?? null,
    founder_id: s.founder_id ?? null,
    item_id: s.item_id ?? null,
    run_id: s.run_id ?? null,
    provider: c.provider,
    model: c.model,
    ok: c.ok,
    error: c.error ? c.error.slice(0, 300) : null,
    tokens_in: c.tokens_in ?? null,
    tokens_out: c.tokens_out ?? null,
    usage: c.usage ?? null,
    cost_usd: c.cost_usd ?? null,
    latency_ms: c.latency_ms ?? null,
  };
}

/** Test seam: where rows go. */
export let sinkModelCall = async (row: ReturnType<typeof modelCallRow>) => {
  const { error } = await admin().from("model_calls").insert(row);
  if (error) throw error;
};
export function setModelCallSink(f: typeof sinkModelCall) { sinkModelCall = f; }

/** Logs one call; a failed insert is a console line, never an error. */
export async function logModelCall(c: ModelCall, s: UsageScope = currentUsage()): Promise<void> {
  try {
    await sinkModelCall(modelCallRow(c, s));
  } catch (e) {
    console.error("model_calls insert failed:", (e as Error).message?.slice(0, 160));
  }
}
