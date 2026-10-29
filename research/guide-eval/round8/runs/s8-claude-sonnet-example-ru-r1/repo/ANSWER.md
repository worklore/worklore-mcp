# Fix: save_fact evicted the whole cached system prompt

**Cause.** `build_system` (bot.py) joined `INSTRUCTIONS` and the athlete context (date, profile, zones, goal, facts, language) into one text block with a single `cache_control`. Caching is prefix-based, so a `save_fact` changed the facts and invalidated the entire block, including the unchanged instructions. That matches `logs/usage.jsonl`: after a `save_fact`, `cache_read_input_tokens` is 0 and `cache_creation_input_tokens` is about 1100 again.

**Change.** `build_system` now returns two text blocks, each with `cache_control: ephemeral`:
1. `INSTRUCTIONS` alone. It has no interpolated values, so it is byte-stable across users and days.
2. `athlete_context(...)`, the volatile tail.

A memory write now invalidates only the tail. The instructions are still read from cache.

**Which parts of the colleague's note I used**
- Used: the two-marker split, and the byte-stability check on the static block (I confirmed `INSTRUCTIONS` is a plain constant).
- Used: keep all facts in the tail and don't select top-N facts per message. The code already injects all of them, so nothing changed there.
- Used: the tools array sits above `system` in the cache prefix, so I left `select_tools` and the tool schemas untouched. NOTES.md says to leave the keyword filter as it is.
- Skipped: the keyword tool filtering itself, since it already exists.
- Skipped: the numbers (780 and 240 tokens, 55 tools) are from their bot, not this one.

**Verification.** I did not run this against the API, because there are no credentials and I was told not to call external services. To check it, send two messages, then trigger a `save_fact`, then send a third. The third call should show `cache_read_input_tokens` covering the instructions and `cache_creation_input_tokens` covering only the tail. The tools array is also part of the prefix, so a message that pulls in an extra tool group will still re-cache once.
