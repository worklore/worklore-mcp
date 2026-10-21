# Answer: save_fact evicts the cached system prompt

## Cause

`build_system()` in `bot.py` put the static coaching rules (`INSTRUCTIONS`) and the
per-athlete context into one text block with a single `cache_control` marker.
The per-athlete context includes `long-term facts`, which `save_fact` appends to.
Any change to that block changes the cache key for the whole prefix, so the next
call after a memory write could not read from cache and paid to write about 1,100
tokens again. `logs/usage.jsonl` shows this: `cache_read_input_tokens: 0` with
`cache_creation_input_tokens` near 1,100 on the call after each `save_fact`.

The per-athlete context also contains today's date, so the cache was also evicted
once a day even without any memory write.

## Change

`bot.py`, `build_system()`:

- Block 1: `INSTRUCTIONS`, with `cache_control: ephemeral`. This is the only
  block with a cache breakpoint.
- Block 2: `athlete_context()` (name, zones, goal, facts, language, today's date),
  with no cache marker. It sits after the breakpoint, so changes to it no longer
  touch the cached prefix.

Nothing else changed. The keyword-based tool selection, the tool-loop, the
athlete storage and the usage logging are untouched.

## Verification

Run offline with a fake LLM and the file writes patched out (nothing written to
`data/` or `logs/`):

- `build_system()` returns an identical block 1 before and after a fact is appended.
- Block 2 contains the new fact.
- Across a `save_fact` round followed by a normal message, the system block 1 sent
  to the API is the same string in both calls.

I did not call the Anthropic API, so I have not measured the cache hit rate.

## Open risks

1. **Minimum cacheable length.** Anthropic only caches a prefix above a minimum
   size (about 1,024 tokens for Sonnet-class models, which is what `MODEL` is set
   to). My estimate of block 1 plus the core tool definitions is roughly
   750 to 1,000 tokens, which is close to that threshold. If it is below, the
   breakpoint is silently ignored and the instructions are not cached at all,
   which would be a regression on ordinary messages. Check after deploy: the first
   call on a new chat should show `cache_creation_input_tokens` near the static
   size, and follow-up calls should show a matching `cache_read_input_tokens`.
   If they do not, the fix is a larger static prefix, not moving the breakpoint.
2. **Tool groups still change the prefix.** Tools come before the system prompt in
   the cache order, so a message that matches a tool group (for example "race")
   changes the tool list and misses the cache for that call. This is the existing
   keyword-filter trade-off that `NOTES.md` says to keep, so I left it. If the
   bill still looks high after this change, this is the next thing to measure.
