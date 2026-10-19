// Model wiring for the server:
//   modelForUser()     which model writes a founder's drafts: her override
//                      (founders.draft_model) if her plan allows it, else the
//                      plan's default, else DRAFT_MODEL ("anthropic:claude-sonnet-5-5",
//                      "gemini:gemini-3.1-flash-lite"). projects.settings.draft_model
//                      is no longer read.
//   draftProvider()    that model as a Provider; Claude falls back to Gemini on any error
//   utilityProvider()  short JSON/summary calls (discover "why", landing read,
//                      triage summary, decider fallback): Gemini, UTILITY_MODEL
//   decider()          TypeSafe Jev with a Gemini fallback
//   embedder()         gemini-embedding-001
// Every text call goes through a per-day cap (usage_counters) so a cron loop
// can't burn a key: GEMINI_DAILY_CAP (the free key is shared with Valentina's
// other projects) and ANTHROPIC_DAILY_CAP (paid). Every call made is logged
// in model_calls with its purpose, tokens and cost (usage.ts).

import {
  AnthropicProvider, Decider, DecideOptions, Decision, Effort, FallbackProvider, GeminiEmbedder, GeminiProvider, GenerateRequest, GenerateResult,
  LlmDecider, parseModelSpec, PRICES, Provider, ProviderError, Questions, TypeSafeDecider,
} from "../draft/mod.ts";
import { admin, env } from "./ctx.ts";
import { logModelCall } from "./usage.ts";

const DEFAULT_CAP = 150;

/** The daily cap for [key]: false when it is reached. */
export async function withinBudget(key: string, cap: number): Promise<boolean> {
  const { data, error } = await admin().rpc("bump_usage", { p_key: key, p_cap: cap });
  if (error) throw error;
  return data === true;
}

/** A provider behind a daily cap; every call it makes is logged under [purpose]. */
export class BudgetedProvider implements Provider {
  readonly name: string;
  readonly model: string;
  constructor(private inner: Provider, private key: string, private cap: number, private purpose = "utility") {
    this.name = inner.name;
    this.model = inner.model;
  }
  async generate(req: GenerateRequest): Promise<GenerateResult> {
    if (!await withinBudget(this.key, this.cap)) throw new ProviderError(`daily budget for ${this.key} reached (${this.cap})`, 429);
    const t0 = Date.now();
    try {
      const r = await this.inner.generate(req);
      await logModelCall({
        purpose: this.purpose, provider: r.provider ?? this.name, model: r.model, ok: true,
        tokens_in: r.tokens_in, tokens_out: r.tokens_out, usage: r.usage as Record<string, unknown> | undefined,
        cost_usd: r.usage?.cost_usd ?? null, latency_ms: r.latency_ms,
      });
      return r;
    } catch (e) {
      await logModelCall({ purpose: this.purpose, provider: this.name, model: this.model, ok: false, error: (e as Error).message, latency_ms: Date.now() - t0 });
      throw e;
    }
  }
}

const DEFAULT_ANTHROPIC_CAP = 300;
const DEFAULT_DRAFT_MODEL = "gemini:gemini-3.1-flash-lite";

/**
 * Gemini for short utility calls (JSON "why" lines, landing reads, summaries,
 * the decider fallback). [purpose] names the calls in model_calls.
 */
export function utilityProvider(model?: string, purpose = "utility"): Provider {
  const m = model ?? env("UTILITY_MODEL") ?? "gemini-3.1-flash-lite";
  const g = new GeminiProvider({ apiKey: env("GEMINI_API_KEY") ?? "", model: m, maxRetries: 2 });
  return new BudgetedProvider(g, `gemini:${m}`, Number(env("GEMINI_DAILY_CAP") ?? DEFAULT_CAP), purpose);
}

/** Why a draft got its model (stored on the drafts row: tokens.model_choice). */
export type ModelReason = "override" | "plan default" | "env";

export interface ModelChoice {
  spec: string;            // "anthropic:claude-sonnet-5-5", "gemini:gemini-3.1-flash-lite"
  reason: ModelReason;
  founder_id: string | null;
  plan_id: string | null;
}

export interface FounderModelRow { id?: string | null; plan_id?: string | null; draft_model?: string | null }
export interface PlanRow { id: string; default_model: string; allowed_models: string[] }

/** A spec the server can run: a priced Claude model (no surprise bills) or a Gemini model. */
export function isRunnableSpec(spec: string | null | undefined): boolean {
  if (!spec?.trim()) return false;
  const c = parseModelSpec(spec.trim());
  return (c.provider === "anthropic" && !!c.model && c.model in PRICES) || (c.provider === "gemini" && /^gemini-[\w.-]+$/.test(c.model ?? ""));
}

/**
 * The resolution order, pure: the founder's override if her plan allows it,
 * else the plan's default, else DRAFT_MODEL (env), else Gemini flash-lite.
 */
export function resolveDraftModel(founder: FounderModelRow | null, plan: PlanRow | null, envModel?: string | null): ModelChoice {
  const who = { founder_id: founder?.id ?? null, plan_id: plan?.id ?? founder?.plan_id ?? null };
  const own = founder?.draft_model?.trim();
  if (own && plan?.allowed_models.includes(own) && isRunnableSpec(own)) return { spec: own, reason: "override", ...who };
  if (own) console.error(`founders.draft_model '${own.slice(0, 60)}' is not allowed by plan ${who.plan_id}; using the plan default`);
  if (plan?.default_model && isRunnableSpec(plan.default_model)) return { spec: plan.default_model, reason: "plan default", ...who };
  return { spec: envModel?.trim() || DEFAULT_DRAFT_MODEL, reason: "env", ...who };
}

