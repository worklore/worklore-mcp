# Fix: split system prompt into two cache blocks

## What changed

In `bot.py`, the `build_system` function now returns **two separate cache blocks** instead of one concatenated block:

```python
def build_system(a, today):
    # Two cache blocks: static instructions (byte-stable) and volatile athlete context.
    # A memory write (save_fact) only invalidates the second block, not the instructions.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

Previously, `INSTRUCTIONS + "\n\n" + athlete_context(a, today)` was a single text block with one `cache_control` marker. When `save_fact` appended to `a.facts`, the entire block's prefix hash changed, evicting the static instructions from cache. With two blocks, a memory write only invalidates the second (volatile) block; the first (static) block stays cached.

## What applied from the colleague's note

- **Two cache_control segments**: Applied directly. Split into static instructions + volatile context.
- **Prefix hash behavior**: Confirmed — Anthropic's cache uses prefix hashing, so any byte change invalidates from that point to the end of the block.
- **Static block must be byte-stable**: Applied. `INSTRUCTIONS` contains no interpolated values.
- **Volatile tail ordered rarest-changing first**: Already satisfied — `athlete_context` puts date first, then profile fields, then facts (which change most often).
- **Resist per-message personalization inside cached blocks**: Applied by keeping all facts in every message (no top-N selection).

## What did not apply

- **Tool filtering**: Already implemented in this codebase (`select_tools` by keyword), and tools sit *above* the system prompt in the request, so they don't affect the system-prompt cache.
- **Anthropic SDK specifics**: The fix is provider-agnostic; the marker syntax works for any provider with prefix-based caching.
- **Usage verification steps**: Not needed for this fix — the change is structural and the colleague's verification steps can be run post-deploy to confirm the cache behavior.
