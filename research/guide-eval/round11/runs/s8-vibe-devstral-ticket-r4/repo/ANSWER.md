# Fix: Split system prompt into static and volatile blocks

## What changed

In `bot.py`, `build_system()` now returns two separate text blocks instead of one concatenated block:

```python
def build_system(a, today):
    # Split into two blocks so that memory writes (facts) only invalidate the
    # per-user tail, while the static instructions stay cached.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

Previously, `INSTRUCTIONS + "\n\n" + athlete_context(a, today)` was a single block. Any change to the athlete context (e.g., a `save_fact` call adding a new fact) changed the entire string, which under prefix-based caching evicts the whole cached prompt. With the split, only the second block (the per-user tail) is invalidated when facts change, while the first block (static instructions) remains cached.

## Which parts of the colleague's note applied

- **Applied**: The core diagnosis — prefix hashing means changing one byte evicts everything from that byte to the end of the cached block. This is exactly what happened with `save_fact` rewriting the facts block.
- **Applied**: The solution of splitting into two text blocks with `cache_control: {"type": "ephemeral"}`, where the first holds static instructions and the second holds per-user volatile content.
- **Applied**: The insight that byte stability matters — `INSTRUCTIONS` is byte-identical across users and days (no interpolated dates, names, or counters), making it a perfect candidate for a separate cacheable block.
- **Applied**: The understanding that memory writes should only invalidate the tail, not the static prefix.
- **Applied**: The marker syntax using `cache_control` with ephemeral type (Anthropic-specific, as noted).

- **Not applied**: Tool filtering by keyword groups — this was already implemented in the codebase (`select_tools()`) and the colleague noted it as a separate improvement from March. The fix here is purely about the system prompt structure.
- **Not applied**: The specific token counts (780 vs 240 tokens) — these were examples from the colleague's setup, not requirements for this fix.
- **Not applied**: The decision to load all facts every time rather than filtering per-message — this code already loads all facts, and that choice is orthogonal to the caching fix.
- **Not applied**: The 5-minute TTL detail — this is provider-specific behavior, not something we control in the code.
- **Not applied**: The usage log fields (`cache_creation_input_tokens`, `cache_read_input_tokens`) — these are observed in `logs/usage.jsonl` but don't require code changes; the fix will naturally improve these metrics.