/**
 * Whose model setting a draft uses: whoever asked for it in the app; for an
 * automatic draft (triage, no caller) the item's assigned founder, else the
 * project owner.
 */
export function modelFounderFor(o: { requestedBy?: string | null; assignedTo?: string | null; owner?: string | null }): string | null {
  return o.requestedBy ?? o.assignedTo ?? o.owner ?? null;
}

/**
 * The one place a founder's draft model is decided (docs/ARCHITECTURE.md ›
 * Models and plans).
 */
export async function modelForUser(founderId: string | null): Promise<ModelChoice> {
  let founder: FounderModelRow | null = null;
  let plan: PlanRow | null = null;
  if (founderId) {
    const { data, error } = await admin().from("founders")
      .select("id, plan_id, draft_model, plans(id, default_model, plan_models!plan_models_plan_fkey(model, ord))")
      .eq("id", founderId).maybeSingle();
    if (error) console.error("modelForUser: founder lookup failed:", error.message.slice(0, 200));
    if (data) {
      founder = { id: data.id, plan_id: data.plan_id, draft_model: data.draft_model };
      const p = (Array.isArray(data.plans) ? data.plans[0] : data.plans) as
        { id: string; default_model: string; plan_models: { model: string; ord: number }[] | null } | null;
      plan = p
        ? { id: p.id, default_model: p.default_model, allowed_models: [...(p.plan_models ?? [])].sort((a, b) => a.ord - b.ord).map((m) => m.model) }
        : null;
    }
  }
  // TODO(Russia): when there is a country signal for the founder (or the
  // item's audience), force a Gemini model here for Russia-based users;
  // Anthropic doesn't serve Russia. No country logic yet.
  return resolveDraftModel(founder, plan, env("DRAFT_MODEL"));
}

/**
 * The draft writer for a spec (from modelForUser). Claude falls back to
 * Gemini on any error. [purpose]: draft / resolve / points (model_calls).
 */
export function draftProvider(spec: string, effortSetting?: unknown, purpose = "draft"): Provider {
  const cfg = parseModelSpec(spec);
  if (cfg.provider === "anthropic" && env("ANTHROPIC_API_KEY")) {
    const effort = (typeof effortSetting === "string" ? effortSetting : env("DRAFT_EFFORT") ?? "medium") as Effort;
    const claude = new AnthropicProvider({ apiKey: env("ANTHROPIC_API_KEY")!, model: cfg.model, effort, timeoutMs: 75_000, maxRetries: 1 });
    const budgeted = new BudgetedProvider(claude, `anthropic:${claude.model}`, Number(env("ANTHROPIC_DAILY_CAP") ?? DEFAULT_ANTHROPIC_CAP), purpose);
    return new FallbackProvider(budgeted, utilityProvider(undefined, purpose));
  }
  if (cfg.provider === "anthropic") console.error("the draft model is a Claude model but ANTHROPIC_API_KEY is not set; drafting with Gemini");
  return utilityProvider(cfg.provider === "gemini" && cfg.model ? cfg.model : undefined, purpose);
}

/** TypeSafe Jev first; on any failure (or no key) the Gemini decider answers the same questions. */
export class FallbackDecider implements Decider {
  readonly name: string;
  readonly model: string;
  constructor(private primary: Decider | null, private fallback: Decider) {
    this.name = primary?.name ?? fallback.name;
    this.model = primary?.model ?? fallback.model;
  }
  async decide(state: string | Record<string, unknown>, questions: Questions, opts?: DecideOptions): Promise<Decision> {
    if (this.primary) {
      const t0 = Date.now();
      try {
        const d = await this.primary.decide(state, questions, opts);
        await logModelCall({
          purpose: "decide", provider: this.primary.name, model: this.primary.model, ok: true,
          tokens_in: d.usage.tokens_in, tokens_out: d.usage.tokens_out, latency_ms: Date.now() - t0,
        });
        return d;
      } catch (e) {
        await logModelCall({ purpose: "decide", provider: this.primary.name, model: this.primary.model, ok: false, error: (e as Error).message, latency_ms: Date.now() - t0 });
        console.error(`decider ${this.primary.name} failed, falling back: ${(e as Error).message.slice(0, 200)}`);
      }
    }
    return this.fallback.decide(state, questions, opts);
  }
}

export function decider(): Decider {
  const key = env("TYPESAFE_API_KEY");
  const primary = key ? new TypeSafeDecider({ apiKey: key, model: env("TYPESAFE_MODEL") ?? "jev-latest", maxRetries: 2 }) : null;
  return new FallbackDecider(primary, new LlmDecider(utilityProvider(undefined, "decide")));
}

export function embedder(): GeminiEmbedder {
  return new GeminiEmbedder({ apiKey: env("GEMINI_API_KEY") ?? "", model: "gemini-embedding-001", dims: 768 });
}

/** pgvector text form "[0.1,0.2,…]" ⇄ number[] */
export const toVector = (v: number[]) => `[${v.map((x) => Math.round(x * 1e6) / 1e6).join(",")}]`;
export function fromVector(v: unknown): number[] {
  if (Array.isArray(v)) return v as number[];
  if (typeof v === "string") return JSON.parse(v);
  return [];
}
