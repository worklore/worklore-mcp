# Fix: split system prompt to preserve static instruction cache

## What changed

In `bot.py`, the function `build_system(a, today)` was changed from returning a single text block (instructions + athlete context concatenated) to returning an array of two separate text blocks:

1. **Static block**: `INSTRUCTIONS` — byte-identical across all users and days, with no interpolation
2. **Volatile block**: `athlete_context(a, today)` — per-athlete data that changes with facts, dates, etc.

Each block has its own `cache_control: {"type": "ephemeral"}` marker, so a `save_fact` call that modifies the athlete's facts only invalidates the second (tail) block, while the first (static instructions) block remains cached.

## Why this works

The underlying issue was prefix hashing: with a single cache marker at the end of one concatenated block, changing any byte (e.g., adding a fact) changed the prefix hash from that byte to the end, evicting the entire cached prompt including the static instructions.

By splitting into two blocks, each with its own cache marker, the static instructions block maintains a stable hash and stays cached across all users and sessions, while only the per-athlete tail (~240 tokens) is re-cached when facts change.

## Colleague's note: what applied

The following parts of the colleague's note **applied directly** and were used in this fix:

- **Root cause**: "With a single cache marker at the end of the system prompt, every `save_fact` call rewrote the facts block and evicted the whole cached prompt, including instructions that never changed."
- **Cause**: "The cause was prefix hashing: changing one byte made everything from that byte to the end of the cached block a miss."
- **Solution**: "I fixed it by splitting `system` into an array of two text blocks, each with `cache_control: {"type": "ephemeral"}`. The first held the static instructions... The second held the per-user tail... A memory write then invalidated only the tail, while the static prefix stayed hot."
- **Byte stability**: "Byte stability also mattered... reordering or rewording schemas changed the prefix."

The following parts were **not applicable** to this codebase:

- Tool filtering into groups by message keywords — this codebase already has `select_tools(text)` which filters tools, and tools sit above the system prompt in the request, not inside it
- The specific mention of Anthropic's 4 markers per request limit — we only need 2 markers (one per block)
- The specific usage field names (`cache_creation_input_tokens`, `cache_read_input_tokens`) — these are already logged in this codebase and will show the improvement
- Top-N fact selection per message — we kept "loading all facts every time" as the colleague recommended
