This patch fixes the caching behavior so that a `save_fact` memory write no longer evicts the static instructions from the cached system prompt.

**What was changed**
1. **`build_system` function** in `bot.py` was rewritten.
   - Previously the system prompt was built as a single text block, meaning any change to the volatile tail (facts, date, etc.) altered the prefix hash and caused the whole prompt—including static instructions—to be re‑cached on every `save_fact`.
   - The new implementation splits the prompt into **two separate blocks**:
     ```python
     static_block = {"type": "text", "text": INSTRUCTIONS,
                     "cache_control": {"type": "ephemeral"}}
     volatile_block = {"type": "text", "text": athlete_context(a, today)}
     return [static_block, volatile_block]
     ```
   - The static block retains the cache marker, so only the volatile block is rebuilt when facts change.
2. Added a detailed docstring to `build_system` explaining the two‑block split and caching semantics.

**Which parts of the colleague’s note applied**
- Identified that changing one byte in the tail invalidated the prefix hash; we solved this by **splitting the system prompt into two cached blocks**.
- Recommended using `cache_control: {"type": "ephemeral"}` on the static prefix; we kept that marker on the static instructions block.
- Suggested ordering the volatile tail after the static block; our implementation follows that order.

**Result**
- `save_fact` now only updates the second block, leaving the cached static instructions hot.
- Subsequent tool‑use loops read the cached static prefix, reducing token usage and avoiding the full‑prompt cache‑creation cost on each memory write.

Further tuning (e.g., additional cache markers for other rarely‑changing sections) can follow the same pattern.

