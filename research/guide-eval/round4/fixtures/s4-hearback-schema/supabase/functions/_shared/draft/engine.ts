// draftReply: assemble context → prompt → provider → clean + lint.
// Pure with respect to storage: the caller loads the DraftRequest (load.ts) and
// stores the DraftResult as a drafts row.

import { assemble, AssembleOptions } from "./context.ts";
import { guardFacts } from "./guard.ts";
import { cleanDraft, lint } from "./lint.ts";
import { PROMPT_VERSION, PromptVersion, systemPrompt, userPrompt, userPromptParts } from "./prompt.ts";
import type { Provider } from "./providers/provider.ts";
import type { DraftRequest, DraftResult } from "./types.ts";

export interface DraftOptions extends AssembleOptions {
  temperature?: number;
  promptVersion?: PromptVersion;
  /** Includes thinking tokens on models that think (gemini-3.5-flash). */
  maxOutputTokens?: number;
}

export async function draftReply(req: DraftRequest, provider: Provider, opts: DraftOptions = {}): Promise<DraftResult> {
  const variant = req.variant ?? "first";
  if (variant !== "first" && !req.previous_draft) throw new Error(`variant '${variant}' needs previous_draft`);
  const a = assemble(req, opts);
  const version = opts.promptVersion ?? PROMPT_VERSION;
  const system = systemPrompt(req.project.founder_name ?? "the founder", req.project.founder_handle, version);
  // The profile part is the same for every draft of a project: providers with
  // prompt caching cache it with the rules; the rest see one user turn.
  const parts = userPromptParts(req, a, variant, version);
  const prompt = `${parts.stable}\n${parts.item}`;
  // Redraft no longer runs hot: a high temperature found "new angles" by inventing them.
  const temperature = opts.temperature ?? (variant === "shorter" ? 0.4 : 0.7);
  const out = await provider.generate({ system, context: parts.stable, prompt: parts.item, temperature, max_output_tokens: opts.maxOutputTokens ?? 2048 });
  // Numbers, statistics and cited studies the model can't know become [check: …] gaps.
  const guarded = guardFacts(cleanDraft(out.text, req.project.founder_name), factContext(req));
  const text = guarded.text;
  const report = lint(text, req.context.item.text, a.targetWords, prompt);
  return {
    text,
    provider: out.provider ?? provider.name,
    model: out.model,
    usage: { tokens_in: out.tokens_in, tokens_out: out.tokens_out, ...(out.usage ? { detail: out.usage } : {}) },
    latency_ms: out.latency_ms,
    instruction: variant === "first" ? (req.note ?? null) : [variant, req.note].filter(Boolean).join(": "),
    lint: { ...report, invented_facts: guarded.invented },
    context_report: { ...a.report, prompt_version: version },
  };
}

/** What a draft may take facts from: her retrieved published work, project notes, the thread, her own note. Not her past replies elsewhere. */
export function factContext(req: DraftRequest): string {
  const p = req.project, c = req.context;
  return [
    p.name, p.one_liner, p.audience, p.aims, p.views, ...(p.links ?? []).map((l) => `${l.title} ${l.url}`),
    c.post?.title, c.post?.text, ...c.chain.map((m) => m.text), c.item.text,
    ...(req.knowledge ?? []).map((k) => `${k.title}\n${k.text}`),
    ...req.memory_pool.map((m) => m.text),
    req.note,
  ].filter(Boolean).join("\n\n");
}

/** For debugging/eval: the exact prompt without calling a model. */
export function renderPrompt(req: DraftRequest, opts: DraftOptions = {}) {
  const a = assemble(req, opts);
  return {
    system: systemPrompt(req.project.founder_name ?? "the founder", req.project.founder_handle, opts.promptVersion),
    prompt: userPrompt(req, a, req.variant ?? "first", opts.promptVersion),
    assembled: a,
  };
}
