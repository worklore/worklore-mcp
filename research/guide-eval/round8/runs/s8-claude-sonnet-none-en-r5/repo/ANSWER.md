# Caching fix

**Cause:** `build_system` concatenated the static `INSTRUCTIONS` and the per-athlete
context (facts, date) into one block with a single `cache_control` breakpoint. Any
change to the facts (`save_fact`) changed that block, so the whole prompt, including
the ~1000 tokens of instructions, was re-created instead of read from cache.

**Change (`bot.py`, `build_system`):** the system prompt is now two blocks:
1. `INSTRUCTIONS` (static) with its own `cache_control` breakpoint.
2. `athlete_context(...)` (facts, zones, date) with its own breakpoint.

After a `save_fact`, block 1 is still read from cache and only the small context block
is re-created. Tools filtering is untouched.

**Caveat:** tools come before the system prompt in the cache prefix, so a message that
adds a tool group (plan/race keywords) still changes the prefix and misses the cache.
That's separate from the save_fact problem. Not verified against the live API; the
change is untested beyond the code edit.
