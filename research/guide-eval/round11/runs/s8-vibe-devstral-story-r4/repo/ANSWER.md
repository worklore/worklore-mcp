# Fix: Two cache_control segments for prompt caching

## What changed

In `bot.py`, the `build_system` function was modified to split the system prompt into two separate cache blocks instead of one:

**Before:**
```python
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

**After:**
```python
def build_system(a, today):
    # Two cache blocks: static instructions (byte-stable) + volatile per-athlete context.
    # This way a memory write (save_fact) only invalidates the tail, not the static prefix.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

## Why this fixes the issue

The Anthropic prompt cache uses a prefix hash mechanism: changing one byte invalidates everything from that byte to the end of the cached block. With a single cache block containing both static instructions and volatile athlete context (including facts), every `save_fact` call rewrites the facts block, changes the prefix hash, and evicts the entire prompt from cache — including the static instructions that never change.

By splitting into two blocks:
- **Block 1:** Static `INSTRUCTIONS` (byte-identical across users and days)
- **Block 2:** Volatile per-user context (date, profile, zones, goal, facts, language)

A memory write now invalidates only Block 2 (~240 tokens). Block 1 stays cached, so subsequent messages within the 5-minute TTL read the static instructions at ~10% price instead of re-paying full price.

## What from the colleague's note applied

The following parts of the colleague's note were directly applicable and implemented:

1. **Two cache_control segments instead of one** — The core fix: split static instructions from volatile data.
2. **Static instructions as byte-stable Block 1** — `INSTRUCTIONS` contains no interpolated values, dates, or counters.
3. **Volatile per-user tail as Block 2** — `athlete_context` contains date, profile, zones, goal, facts, and language, ordered rarest-changing first.
4. **Memory write only invalidates the tail** — `save_fact` modifies facts in Block 2, leaving Block 1 cached.

The following parts were noted but not directly relevant to this fix:
- Tool filtering by message keywords — Already implemented in the codebase (`select_tools`), but separate from the caching fix.
- Top-N fact selection per message — Rejected in the note, and we also keep all facts in the context.
- Aggressive tool filtering tension — Noted as a consideration, but tools sit above the system prompt and are handled separately.

## Expected behavior after fix

- First message: `cache_creation_input_tokens` ≈ full prompt size (both blocks created)
- Second message within 5 min: `cache_read_input_tokens` ≈ full prompt size (both blocks hit)
- After `save_fact`: Next message has `cache_read_input_tokens` ≈ size of Block 1 only, `cache_creation_input_tokens` ≈ size of Block 2 only
