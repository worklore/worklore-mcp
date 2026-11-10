Fixed the caching issue by splitting the system prompt into two separate text blocks, each with its own `cache_control: {"type": "ephemeral"}`.

**What changed in bot.py:**
- `build_system` now returns a list of two text blocks instead of one concatenated block:
  1. Static INSTRUCTIONS (byte-identical across users and days, no interpolated values)
  2. Per-athlete context from `athlete_context` (date, profile, zones, goal, facts, language)

This ensures that when `save_fact` modifies the athlete's facts, only the second block (the volatile tail) is invalidated in the cache, while the first block (static instructions) remains cached and reused at ~10% cost.

**Which parts of the colleague's note applied:**
- The root cause: prefix hashing causing a single byte change to evict the entire cached prompt
- The solution: splitting system into an array of two text blocks with separate cache markers
- The ordering principle: static content first, volatile content second
- The cache behavior: memory writes now invalidate only the tail (~240 tokens) instead of the whole prompt (~1000+ tokens)
- The usage tracking: `cache_creation_input_tokens` vs `cache_read_input_tokens` will show the improvement

**Which parts did NOT apply:**
- Tool filtering into groups by message keywords (already implemented in the codebase but not part of this fix)
- The specific token counts (780 vs 240) and tool list placement (Anthropic-specific details)
- The 5-minute TTL mention (provider-specific)
- The rejection of top-N fact selection (we kept all facts, as in the original code)
