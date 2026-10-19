// List prices in USD per million tokens, for drafts.tokens.cost_usd and the
// eval's spend log. Source: https://platform.claude.com/docs/en/about-claude/pricing
// (read 2026-10-09). Cache writes are the 5-minute TTL price. Haiku 5.5 is
// priced higher for prompts over 100k tokens; drafts are ~6k, so the table
// keeps only the short-prompt row. Gemini on the free key costs nothing.

export interface Price { input: number; output: number; cache_write: number; cache_read: number }

export const PRICES: Record<string, Price> = {
  "claude-haiku-5-5": { input: 0.10, output: 0.50, cache_write: 0.125, cache_read: 0.01 },
  "claude-sonnet-5-5": { input: 2, output: 10, cache_write: 2.50, cache_read: 0.10 },
  "claude-opus-5-5": { input: 4, output: 20, cache_write: 5, cache_read: 0.20 },
};

export function costUsd(model: string, u: { input: number; output: number; cache_read?: number; cache_write?: number }): number | undefined {
  const p = PRICES[model] ?? PRICES[Object.keys(PRICES).find((k) => model.startsWith(k)) ?? ""];
  if (!p) return undefined;
  const usd = (u.input * p.input + u.output * p.output + (u.cache_write ?? 0) * p.cache_write + (u.cache_read ?? 0) * p.cache_read) / 1e6;
  return Math.round(usd * 1e6) / 1e6;
}
