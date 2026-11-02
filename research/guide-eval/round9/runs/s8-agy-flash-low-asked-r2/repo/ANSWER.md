# Fix for Prompt Caching Invalidation on Memory Writes

## Cause
Previously, `build_system(a, today)` concatenated the static coaching instructions (`INSTRUCTIONS`) and the volatile athlete context (`athlete_context(a, today)`, which contains the date, profile, zones, and dynamic memory facts) into a single text block with a single `cache_control: {"type": "ephemeral"}` marker:

```python
text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

Because Anthropic prompt caching operates via prefix hashing, whenever `save_fact` appended a new fact to `a.facts`, the contents of the single prompt block changed. This caused a cache miss across the entire prompt (including the static instructions), forcing the subsequent request to re-read and recreate the cache for the entire ~1000+ token prompt (`cache_read_input_tokens: 0`, `cache_creation_input_tokens: ~1000`).

## Solution
Split the `system` parameter into two separate content blocks, each marked with `cache_control: {"type": "ephemeral"}`:

1. **Static Instruction Block**: Contains `INSTRUCTIONS.strip()`, which is byte-stable across all athletes, requests, and dates (~780 tokens).
2. **Volatile Context Block**: Contains `athlete_context(a, today)`, which includes the athlete profile, current date, zones, and dynamic facts list.

```python
def build_system(a, today):
    # Two blocks: static instructions (byte-stable across athletes and dates)
    # and dynamic per-athlete context (profile, zones, facts).
    # Memory writes only invalidate the second block, keeping instructions cached.
    return [
        {"type": "text", "text": INSTRUCTIONS.strip(), "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

## Impact
- When an athlete triggers `save_fact`, only the second (volatile context) block's cache prefix is invalidated and recreated (~240 tokens).
- The first block (static coaching instructions) remains hot in cache, avoiding full re-caching charges on subsequent calls and tool rounds.
