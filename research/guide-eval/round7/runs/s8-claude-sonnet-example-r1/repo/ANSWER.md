# Cache fix: memory writes no longer evict the static instructions

**Cause:** `build_system` (bot.py) joined `INSTRUCTIONS` and the per-athlete context
(date, profile, zones, goal, facts, language) into one text block with a single
`cache_control` marker. `save_fact` changes the facts, so the prefix hash changed and the
whole ~1000-token prompt was re-created. `logs/usage.jsonl` shows this: reads of 1046, then
the call after `save_fact` has `cache_read: 0` and `cache_creation: 1061`.

**Change:** `build_system` now returns two text blocks, each with `cache_control: ephemeral`:
1. `INSTRUCTIONS` alone. It has no interpolated values, so it is byte-stable.
2. `athlete_context(...)`, the volatile tail.

A memory write now re-creates only the tail. The instructions stay cached.

**From the colleague's note:**
- *Applied:* the two-marker split, and keeping the static block free of interpolated values.
  I checked `INSTRUCTIONS` and it has none.
- *Applied (nothing to change):* loading all facts every time rather than selecting top-N.
  The code already does this, and I kept it. I also left the keyword-based tool filtering
  alone, as NOTES.md says. Tools sit above the system prompt in the cache, so a message that
  adds a tool group still causes one full re-read. The log shows this on `plan_week`.
- *Not applicable:* the MCP and Telegram specifics, and the token counts. Those were that
  bot's numbers.

**Not verified:** I did not run the bot or call the API. To check, send two messages, then a
`save_fact`, then a third message. The third should show `cache_read` of roughly the
instructions' size and `cache_creation` of roughly the tail's size only.
