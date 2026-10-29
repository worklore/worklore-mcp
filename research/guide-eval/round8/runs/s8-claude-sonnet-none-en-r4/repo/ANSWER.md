# Cache fix for save_fact

**Cause:** `build_system` put the instructions and the athlete context (today's date plus the facts list) in one text block with one `cache_control` breakpoint. `save_fact` changes the facts, so the block text changed and the whole cached prefix was invalidated, including the ~600+ tokens of static instructions.

**Change (bot.py, `build_system`):** the system prompt is now two blocks. The static `INSTRUCTIONS` block has its own breakpoint. The athlete context block comes after it and has a second breakpoint. A fact write now only changes the second block, so the instructions prefix can still be read from cache.

**Caveats (not verified, I can't call the API from here):**
- The minimum cacheable prefix on Sonnet 4.5 is 1024 tokens. Tools plus instructions are probably around 900 tokens (my estimate from the log and character counts). If so, the static block alone is too small to cache and this change won't show up in the logs. To get the full benefit, the static prefix needs to pass 1024 tokens. Check `cache_read_input_tokens` after a `save_fact` to confirm.
- The prefix order is tools, then system, then messages. `select_tools` changes the tools list per message (for example when a message adds `plan_week`), which invalidates everything after it. The log shows this too: `plan_week` rounds have `cache_read_input_tokens: 0`. I left the keyword filtering alone, as NOTES.md says. A fix would be to send a fixed tool list, or to measure whether the tool-token savings outweigh the cache misses.
