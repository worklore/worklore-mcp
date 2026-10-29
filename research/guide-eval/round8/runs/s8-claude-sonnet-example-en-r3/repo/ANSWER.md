# Fix: a memory write no longer evicts the static instructions

## Cause
`build_system` (bot.py) returned one text block (instructions + date + profile + facts) with one
`cache_control` marker. Caching is a prefix hash, so `save_fact` changed the facts, changed the
hash, and the whole ~1000-token block was re-created on the next call (`cache_read_input_tokens: 0`
in logs/usage.jsonl right after each `save_fact`). The date line also sat in that block, so every
new day evicted it too.

## Change (bot.py only)
`build_system` now returns three blocks, each with an ephemeral marker, ordered by volatility:
1. `INSTRUCTIONS`: byte-identical for everyone, always.
2. `athlete_profile`: name, sport, zones, goal, language. It changes rarely.
3. `athlete_volatile`: today's date and the long-term facts. It changes daily and on every `save_fact`.

A `save_fact` or a new day now invalidates only block 3. I checked offline that adding a fact
changes only block 3's text. I did not call the API, so no real cache numbers.
Tool filtering, tools and the loop are untouched. Tools sit above the system prompt in the prefix,
so they stay as they were.

## Caveat: the 1024-token minimum
From the logs, instructions + core tools are roughly 900-950 tokens (my estimate from char counts,
not measured). The model is Sonnet 4.5, whose minimum cacheable prefix is 1024 tokens, and a
breakpoint under that is silently not cached. So block 1 alone may not be cached for messages that
only get the core tools. When plan/race tools are added it should be. The profile breakpoint
(prefix about 1000-1050) may or may not clear the minimum. If the 1024 minimum is not met, a
memory write could still evict as before. I did not pad the instructions with filler, because that
would change bot behaviour and cost tokens on every call.

## Verify
Send two messages within 5 minutes, then one that triggers `save_fact`, then another. Read
`logs/usage.jsonl`: after the write, `cache_read_input_tokens` should still cover the instructions
(and profile), and `cache_creation_input_tokens` should be only the facts/date tail (~100-250 tokens).
If `cache_read` is 0 after a write, the prefix is under the minimum. Then either add real, useful
static content, or switch to a model with a lower minimum.

## Colleague's note: what applied
- Applied: split the system prompt into segments with a marker each, so the volatile part is last.
  I used three segments instead of two, because the profile changes far less often than facts and date.
- Applied: keep instructions byte-stable (no interpolation), and keep tools stable.
- Applied: keep injecting all facts, with no per-message selection. The code already did this.
- Applied: read `usage` to verify, via the existing log.
- Did not apply: their token counts (~780 / ~240). Our numbers differ, hence the minimum-length caveat above.
- Not needed: the tool-filtering advice (already in place, left alone) and the MCP/Telegram specifics.
