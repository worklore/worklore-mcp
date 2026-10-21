# Cache fix: memory writes no longer evict the static instructions

**Cause:** `build_system` (bot.py) emitted one text block, `INSTRUCTIONS + athlete_context`, with a single
`cache_control` marker. `save_fact` changes the facts list, which changes the block, so the prefix hash
changed and the whole ~1000-token prompt was re-created (see `logs/usage.jsonl`: `cache_read 0`,
`cache_creation ~1060` right after each `save_fact`).

**Change:** `build_system` now returns two blocks, each with `cache_control: ephemeral`:
1. `INSTRUCTIONS`: static and byte-identical across users and days (no interpolated values).
2. `athlete_context(...)`: date, profile, zones, goal, facts, language. This is the volatile tail.

A memory write now invalidates only the tail, which is roughly 240 tokens. Two markers are used, and the limit is 4.

**Deliberately not done:** per-message top-N fact selection, because it makes the tail differ on every
message and it would never hit the cache. Tool filtering is unchanged. Tools sit above the system prompt in the
prefix, so a message that adds a tool group re-creates the cache once. The default set covers most
messages, and the tool list is constant within a single tool loop.

**Verify:** I have not run this against the API. Send two messages within 5 minutes. The second should show
`cache_read_input_tokens` covering the whole prompt. Then trigger `save_fact` and send a third message.
`cache_read` should still cover the instructions, and `cache_creation` should be only about the size of the tail.
Caveat: the model has a minimum cacheable prefix, which is 1024 tokens on some models. The tools plus the
~780-token instructions count toward it. If `cache_read` stays 0 for the static segment, the prefix is below
that minimum.
