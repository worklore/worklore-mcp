// Decider adapter over any text Provider (Gemini by default): one JSON call
// that returns probabilities per option. LLM-stated probabilities are not
// calibrated; we report them as given and take confidence = the top option's
// probability. Swap in a calibrated decider (TypeSafe "Jev") when available.

import type { Provider } from "../providers/provider.ts";
import { DecideOptions, Decider, Decision, Questions, toAnswer } from "./decider.ts";

export class LlmDecider implements Decider {
  readonly name: string;
  readonly model: string;
  constructor(private llm: Provider) {
    this.name = llm.name;
    this.model = llm.model;
  }

  async decide(state: string | Record<string, unknown>, questions: Questions, opts: DecideOptions = {}): Promise<Decision> {
    const st = typeof state === "string" ? state : JSON.stringify(state, null, 1);
    const qs = Object.entries(questions).map(([id, q]) => {
      if (q.type === "choice") {
        return `"${id}" (choice): ${q.instructions}\n${Object.entries(q.criteria).map(([o, c]) => `  - "${o}": ${c}`).join("\n")}\n  → answer as {"${Object.keys(q.criteria).join('": p, "')}": p}, probabilities summing to 1`;
      }
      if (q.type === "boolean") return `"${id}" (yes/no): ${q.instructions}\n  Yes: ${q.criteria.true}\n  No: ${q.criteria.false}\n  → answer as the probability (0–1) of yes`;
      return `"${id}" (score): ${q.instructions}\n${q.criteria.map((c, i) => `  ${i}: ${c}`).join("\n")}\n  → answer as {"0": p, "1": p, …}, probabilities of each level summing to 1`;
    }).join("\n\n");
    const notes = opts.notes && Object.keys(opts.notes).length
      ? `\n\nAlso write these short notes:\n${Object.entries(opts.notes).map(([id, ins]) => `- "${id}": ${ins}`).join("\n")}`
      : "";
    const shape = `{"answers": {${Object.keys(questions).map((id) => `"${id}": …`).join(", ")}}${notes ? `, "notes": {${Object.keys(opts.notes!).map((id) => `"${id}": "…"`).join(", ")}}` : ""}}`;
    const prompt = `STATE\n${st}\n\nQUESTIONS\n${qs}${notes}\n\nGive honest probabilities: spread them when the case is unclear, put ~0.9+ on one option only when it is clear.\nReturn only JSON: ${shape}`;
    const out = await this.llm.generate({
      system: "You answer typed decision questions about a state with calibrated probabilities. Return only JSON.",
      prompt, temperature: 0, json: true, max_output_tokens: 600,
    });
    const t = out.text.trim().replace(/^```(?:json)?\s*|\s*```$/g, "");
    // deno-lint-ignore no-explicit-any
    let j: any;
    try { j = JSON.parse(t); } catch { j = JSON.parse(t.slice(t.indexOf("{"), t.lastIndexOf("}") + 1)); }
    const answers = Object.fromEntries(Object.entries(questions).map(([id, q]) => [id, toAnswer(q, j.answers?.[id])]));
    const n = j.notes && typeof j.notes === "object" ? Object.fromEntries(Object.entries(j.notes).map(([k, v]) => [k, String(v).slice(0, 300)])) : undefined;
    return {
      answers, notes: n, decider: this.name, model: out.model,
      usage: { tokens_in: out.tokens_in, tokens_out: out.tokens_out }, latency_ms: out.latency_ms,
    };
  }
}
