# Cache fix

**Cause:** `build_system` (bot.py) put instructions + athlete context (incl. facts) in one block with one `cache_control` marker. `save_fact` changes the facts, so the prefix hash changed and the whole ~1100-token prompt was re-created (see `logs/usage.jsonl`: `cache_read 0`, `cache_creation ~1100` after a save).

**Change:** `build_system` now returns two text blocks, each with `cache_control: ephemeral`: (1) `INSTRUCTIONS`, byte-stable; (2) `athlete_context(...)` (date, profile, zones, goal, facts, language). A memory write now only invalidates block 2. Tool filtering is untouched. Only 2 of the 4 allowed markers are used.

**Caveat (please verify):** a cached prefix must meet the model's minimum cacheable length (1024 tokens for Sonnet 4.5). The static prefix is tools (~110 tokens) + instructions (~2.5k chars, roughly 600-750 tokens), so it is probably *below* 1024 and the first marker may silently not cache. I couldn't call the API here to check. After deploying, send two messages, then a `save_fact`, then a third, and look at `logs/usage.jsonl`: `cache_read_input_tokens` should stay at roughly the static size after the write. If it drops to 0, the static part is too short. Then the fix is to lengthen the static prefix with real content (for example more coaching rules or examples), not padding.

Nothing was deployed or sent anywhere.
